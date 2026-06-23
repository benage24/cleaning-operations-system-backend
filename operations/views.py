from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import CleanerProfile, EmploymentStatus, User
from accounts.serializers import CleanerSerializer
from operations.models import (
    AttendanceRecord,
    AttendanceStatus,
    CleaningTask,
    Notification,
    Room,
    RoomAssignment,
    RoomStatus,
    TaskStatus,
)
from operations.serializers import (
    AttendanceRecordSerializer,
    BulkAssignSerializer,
    CheckInOutSerializer,
    CleaningTaskSerializer,
    CompleteTaskSerializer,
    CreateTaskFromAssignmentSerializer,
    DashboardStatsSerializer,
    ExportReportRequestSerializer,
    ExportReportResponseSerializer,
    NotificationSerializer,
    PerformanceReportSerializer,
    ReassignSerializer,
    RoomAssignmentSerializer,
    RoomSerializer,
    StartTaskSerializer,
    VerifyTaskSerializer,
    WeeklyCompletionItemSerializer,
)
from operations.utils import (
    create_notification,
    get_supervisor_for_cleaner,
    parse_gps,
)


class CleanerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CleanerSerializer
    queryset = CleanerProfile.objects.select_related('user', 'supervisor').all()

    def get_object(self):
        return CleanerProfile.objects.get(user_id=self.kwargs['pk'])

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        profile = self.get_object()
        profile.employment_status = EmploymentStatus.INACTIVE
        profile.user.is_active = False
        profile.user.save()
        profile.save()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class RoomViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializer
    queryset = Room.objects.all()

    @action(detail=False, methods=['get'], url_path='by-qr/(?P<qr_code>[^/.]+)')
    def by_qr(self, request, qr_code=None):
        try:
            room = Room.objects.get(qr_code=qr_code)
        except Room.DoesNotExist:
            return Response({'detail': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(RoomSerializer(room, context={'request': request}).data)

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        room = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(RoomStatus.choices):
            return Response({'detail': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        room.status = new_status
        room.save()
        return Response(RoomSerializer(room, context={'request': request}).data)


class AssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RoomAssignmentSerializer
    queryset = RoomAssignment.objects.select_related('room', 'cleaner', 'assigned_by').all()

    def get_queryset(self):
        qs = super().get_queryset()
        cleaner_id = self.request.query_params.get('cleanerId')
        if cleaner_id:
            qs = qs.filter(cleaner_id=cleaner_id, is_active=True)
        return qs

    @action(detail=False, methods=['post'], url_path='bulk-assign')
    def bulk_assign(self, request):
        serializer = BulkAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room_ids = serializer.validated_data['roomIds']
        cleaner_id = serializer.validated_data['cleanerId']

        try:
            cleaner = User.objects.get(pk=cleaner_id, role='cleaner')
        except User.DoesNotExist:
            return Response({'detail': 'Cleaner not found'}, status=status.HTTP_404_NOT_FOUND)

        created = []
        with transaction.atomic():
            for room_id in room_ids:
                RoomAssignment.objects.filter(room_id=room_id, is_active=True).update(is_active=False)
                assignment = RoomAssignment.objects.create(
                    room_id=room_id,
                    cleaner=cleaner,
                    assigned_by=request.user,
                    is_active=True,
                )
                created.append(assignment)

        create_notification(
            cleaner.id,
            'New Room Assignment',
            f'You have been assigned {len(room_ids)} room(s).',
            'info',
        )

        data = RoomAssignmentSerializer(created, many=True, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reassign(self, request, pk=None):
        assignment = self.get_object()
        serializer = ReassignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_cleaner_id = serializer.validated_data['newCleanerId']

        try:
            new_cleaner = User.objects.get(pk=new_cleaner_id, role='cleaner')
        except User.DoesNotExist:
            return Response({'detail': 'Cleaner not found'}, status=status.HTTP_404_NOT_FOUND)

        assignment.is_active = False
        assignment.save()

        new_assignment = RoomAssignment.objects.create(
            room=assignment.room,
            cleaner=new_cleaner,
            assigned_by=request.user,
            is_active=True,
        )
        return Response(
            RoomAssignmentSerializer(new_assignment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CleaningTaskSerializer
    queryset = CleaningTask.objects.select_related('room', 'cleaner', 'assignment', 'verified_by').all()
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        cleaner_id = self.request.query_params.get('cleanerId')
        status_filter = self.request.query_params.get('status')
        if cleaner_id:
            qs = qs.filter(cleaner_id=cleaner_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=False, methods=['get'], url_path='pending-verification')
    def pending_verification(self, request):
        tasks = self.get_queryset().filter(status=TaskStatus.PENDING_VERIFICATION)
        return Response(CleaningTaskSerializer(tasks, many=True, context={'request': request}).data)

    @action(detail=False, methods=['post'], url_path='from-assignment')
    def from_assignment(self, request):
        serializer = CreateTaskFromAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        task = CleaningTask.objects.create(
            room_id=data['roomId'],
            cleaner_id=data['cleanerId'],
            assignment_id=data['assignmentId'],
            status=TaskStatus.ASSIGNED,
        )
        return Response(
            CleaningTaskSerializer(task, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        task = self.get_object()
        serializer = StartTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qr_code = serializer.validated_data['qrCode']
        if task.room.qr_code != qr_code:
            return Response({'detail': 'Invalid QR code for this room'}, status=status.HTTP_400_BAD_REQUEST)

        gps = parse_gps(serializer.validated_data.get('gps'))
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = timezone.now()
        task.qr_verified = True
        task.gps_start_lat = gps.get('lat')
        task.gps_start_lng = gps.get('lng')
        task.gps_start_accuracy = gps.get('accuracy')
        task.save()

        task.room.status = RoomStatus.IN_PROGRESS
        task.room.save()

        return Response(CleaningTaskSerializer(task, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='before-photo')
    def before_photo(self, request, pk=None):
        task = self.get_object()
        photo = request.FILES.get('photo') or request.data.get('photoUrl')
        if hasattr(photo, 'read'):
            task.before_photo = photo
        elif isinstance(photo, str) and photo.startswith('http'):
            task.before_photo = None
        task.save()
        return Response(CleaningTaskSerializer(task, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='after-photo')
    def after_photo(self, request, pk=None):
        task = self.get_object()
        photo = request.FILES.get('photo') or request.data.get('photoUrl')
        if hasattr(photo, 'read'):
            task.after_photo = photo
        task.save()
        return Response(CleaningTaskSerializer(task, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        if not task.before_photo and not request.data.get('beforePhotoUrl'):
            return Response({'detail': 'Before and after photos are required'}, status=status.HTTP_400_BAD_REQUEST)
        if not task.after_photo and not request.data.get('afterPhotoUrl'):
            return Response({'detail': 'Before and after photos are required'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CompleteTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gps = parse_gps(serializer.validated_data.get('gps'))

        task.status = TaskStatus.PENDING_VERIFICATION
        task.completed_at = timezone.now()
        task.gps_complete_lat = gps.get('lat')
        task.gps_complete_lng = gps.get('lng')
        task.gps_complete_accuracy = gps.get('accuracy')
        task.save()

        task.room.status = RoomStatus.PENDING_VERIFICATION
        task.room.save()

        supervisor_id = get_supervisor_for_cleaner(task.cleaner)
        if supervisor_id:
            create_notification(
                supervisor_id,
                'Task Completed',
                f'Task #{task.pk} is awaiting verification.',
                'success',
            )

        return Response(CleaningTaskSerializer(task, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        task = self.get_object()
        serializer = VerifyTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data['action']
        status_map = {
            'approve': TaskStatus.APPROVED,
            'reject': TaskStatus.REJECTED,
            're_cleaning': TaskStatus.RE_CLEANING,
        }

        task.status = status_map[action_type]
        task.verified_at = timezone.now()
        task.verified_by = request.user
        task.rejection_reason = serializer.validated_data.get('reason', '')
        task.supervisor_rating = serializer.validated_data.get('rating')
        task.save()

        room_status = RoomStatus.CLEAN if action_type == 'approve' else RoomStatus.DIRTY
        task.room.status = room_status
        task.room.save()

        if action_type == 'reject':
            create_notification(
                task.cleaner_id,
                'Task Rejected',
                task.rejection_reason or 'Your cleaning task was rejected.',
                'error',
            )

        return Response(CleaningTaskSerializer(task, context={'request': request}).data)


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AttendanceRecordSerializer
    queryset = AttendanceRecord.objects.select_related('cleaner').all()

    def get_queryset(self):
        qs = super().get_queryset()
        cleaner_id = self.request.query_params.get('cleanerId')
        if cleaner_id:
            qs = qs.filter(cleaner_id=cleaner_id)
        return qs

    @action(detail=False, methods=['get'], url_path='today/(?P<cleaner_id>[^/.]+)')
    def today(self, request, cleaner_id=None):
        today = timezone.localdate()
        record = AttendanceRecord.objects.filter(cleaner_id=cleaner_id, date=today).first()
        if not record:
            return Response(None)
        return Response(AttendanceRecordSerializer(record).data)

    @action(detail=False, methods=['post'], url_path='check-in')
    def check_in(self, request):
        serializer = CheckInOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cleaner_id = serializer.validated_data.get('cleanerId') or request.user.id
        gps = parse_gps(serializer.validated_data.get('gps'))

        today = timezone.localdate()
        now = timezone.now()
        hour = now.hour
        att_status = AttendanceStatus.LATE if hour > 8 else AttendanceStatus.PRESENT

        record, _ = AttendanceRecord.objects.update_or_create(
            cleaner_id=cleaner_id,
            date=today,
            defaults={
                'check_in': now,
                'status': att_status,
                'gps_check_in_lat': gps.get('lat'),
                'gps_check_in_lng': gps.get('lng'),
                'gps_check_in_accuracy': gps.get('accuracy'),
            },
        )

        supervisor_id = get_supervisor_for_cleaner(record.cleaner)
        if supervisor_id:
            create_notification(
                supervisor_id,
                'Cleaner Checked In',
                f'{record.cleaner.get_full_name()} checked in.',
                'info',
            )

        return Response(AttendanceRecordSerializer(record).data)

    @action(detail=False, methods=['post'], url_path='check-out')
    def check_out(self, request):
        serializer = CheckInOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cleaner_id = serializer.validated_data.get('cleanerId') or request.user.id
        gps = parse_gps(serializer.validated_data.get('gps'))

        today = timezone.localdate()
        try:
            record = AttendanceRecord.objects.get(cleaner_id=cleaner_id, date=today)
        except AttendanceRecord.DoesNotExist:
            return Response({'detail': 'No check-in found for today'}, status=status.HTTP_400_BAD_REQUEST)

        record.check_out = timezone.now()
        record.gps_check_out_lat = gps.get('lat')
        record.gps_check_out_lng = gps.get('lng')
        record.gps_check_out_accuracy = gps.get('accuracy')
        record.save()

        return Response(AttendanceRecordSerializer(record).data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['patch'], url_path='read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)


class DashboardStatsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DashboardStatsSerializer

    def get(self, request):
        today = timezone.localdate()
        today_attendance = AttendanceRecord.objects.filter(date=today)
        active_assignments = RoomAssignment.objects.filter(is_active=True)
        active_cleaners = CleanerProfile.objects.filter(
            employment_status=EmploymentStatus.ACTIVE,
            user__is_active=True,
        ).count()

        completed_tasks = CleaningTask.objects.filter(status=TaskStatus.APPROVED).count()
        total_tasks = CleaningTask.objects.count()
        completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks else 0, 1)

        completed_with_times = CleaningTask.objects.filter(
            status=TaskStatus.APPROVED,
            started_at__isnull=False,
            completed_at__isnull=False,
        )
        avg_minutes = 42.0
        if completed_with_times.exists():
            total_minutes = sum(
                (t.completed_at - t.started_at).total_seconds() / 60
                for t in completed_with_times
            )
            avg_minutes = round(total_minutes / completed_with_times.count(), 1)

        stats = {
            'totalCleaners': active_cleaners,
            'cleanersPresent': today_attendance.filter(
                status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]
            ).count(),
            'cleanersAbsent': today_attendance.filter(status=AttendanceStatus.ABSENT).count(),
            'totalRoomsAssigned': active_assignments.count(),
            'roomsCompleted': Room.objects.filter(status=RoomStatus.CLEAN).count(),
            'roomsPending': Room.objects.filter(
                status__in=[RoomStatus.DIRTY, RoomStatus.IN_PROGRESS]
            ).count(),
            'roomsOverdue': Room.objects.filter(status=RoomStatus.OVERDUE).count(),
            'tasksAwaitingVerification': CleaningTask.objects.filter(
                status=TaskStatus.PENDING_VERIFICATION
            ).count(),
            'completionRate': completion_rate,
            'averageCleaningTime': avg_minutes,
        }
        return Response(DashboardStatsSerializer(stats).data)


@extend_schema(responses=WeeklyCompletionItemSerializer(many=True))
class WeeklyCompletionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WeeklyCompletionItemSerializer

    def get(self, request):
        data = [
            {'day': 'Mon', 'completed': 12, 'assigned': 15},
            {'day': 'Tue', 'completed': 14, 'assigned': 16},
            {'day': 'Wed', 'completed': 11, 'assigned': 14},
            {'day': 'Thu', 'completed': 16, 'assigned': 18},
            {'day': 'Fri', 'completed': 13, 'assigned': 15},
            {'day': 'Sat', 'completed': 8, 'assigned': 10},
            {'day': 'Sun', 'completed': 6, 'assigned': 8},
        ]
        return Response(WeeklyCompletionItemSerializer(data, many=True).data)


@extend_schema(responses=PerformanceReportSerializer(many=True))
class PerformanceReportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PerformanceReportSerializer

    def get(self, request):
        reports = []
        for profile in CleanerProfile.objects.select_related('user'):
            rooms_cleaned = CleaningTask.objects.filter(
                cleaner=profile.user,
                status=TaskStatus.APPROVED,
            ).count()
            total_attendance = AttendanceRecord.objects.filter(cleaner=profile.user).count()
            present = AttendanceRecord.objects.filter(
                cleaner=profile.user,
                status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE],
            ).count()
            attendance_rate = round((present / total_attendance * 100) if total_attendance else 0, 1)

            completed = CleaningTask.objects.filter(
                cleaner=profile.user,
                status=TaskStatus.APPROVED,
                started_at__isnull=False,
                completed_at__isnull=False,
            )
            avg_time = 42.0
            if completed.exists():
                avg_time = round(
                    sum((t.completed_at - t.started_at).total_seconds() / 60 for t in completed)
                    / completed.count(),
                    1,
                )

            reports.append({
                'cleanerId': profile.user_id,
                'cleanerName': profile.user.get_full_name(),
                'roomsCleaned': rooms_cleaned,
                'completionRate': float(profile.performance_score),
                'averageTimeMinutes': avg_time,
                'attendanceRate': attendance_rate,
                'performanceScore': profile.performance_score,
            })

        return Response(PerformanceReportSerializer(reports, many=True).data)


@extend_schema(
    request=ExportReportRequestSerializer,
    responses=ExportReportResponseSerializer,
)
class ExportReportView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExportReportRequestSerializer

    def post(self, request):
        report_type = request.data.get('type', 'pdf')
        report_name = request.data.get('reportName', 'report')
        return Response(ExportReportResponseSerializer({'url': f'#export-{report_type}-{report_name}'}).data)
