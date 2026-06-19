from django.urls import include, path
from rest_framework.routers import DefaultRouter

from operations.views import (
    AssignmentViewSet,
    AttendanceViewSet,
    CleanerViewSet,
    DashboardStatsView,
    ExportReportView,
    NotificationViewSet,
    PerformanceReportView,
    RoomViewSet,
    TaskViewSet,
    WeeklyCompletionView,
)

router = DefaultRouter()
router.register('cleaners', CleanerViewSet, basename='cleaner')
router.register('rooms', RoomViewSet, basename='room')
router.register('assignments', AssignmentViewSet, basename='assignment')
router.register('tasks', TaskViewSet, basename='task')
router.register('attendance', AttendanceViewSet, basename='attendance')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/weekly-completion/', WeeklyCompletionView.as_view(), name='weekly-completion'),
    path('reports/performance/', PerformanceReportView.as_view(), name='performance-reports'),
    path('reports/export/', ExportReportView.as_view(), name='export-report'),
]
