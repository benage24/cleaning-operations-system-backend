from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsSupervisor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('admin', 'supervisor')


class IsCleaner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'cleaner'


class IsAdminOrSupervisor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('admin', 'supervisor')


def build_gps(lat, lng, accuracy=None):
    if lat is None or lng is None:
        return None
    data = {'latitude': lat, 'longitude': lng}
    if accuracy is not None:
        data['accuracy'] = accuracy
    return data


def parse_gps(data):
    if not data:
        return {}
    return {
        'lat': data.get('latitude'),
        'lng': data.get('longitude'),
        'accuracy': data.get('accuracy'),
    }


def create_notification(user_id, title, message, notification_type='info'):
    from operations.models import Notification

    Notification.objects.create(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
    )


def get_supervisor_for_cleaner(cleaner):
    profile = getattr(cleaner, 'cleaner_profile', None)
    if profile and profile.supervisor_id:
        return profile.supervisor_id
    supervisor = cleaner.__class__.objects.filter(role='supervisor', is_active=True).first()
    return supervisor.id if supervisor else None
