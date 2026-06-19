from django.urls import path

from accounts.views import LoginView, MeView, PasswordResetView, RefreshTokenView, UserListCreateView

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshTokenView.as_view(), name='auth-refresh'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('password-reset/', PasswordResetView.as_view(), name='auth-password-reset'),
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
]
