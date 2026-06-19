from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CleanerProfile, EmploymentStatus, User, UserRole
from operations.models import (
    AttendanceRecord,
    AttendanceStatus,
    CleaningTask,
    Location,
    LocationType,
    Notification,
    NotificationType,
    Room,
    RoomAssignment,
    RoomStatus,
    TaskStatus,
)


class Command(BaseCommand):
    help = 'Seed demo data matching the Angular frontend mock data'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        Notification.objects.all().delete()
        AttendanceRecord.objects.all().delete()
        CleaningTask.objects.all().delete()
        RoomAssignment.objects.all().delete()
        Room.objects.all().delete()
        Location.objects.all().delete()
        CleanerProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write('Creating users...')
        admin = User.objects.create_user(
            username='admin@cleanops.com',
            email='admin@cleanops.com',
            password='admin123',
            first_name='Alex',
            last_name='Morgan',
            role=UserRole.ADMIN,
            phone='+1 555-0100',
        )
        supervisor = User.objects.create_user(
            username='supervisor@cleanops.com',
            email='supervisor@cleanops.com',
            password='supervisor123',
            first_name='Sarah',
            last_name='Chen',
            role=UserRole.SUPERVISOR,
            phone='+1 555-0101',
        )
        User.objects.create_user(
            username='lisa.park@cleanops.com',
            email='lisa.park@cleanops.com',
            password='supervisor123',
            first_name='Lisa',
            last_name='Park',
            role=UserRole.SUPERVISOR,
            phone='+1 555-0105',
        )

        cleaner1 = User.objects.create_user(
            username='cleaner@cleanops.com',
            email='cleaner@cleanops.com',
            password='cleaner123',
            first_name='James',
            last_name='Wilson',
            role=UserRole.CLEANER,
            phone='+1 555-0102',
        )
        cleaner2 = User.objects.create_user(
            username='maria.garcia@cleanops.com',
            email='maria.garcia@cleanops.com',
            password='cleaner123',
            first_name='Maria',
            last_name='Garcia',
            role=UserRole.CLEANER,
            phone='+1 555-0103',
        )
        cleaner3 = User.objects.create_user(
            username='david.kim@cleanops.com',
            email='david.kim@cleanops.com',
            password='cleaner123',
            first_name='David',
            last_name='Kim',
            role=UserRole.CLEANER,
            phone='+1 555-0104',
        )

        self.stdout.write('Creating cleaner profiles...')
        cp1 = CleanerProfile.objects.create(
            user=cleaner1,
            employee_id='CLN-001',
            employment_status=EmploymentStatus.ACTIVE,
            hire_date='2024-03-10',
            performance_score=92,
            supervisor=supervisor,
        )
        cp2 = CleanerProfile.objects.create(
            user=cleaner2,
            employee_id='CLN-002',
            employment_status=EmploymentStatus.ACTIVE,
            hire_date='2024-04-05',
            performance_score=88,
            supervisor=supervisor,
        )
        cp3 = CleanerProfile.objects.create(
            user=cleaner3,
            employee_id='CLN-003',
            employment_status=EmploymentStatus.ACTIVE,
            hire_date='2024-05-20',
            performance_score=76,
            supervisor=supervisor,
        )

        self.stdout.write('Creating locations...')
        loc1 = Location.objects.create(name='Main Building', type=LocationType.BUILDING)
        loc2 = Location.objects.create(name='Floor 1', type=LocationType.FLOOR, parent=loc1)
        loc3 = Location.objects.create(name='Floor 2', type=LocationType.FLOOR, parent=loc1)
        loc4 = Location.objects.create(name='East Wing', type=LocationType.DEPARTMENT, parent=loc2)

        now = timezone.now()
        self.stdout.write('Creating rooms...')
        r1 = Room.objects.create(
            number='101', name='Room 101', building='Main Building', floor='Floor 1',
            department='East Wing', status=RoomStatus.CLEAN, qr_code='QR-R101', location=loc4,
        )
        r2 = Room.objects.create(
            number='102', name='Room 102', building='Main Building', floor='Floor 1',
            department='East Wing', status=RoomStatus.DIRTY, qr_code='QR-R102', location=loc4,
            deadline=now + timedelta(hours=2),
        )
        r3 = Room.objects.create(
            number='103', name='Room 103', building='Main Building', floor='Floor 1',
            status=RoomStatus.IN_PROGRESS, qr_code='QR-R103', location=loc2,
        )
        r4 = Room.objects.create(
            number='201', name='Room 201', building='Main Building', floor='Floor 2',
            status=RoomStatus.PENDING_VERIFICATION, qr_code='QR-R201', location=loc3,
        )
        r5 = Room.objects.create(
            number='202', name='Room 202', building='Main Building', floor='Floor 2',
            status=RoomStatus.OVERDUE, qr_code='QR-R202', location=loc3,
            deadline=now - timedelta(hours=1),
        )
        r6 = Room.objects.create(
            number='203', name='Room 203', building='Main Building', floor='Floor 2',
            status=RoomStatus.DIRTY, qr_code='QR-R203', location=loc3,
        )

        self.stdout.write('Creating assignments...')
        a1 = RoomAssignment.objects.create(room=r2, cleaner=cleaner1, assigned_by=supervisor, is_active=True)
        a2 = RoomAssignment.objects.create(room=r3, cleaner=cleaner1, assigned_by=supervisor, is_active=True)
        a3 = RoomAssignment.objects.create(room=r4, cleaner=cleaner2, assigned_by=supervisor, is_active=True)
        a4 = RoomAssignment.objects.create(
            room=r5, cleaner=cleaner3, assigned_by=supervisor, is_active=True,
            assigned_at=now - timedelta(hours=4),
        )
        a5 = RoomAssignment.objects.create(room=r6, cleaner=cleaner2, assigned_by=supervisor, is_active=True)

        self.stdout.write('Creating tasks...')
        CleaningTask.objects.create(
            room=r3, cleaner=cleaner1, assignment=a2,
            status=TaskStatus.IN_PROGRESS,
            started_at=now - timedelta(minutes=20),
            qr_verified=True,
            gps_start_lat=40.7128, gps_start_lng=-74.006,
        )
        CleaningTask.objects.create(
            room=r4, cleaner=cleaner2, assignment=a3,
            status=TaskStatus.PENDING_VERIFICATION,
            started_at=now - timedelta(minutes=90),
            completed_at=now - timedelta(minutes=30),
            qr_verified=True,
            gps_start_lat=40.7128, gps_start_lng=-74.006,
            gps_complete_lat=40.7128, gps_complete_lng=-74.006,
        )
        CleaningTask.objects.create(
            room=r5, cleaner=cleaner3, assignment=a4,
            status=TaskStatus.ASSIGNED,
            qr_verified=False,
        )

        today = timezone.localdate()
        check_in_time = timezone.now().replace(hour=8, minute=5, second=0, microsecond=0)
        late_check_in = timezone.now().replace(hour=8, minute=25, second=0, microsecond=0)

        self.stdout.write('Creating attendance records...')
        AttendanceRecord.objects.create(
            cleaner=cleaner1, date=today, check_in=check_in_time,
            status=AttendanceStatus.PRESENT,
            gps_check_in_lat=40.7128, gps_check_in_lng=-74.006,
        )
        AttendanceRecord.objects.create(
            cleaner=cleaner2, date=today, check_in=late_check_in,
            status=AttendanceStatus.LATE,
            gps_check_in_lat=40.7128, gps_check_in_lng=-74.006,
        )
        AttendanceRecord.objects.create(
            cleaner=cleaner3, date=today, status=AttendanceStatus.ABSENT,
        )

        self.stdout.write('Creating notifications...')
        Notification.objects.create(
            user=supervisor,
            title='Task Completed',
            message='Maria Garcia completed Room 201 cleaning.',
            type=NotificationType.SUCCESS,
            read=False,
            created_at=now - timedelta(minutes=30),
        )
        Notification.objects.create(
            user=supervisor,
            title='Cleaner Checked In',
            message='James Wilson checked in at 8:05 AM.',
            type=NotificationType.INFO,
            read=False,
            created_at=now - timedelta(hours=2),
        )
        Notification.objects.create(
            user=supervisor,
            title='Overdue Room',
            message='Room 202 is past its cleaning deadline.',
            type=NotificationType.WARNING,
            read=True,
            created_at=now - timedelta(hours=1),
        )

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('Demo accounts:')
        self.stdout.write('  Admin:      admin@cleanops.com / admin123')
        self.stdout.write('  Supervisor: supervisor@cleanops.com / supervisor123')
        self.stdout.write('  Cleaner:    cleaner@cleanops.com / cleaner123')
