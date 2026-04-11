from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from roadmaps.models import Task

from .models import StudyTimeLog, UserProgress


class UserProgressSerializer(serializers.ModelSerializer):
    """Serializer for user gamification counters."""

    total_points = serializers.IntegerField(label="Total points", help_text="Total gamification points earned.")
    current_streak = serializers.IntegerField(label="Current streak", help_text="Current consecutive activity streak.")
    longest_streak = serializers.IntegerField(label="Longest streak", help_text="Longest streak ever achieved.")

    class Meta:
        model = UserProgress
        fields = ("total_points", "current_streak", "longest_streak")


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard analytics payload."""

    progress = UserProgressSerializer(
        read_only=True,
        label="Progress",
        help_text="Gamification counters for the authenticated user.",
    )
    roadmap_completion_percentage = serializers.FloatField(
        read_only=True,
        label="Roadmap completion percentage",
        help_text="Percentage of roadmap tasks completed.",
    )
    completed_tasks_count = serializers.IntegerField(
        read_only=True,
        label="Completed tasks count",
        help_text="Count of completed tasks in the roadmap.",
    )
    total_tasks_count = serializers.IntegerField(
        read_only=True,
        label="Total tasks count",
        help_text="Total count of tasks in the roadmap.",
    )


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    """Serializer for top user rankings."""

    email = serializers.EmailField(
        source="user.email",
        read_only=True,
        label="Email",
        help_text="User email used as leaderboard identifier.",
    )
    total_points = serializers.IntegerField(label="Total points", help_text="Total earned points.")
    current_streak = serializers.IntegerField(label="Current streak", help_text="Current activity streak.")

    class Meta:
        model = UserProgress
        fields = ("email", "total_points", "current_streak")


class StudyTimeLogSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating today's study time log."""

    task_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    is_falling_behind = serializers.BooleanField(read_only=True)
    deficit_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = StudyTimeLog
        fields = (
            "id",
            "date",
            "planned_minutes",
            "actual_minutes",
            "task",
            "task_id",
            "is_falling_behind",
            "deficit_minutes",
        )
        read_only_fields = ("id", "task", "is_falling_behind", "deficit_minutes")
        extra_kwargs = {
            "date": {"required": False},
        }

    def validate_planned_minutes(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("planned_minutes must be greater than 0.")
        if value > 1440:
            raise serializers.ValidationError("planned_minutes cannot exceed 1440.")
        return value

    def validate_actual_minutes(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError("actual_minutes cannot be negative.")
        if value > 1440:
            raise serializers.ValidationError("actual_minutes cannot exceed 1440.")
        return value

    def validate_task_id(self, value: int | None) -> int | None:
        if value is None:
            return value

        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError("Authenticated user is required.")

        if not Task.objects.filter(pk=value, phase__roadmap__user=request.user).exists():
            raise serializers.ValidationError("Task does not belong to the current user.")

        return value

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        date_value = validated_data.get("date") or timezone.localdate()
        task_id = validated_data.pop("task_id", None)
        task = Task.objects.filter(pk=task_id).first() if task_id else None

        defaults = {
            "planned_minutes": validated_data.get("planned_minutes", 120),
            "actual_minutes": validated_data["actual_minutes"],
            "task": task,
        }
        instance, _ = StudyTimeLog.objects.update_or_create(
            user=user,
            date=date_value,
            defaults=defaults,
        )
        return instance
