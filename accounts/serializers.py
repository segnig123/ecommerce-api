from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for creating new customer accounts."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        help_text="Password must contain at least 8 characters."
    )

    email = serializers.EmailField(
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all())
        ],
        help_text="Unique email address for the account."
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password'
        ]
        read_only_fields = ['id']

    def validate_password(self, value):
        """Validate the password against Django's password validators."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """Create a user while securely hashing their password."""
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for displaying authenticated user profile information."""

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'date_joined',
        ]
        read_only_fields = fields


class ChangePasswordSerializer(serializers.Serializer):
    """Validate and process authenticated users' password changes."""

    old_password = serializers.CharField(
        write_only=True,
        help_text="User's current password."
    )

    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="New password that must satisfy Django's password validators."
    )

    def validate_old_password(self, value):
        """Verify that the supplied current password is correct."""
        user = self.context['request'].user

        if not user.check_password(value):
            raise serializers.ValidationError(
                "Current password is incorrect."
            )

        return value

    def validate(self, attrs):
        """Ensure the new password differs from the current password."""
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                "New password must be different from the current password."
            )

        return attrs

    def save(self):
        """Hash and save the user's new password."""
        user = self.context['request'].user

        user.set_password(self.validated_data['new_password'])
        user.save()

        return user
