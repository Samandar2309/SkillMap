"""Serializers for user authentication and profile management."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only user profile serializer."""

    class Meta:
        model = User
        fields = ("id", "email", "is_verified", "created_at")
        read_only_fields = fields


class RegisterResponseSerializer(serializers.Serializer):
    """Serializer for registration success response."""

    message = serializers.CharField(
        label="Message",
        help_text="Human-readable registration result.",
    )
    user = UserSerializer(read_only=True)


class DetailResponseSerializer(serializers.Serializer):
    """Generic detail response serializer."""

    detail = serializers.CharField(
        label="Detail",
        help_text="Human-readable status or error message.",
    )


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration with email and password."""

    email = serializers.EmailField(
        required=True,
        label="Email",
        help_text="Email address used to create and later sign in to the account.",
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        label="Password",
        help_text="Choose a strong password for the new account.",
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        label="Confirm password",
        help_text="Repeat the password to confirm registration.",
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("email", "password", "password_confirm")

    def validate_email(self, value):
        normalized = User.objects.normalize_email(value)
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(_("A user with this email already exists."))
        return normalized

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")}
            )

        temp_user = User(email=attrs.get("email"))
        validate_password(attrs["password"], user=temp_user)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return User.objects.create_user(
            password=password,
            is_verified=False,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    """Serializer for email/password login."""

    email = serializers.EmailField(
        required=True,
        label="Email",
        help_text="Email address associated with the user account.",
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        label="Password",
        help_text="Account password.",
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        email = User.objects.normalize_email(attrs.get("email"))
        password = attrs.get("password")

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise AuthenticationFailed(_("Invalid email or password.")) from exc

        if not user.check_password(password):
            raise AuthenticationFailed(_("Invalid email or password."))

        if not user.is_active:
            raise AuthenticationFailed(_("This account is inactive."))

        if not user.is_verified:
            raise AuthenticationFailed(_("Please verify your email before logging in."))

        attrs["user"] = user
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification token validation."""

    uid = serializers.CharField(
        required=True,
        label="UID",
        help_text="Base64-encoded user identifier from the verification link.",
    )
    token = serializers.CharField(
        required=True,
        label="Token",
        help_text="One-time verification token from the verification link.",
    )


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response payload."""

    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UserSerializer(read_only=True)

