from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.models import User
from accounts.serializers import LoginSerializer, PasswordResetSerializer, UserSerializer


class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class RefreshTokenView(TokenRefreshView):
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class PasswordResetView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message': 'Password reset link sent to your email.'})


class UserListCreateView(generics.ListCreateAPIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_queryset(self):
        qs = User.objects.all()
        print(qs)
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

    def perform_create(self, serializer):
        email = self.request.data.get('email')
        password = self.request.data.get('password', 'changeme123')
        role = self.request.data.get('role', 'supervisor')
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=self.request.data.get('firstName', ''),
            last_name=self.request.data.get('lastName', ''),
            phone=self.request.data.get('phone', ''),
            role=role,
        )
        serializer.instance = user
