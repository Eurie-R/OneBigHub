from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .validators import validate_ateneo_email, get_role_from_email
from .models import OrganizationProfile, AdminOfficeProfile, Officer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password2']

    def validate_email(self, value):
        validate_ateneo_email(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        role = get_role_from_email(email)
        user = User.objects.create_user(
            username=email.split('@')[0],
            email=email,
            password=validated_data['password'],
            role=role
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role']
        read_only_fields = ['id', 'email', 'role']


# ─────────────────────────────────────────────
# Officer Serializer
# ─────────────────────────────────────────────

class OfficerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Officer
        fields = ['id', 'name', 'position']


# ─────────────────────────────────────────────
# Organization Profile Serializer
# REQ: SRS 4.1.2 Sub-Feature 4, 7
# ─────────────────────────────────────────────

class OrganizationProfileSerializer(serializers.ModelSerializer):
    officers = OfficerSerializer(many=True, read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = OrganizationProfile
        fields = [
            'id', 'email', 'role',
            'org_name', 'contact_email', 'moderator_name',
            'building', 'room_number', 'description',
            'logo', 'officers', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ─────────────────────────────────────────────
# Admin Office Profile Serializer
# REQ: SRS 4.1.2 Sub-Feature 5, 7
# ─────────────────────────────────────────────

class AdminOfficeProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = AdminOfficeProfile
        fields = [
            'id', 'email', 'role',
            'office_name', 'office_type', 'contact_email',
            'building', 'room_number', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']