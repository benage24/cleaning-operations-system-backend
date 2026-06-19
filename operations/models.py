from django.conf import settings
from django.db import models


class LocationType(models.TextChoices):
    BUILDING = 'building', 'Building'
    FLOOR = 'floor', 'Floor'
    DEPARTMENT = 'department', 'Department'


class Location(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=LocationType.choices)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class RoomStatus(models.TextChoices):
    CLEAN = 'clean', 'Clean'
    DIRTY = 'dirty', 'Dirty'
    IN_PROGRESS = 'in_progress', 'In Progress'
    PENDING_VERIFICATION = 'pending_verification', 'Pending Verification'
    OVERDUE = 'overdue', 'Overdue'


class Room(models.Model):
    number = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    building = models.CharField(max_length=100)
    floor = models.CharField(max_length=50)
    department = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=30, choices=RoomStatus.choices, default=RoomStatus.DIRTY)
    qr_code = models.CharField(max_length=50, unique=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='rooms')
    deadline = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['building', 'floor', 'number']

    def __str__(self):
        return self.name


class RoomAssignment(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='assignments')
    cleaner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='room_assignments',
        limit_choices_to={'role': 'cleaner'},
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignments_made',
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-assigned_at']

    def __str__(self):
        return f'{self.room.name} → {self.cleaner.get_full_name()}'


class TaskStatus(models.TextChoices):
    ASSIGNED = 'assigned', 'Assigned'
    IN_PROGRESS = 'in_progress', 'In Progress'
    PENDING_VERIFICATION = 'pending_verification', 'Pending Verification'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    RE_CLEANING = 're_cleaning', 'Re-cleaning'


class CleaningTask(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='tasks')
    cleaner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cleaning_tasks',
    )
    assignment = models.ForeignKey(
        RoomAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
    )
    status = models.CharField(max_length=30, choices=TaskStatus.choices, default=TaskStatus.ASSIGNED)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_tasks',
    )
    before_photo = models.ImageField(upload_to='task_photos/before/', blank=True, null=True)
    after_photo = models.ImageField(upload_to='task_photos/after/', blank=True, null=True)
    rejection_reason = models.TextField(blank=True)
    supervisor_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    gps_start_lat = models.FloatField(null=True, blank=True)
    gps_start_lng = models.FloatField(null=True, blank=True)
    gps_start_accuracy = models.FloatField(null=True, blank=True)
    gps_complete_lat = models.FloatField(null=True, blank=True)
    gps_complete_lng = models.FloatField(null=True, blank=True)
    gps_complete_accuracy = models.FloatField(null=True, blank=True)
    qr_verified = models.BooleanField(default=False)
    estimated_duration_minutes = models.PositiveSmallIntegerField(default=45)

    class Meta:
        ordering = ['-started_at', '-id']

    def __str__(self):
        return f'Task #{self.pk} - {self.room.name}'


class AttendanceStatus(models.TextChoices):
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'
    LATE = 'late', 'Late'
    LEAVE = 'leave', 'Leave'


class AttendanceRecord(models.Model):
    cleaner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.ABSENT)
    gps_check_in_lat = models.FloatField(null=True, blank=True)
    gps_check_in_lng = models.FloatField(null=True, blank=True)
    gps_check_in_accuracy = models.FloatField(null=True, blank=True)
    gps_check_out_lat = models.FloatField(null=True, blank=True)
    gps_check_out_lng = models.FloatField(null=True, blank=True)
    gps_check_out_accuracy = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['cleaner', 'date']

    def __str__(self):
        return f'{self.cleaner.get_full_name()} - {self.date}'


class NotificationType(models.TextChoices):
    INFO = 'info', 'Info'
    SUCCESS = 'success', 'Success'
    WARNING = 'warning', 'Warning'
    ERROR = 'error', 'Error'


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.INFO)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
