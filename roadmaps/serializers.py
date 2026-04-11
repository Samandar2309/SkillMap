from __future__ import annotations

from rest_framework import serializers

from .models import Phase, Roadmap, Task


class TaskSerializer(serializers.ModelSerializer):
    """Task serializer for nested roadmap reads."""

    title = serializers.CharField(label="Task title", help_text="Short title for the task.")
    description = serializers.CharField(
        label="Task description",
        help_text="Detailed explanation of what the learner should do.",
        required=False,
        allow_blank=True,
    )
    resource_link = serializers.URLField(
        label="Resource link",
        help_text="Optional URL to a learning resource for this task.",
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ("is_completed",)


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Restricted serializer for task completion updates."""

    is_completed = serializers.BooleanField(
        label="Completed",
        help_text="Mark the task as completed or not completed.",
    )

    class Meta:
        model = Task
        fields = ("id", "is_completed")
        read_only_fields = ("id",)


class PhaseSerializer(serializers.ModelSerializer):
    """Nested phase serializer with tasks."""

    tasks = TaskSerializer(many=True, read_only=True)
    title = serializers.CharField(label="Phase title", help_text="Name of the phase.")
    order = serializers.IntegerField(label="Phase order", help_text="Ordering of the phase in the roadmap.")

    class Meta:
        model = Phase
        fields = ("id", "roadmap", "title", "order", "is_completed", "tasks")
        read_only_fields = ("roadmap",)


class RoadmapSerializer(serializers.ModelSerializer):
    """Roadmap serializer with nested phases and tasks."""

    phases = PhaseSerializer(many=True, read_only=True)
    title = serializers.CharField(label="Roadmap title", help_text="Title of the generated roadmap.")
    estimated_months = serializers.IntegerField(
        label="Estimated months",
        help_text="Approximate number of months needed to complete the roadmap.",
    )

    class Meta:
        model = Roadmap
        fields = (
            "id",
            "user",
            "title",
            "estimated_months",
            "is_completed",
            "created_at",
            "phases",
        )
        read_only_fields = ("user", "created_at")


class RoadmapErrorSerializer(serializers.Serializer):
    """Error response serializer for roadmap endpoints."""

    detail = serializers.CharField(label="Detail", help_text="Human readable error message.")
    code = serializers.CharField(
        required=False,
        allow_blank=True,
        label="Error code",
        help_text="Machine-readable error code when available.",
    )


