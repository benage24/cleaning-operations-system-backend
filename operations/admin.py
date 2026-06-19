from django.contrib import admin

from operations.models import (
    AttendanceRecord,
    CleaningTask,
    Location,
    Notification,
    Room,
    RoomAssignment,
)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'parent')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'building', 'floor', 'status', 'qr_code')
    list_filter = ('status', 'building', 'floor')
    search_fields = ('name', 'number', 'qr_code')


@admin.register(RoomAssignment)
class RoomAssignmentAdmin(admin.ModelAdmin):
    list_display = ('room', 'cleaner', 'assigned_by', 'assigned_at', 'is_active')
    list_filter = ('is_active',)


@admin.register(CleaningTask)
class CleaningTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'cleaner', 'status', 'started_at', 'completed_at')
    list_filter = ('status',)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('cleaner', 'date', 'status', 'check_in', 'check_out')
    list_filter = ('status', 'date')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'read', 'created_at')
    list_filter = ('type', 'read')
