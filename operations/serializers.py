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
    qr_code = serializers.CharField()
    location_id = serializers.PrimaryKeyRelatedField(
        source='location',
        queryset=Location.objects.all(),
    )

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
            'qr_code',
            'location_id',
            'deadline',
        ]


class RoomAssignmentSerializer(serializers.ModelSerializer):
    roomId = serializers.IntegerField(source='room_id')
    cleanerId = serializers.IntegerField(source='cleaner_id')
    assignedBy = serializers.IntegerField(source='assigned_by_id', allow_null=True)
    assignedAt = serializers.DateTimeField(source='assigned_at', read_only=True)
    isActive = serializers.BooleanField(source='is_active', required=False)

    class Meta:
        model = RoomAssignment
        fields = ['id', 'roomId', 'cleanerId', 'assignedBy', 'assignedAt', 'isActive']


class BulkAssignSerializer(serializers.Serializer):
    room_ids = serializers.ListField(child=serializers.IntegerField(), min_length=1)
    cleaner_id = serializers.IntegerField()


class ReassignSerializer(serializers.Serializer):
    new_cleaner_id = serializers.IntegerField()


class CleaningTaskSerializer(serializers.ModelSerializer):
    before_photo_url = serializers.SerializerMethodField()
    after_photo_url = serializers.SerializerMethodField()
    gps_start = serializers.SerializerMethodField()
    gps_complete = serializers.SerializerMethodField()

    class Meta:
        model = CleaningTask
        fields = [
            'id',
            'room_id',
            'cleaner_id',
            'assignment_id',
            'status',
            'started_at',
            'completed_at',
            'verified_at',
            'verified_by',
            'before_photo_url',
            'after_photo_url',
            'rejection_reason',
            'supervisor_rating',
            'gps_start',
            'gps_complete',
            'qr_verified',
            'estimated_duration_minutes',
        ]
        read_only_fields = [
            'id',
            'started_at',
            'completed_at',
            'verified_at',
            'verified_by',
            'before_photo_url',
            'after_photo_url',
            'rejection_reason',
            'supervisor_rating',
            'gps_start',
            'gps_complete',
            'qr_verified',
        ]
        extra_kwargs = {
            'assignment_id': {'required': False, 'allow_null': True},
        }

    def get_before_photo_url(self, obj):
        if obj.before_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.before_photo.url)
            return obj.before_photo.url
        return None

    def get_after_photo_url(self, obj):
        if obj.after_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.after_photo.url)
            return obj.after_photo.url
        return None

    def get_gps_start(self, obj):
        return build_gps(obj.gps_start_lat, obj.gps_start_lng, obj.gps_start_accuracy)

    def get_gps_complete(self, obj):
        return build_gps(obj.gps_complete_lat, obj.gps_complete_lng, obj.gps_complete_accuracy)


class StartTaskSerializer(serializers.Serializer):
    qr_code = serializers.CharField()
    gps = serializers.DictField(required=False)


class CompleteTaskSerializer(serializers.Serializer):
    gps = serializers.DictField(required=False)


class VerifyTaskSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject', 're_cleaning'])
    reason = serializers.CharField(required=False, allow_blank=True)
    rating = serializers.IntegerField(required=False, min_value=1, max_value=5)


class CreateTaskFromAssignmentSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField()
    room_id = serializers.IntegerField()
    cleaner_id = serializers.IntegerField()


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
