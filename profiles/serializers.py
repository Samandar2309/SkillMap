from __future__ import annotations

from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for reading and partially updating a user's profile."""

    direction = serializers.CharField(
        required=False,
        allow_blank=True,
        label="Career direction",
        help_text="Target career direction such as backend, frontend, or data science.",
    )
    english_level = serializers.ChoiceField(
        choices=Profile._meta.get_field("english_level").choices,
        required=False,
        allow_blank=True,
        label="English level",
        help_text="Current English level using CEFR scale.",
    )
    current_goal = serializers.CharField(
        required=False,
        allow_blank=True,
        label="Current goal",
        help_text="User's current learning or career goal.",
    )

    class Meta:
        model = Profile
        fields = "__all__"
        read_only_fields = ("user", "is_onboarded", "created_at", "updated_at")


class OnboardingSerializer(serializers.ModelSerializer):
    """Serializer for completing onboarding for the current user."""

    direction = serializers.CharField(
        label="Career direction",
        help_text="Choose the target career direction.",
    )
    english_level = serializers.ChoiceField(
        choices=Profile._meta.get_field("english_level").choices,
        label="English level",
        help_text="Choose the user's current English level.",
    )
    current_goal = serializers.CharField(
        label="Current goal",
        help_text="Describe the immediate learning goal.",
    )

    class Meta:
        model = Profile
        fields = ("direction", "english_level", "current_goal")

    def validate(self, attrs):
        required_fields = ("direction", "english_level", "current_goal")
        missing = [field for field in required_fields if not attrs.get(field)]
        if missing:
            raise serializers.ValidationError(
                {field: "This field is required." for field in missing}
            )
        return attrs

    def update(self, instance, validated_data):
        instance.direction = validated_data.get("direction", instance.direction)
        instance.english_level = validated_data.get(
            "english_level",
            instance.english_level,
        )
        instance.current_goal = validated_data.get("current_goal", instance.current_goal)
        instance.is_onboarded = True
        instance.save(
            update_fields=[
                "direction",
                "english_level",
                "current_goal",
                "is_onboarded",
                "updated_at",
            ]
        )
        return instance

