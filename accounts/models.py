from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    SUPERVISOR = 'supervisor', 'Supervisor'
    CLEANER = 'cleaner', 'Cleaner'


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CLEANER)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    class Meta:
        ordering = ['first_name', 'last_name']

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


class EmploymentStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    ON_LEAVE = 'on_leave', 'On Leave'


class CleanerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cleaner_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
    )
    hire_date = models.DateField()
    performance_score = models.PositiveSmallIntegerField(default=0)
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_cleaners',
        limit_choices_to={'role': UserRole.SUPERVISOR},
    )

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f'{self.employee_id} - {self.user.get_full_name()}'
