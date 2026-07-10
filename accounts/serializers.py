from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import CleanerProfile, User


class UserSerializer(serializers.ModelSerializer):
    avatarUrl = serializers.SerializerMethodField()
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    isActive = serializers.BooleanField(source='is_active')
    createdAt = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'firstName',
            'lastName',
            'role',
            'phone',
            'avatarUrl',
            'isActive',
            'createdAt',
        ]
        read_only_fields = ['id', 'createdAt']

    def get_avatarUrl(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class CleanerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', required=True, allow_blank=False)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    role = serializers.CharField(source='user.role', read_only=True)
    phone = serializers.CharField(source='user.phone', required=False, allow_blank=True)
    avatar_url = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    created_at = serializers.DateTimeField(source='user.date_joined', read_only=True)
    employee_id = serializers.CharField()
    employment_status = serializers.CharField(read_only=True)
    hire_date = serializers.DateField(required=False, default=timezone.localdate)
    performance_score = serializers.IntegerField(read_only=True)
    supervisor_id = serializers.PrimaryKeyRelatedField(
        source='supervisor',
        queryset=User.objects.filter(role='supervisor'),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = CleanerProfile
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'phone',
            'avatar_url',
            'is_active',
            'created_at',
            'employee_id',
            'employment_status',
            'hire_date',
            'performance_score',
            'supervisor_id',
        ]

    def get_avatar_url(self, obj):
        if obj.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.avatar.url)
            return obj.user.avatar.url
        return None

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        supervisor = validated_data.pop('supervisor', None)
        user = User.objects.create_user(
            username=user_data['email'],
            email=user_data['email'],
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            phone=user_data.get('phone', ''),
            role='cleaner',
        )
        user.set_unusable_password()
        user.save()
        return CleanerProfile.objects.create(user=user, supervisor=supervisor, **validated_data)

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        supervisor = validated_data.pop('supervisor', serializers.empty)

        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        if supervisor is not serializers.empty:
            instance.supervisor = supervisor

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs['username']
        password = attrs['password']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid username or password')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid username or password')

        if not user.is_active:
            raise serializers.ValidationError('Account is inactive')

        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user, context=self.context)
        return {
            'refresh': str(refresh),
            'token': str(refresh.access_token),
            'user': user_serializer.data,
        }


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError('No account found with this email')
        return value
