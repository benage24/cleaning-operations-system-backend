from rest_framework import serializers

from operations.models import (
    AttendanceRecord,
    CleaningTask,
    Location,
    Notification,
    Room,
    RoomAssignment,
)
from operations.utils import build_gps


class LocationSerializer(serializers.ModelSerializer):
    parentId = serializers.PrimaryKeyRelatedField(
        source='parent',
        queryset=Location.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Location
        fields = ['id', 'name', 'type', 'parentId']


class RoomSerializer(serializers.ModelSerializer):
    qrCode = serializers.CharField(source='qr_code')
    locationId = serializers.PrimaryKeyRelatedField(source='location', queryset=Location.objects.all())

    class Meta:
        model = Room
        fields = [
            'id',
            'number',
            'name',
            'building',
            'floor',
            'department',
            'status',
            'qrCode',
            'locationId',
            'deadline',
        ]


class RoomAssignmentSerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source='room_id')
    cleanerId = serializers.IntegerField(source='cleaner_id')
    assignedBy = serializers.IntegerField(source='assigned_by_id', allow_null=True)
    assignedAt = serializers.DateTimeField(source='assigned_at', read_only=True)
    isActive = serializers.BooleanField(source='is_active')

    class Meta:
        model = RoomAssignment
        fields = ['id', 'roomId', 'cleanerId', 'assignedBy', 'assignedAt', 'isActive']


class BulkAssignSerializer(serializers.Serializer):
    roomIds = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    cleanerId = serializers.IntegerField()


class ReassignSerializer(serializers.Serializer):
    newCleanerId = serializers.IntegerField()


class CleaningTaskSerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source='room_id')
    cleanerId = serializers.IntegerField(source='cleaner_id')
    assignmentId = serializers.IntegerField(source='assignment_id', allow_null=True)
    startedAt = serializers.DateTimeField(source='started_at', read_only=True)
    completedAt = serializers.DateTimeField(source='completed_at', read_only=True)
    verifiedAt = serializers.DateTimeField(source='verified_at', read_only=True)
    verifiedBy = serializers.PrimaryKeyRelatedField(source='verified_by', read_only=True)
    beforePhotoUrl = serializers.SerializerMethodField()
    afterPhotoUrl = serializers.SerializerMethodField()
    rejectionReason = serializers.CharField(source='rejection_reason', read_only=True)
    supervisorRating = serializers.IntegerField(source='supervisor_rating', read_only=True)
    gpsStart = serializers.SerializerMethodField()
    gpsComplete = serializers.SerializerMethodField()
    qrVerified = serializers.BooleanField(source='qr_verified', read_only=True)
    estimatedDurationMinutes = serializers.IntegerField(source='estimated_duration_minutes')

    class Meta:
        model = CleaningTask
        fields = [
            'id',
            'roomId',
            'cleanerId',
            'assignmentId',
            'status',
            'startedAt',
            'completedAt',
            'verifiedAt',
            'verifiedBy',
            'beforePhotoUrl',
            'afterPhotoUrl',
            'rejectionReason',
            'supervisorRating',
            'gpsStart',
            'gpsComplete',
            'qrVerified',
            'estimatedDurationMinutes',
        ]

    def get_beforePhotoUrl(self, obj):
        if obj.before_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.before_photo.url)
            return obj.before_photo.url
        return None

    def get_afterPhotoUrl(self, obj):
        if obj.after_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.after_photo.url)
            return obj.after_photo.url
        return None

    def get_gpsStart(self, obj):
        return build_gps(obj.gps_start_lat, obj.gps_start_lng, obj.gps_start_accuracy)

    def get_gpsComplete(self, obj):
        return build_gps(obj.gps_complete_lat, obj.gps_complete_lng, obj.gps_complete_accuracy)


class StartTaskSerializer(serializers.Serializer):
    qrCode = serializers.CharField()
    gps = serializers.DictField(required=False)


class CompleteTaskSerializer(serializers.Serializer):
    gps = serializers.DictField(required=False)


class VerifyTaskSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject', 're_cleaning'])
    reason = serializers.CharField(required=False, allow_blank=True)
    rating = serializers.IntegerField(required=False, min_value=1, max_value=5)


class CreateTaskFromAssignmentSerializer(serializers.Serializer):
    assignmentId = serializers.IntegerField()
    roomId = serializers.IntegerField()
    cleanerId = serializers.IntegerField()


class AttendanceRecordSerializer(serializers.ModelSerializer):
    cleanerId = serializers.PrimaryKeyRelatedField(source='cleaner', read_only=True)
    checkIn = serializers.DateTimeField(source='check_in', read_only=True)
    checkOut = serializers.DateTimeField(source='check_out', read_only=True)
    gpsCheckIn = serializers.SerializerMethodField()
    gpsCheckOut = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = ['id', 'cleanerId', 'date', 'checkIn', 'checkOut', 'status', 'gpsCheckIn', 'gpsCheckOut']

    def get_gpsCheckIn(self, obj):
        return build_gps(obj.gps_check_in_lat, obj.gps_check_in_lng, obj.gps_check_in_accuracy)

    def get_gpsCheckOut(self, obj):
        return build_gps(obj.gps_check_out_lat, obj.gps_check_out_lng, obj.gps_check_out_accuracy)


class CheckInOutSerializer(serializers.Serializer):
    cleanerId = serializers.IntegerField(required=False)
    gps = serializers.DictField(required=False)


class NotificationSerializer(serializers.ModelSerializer):
    userId = serializers.PrimaryKeyRelatedField(source='user', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'userId', 'title', 'message', 'type', 'read', 'createdAt']


class DashboardStatsSerializer(serializers.Serializer):
    totalCleaners = serializers.IntegerField()
    cleanersPresent = serializers.IntegerField()
    cleanersAbsent = serializers.IntegerField()
    totalRoomsAssigned = serializers.IntegerField()
    roomsCompleted = serializers.IntegerField()
    roomsPending = serializers.IntegerField()
    roomsOverdue = serializers.IntegerField()
    tasksAwaitingVerification = serializers.IntegerField()
    completionRate = serializers.FloatField()
    averageCleaningTime = serializers.FloatField()


class PerformanceReportSerializer(serializers.Serializer):
    cleanerId = serializers.IntegerField()
    cleanerName = serializers.CharField()
    roomsCleaned = serializers.IntegerField()
    completionRate = serializers.FloatField()
    averageTimeMinutes = serializers.FloatField()
    attendanceRate = serializers.FloatField()
    performanceScore = serializers.IntegerField()


class WeeklyCompletionItemSerializer(serializers.Serializer):
    day = serializers.CharField()
    completed = serializers.IntegerField()
    assigned = serializers.IntegerField()


class ExportReportRequestSerializer(serializers.Serializer):
    type = serializers.CharField(required=False, default='pdf')
    reportName = serializers.CharField(required=False, default='report')


class ExportReportResponseSerializer(serializers.Serializer):
    url = serializers.CharField()
