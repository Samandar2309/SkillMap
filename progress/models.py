from __future__ import annotations

from django.conf import settings
from django.db import models


class UserProgress(models.Model):
    """Stores gamification counters for a single user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress",
    )
    total_points = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-total_points", "-current_streak", "user_id"]

    def __str__(self) -> str:
        return (
            f"Progress for {self.user}: points={self.total_points}, "
            f"streak={self.current_streak}"
        )


class StudyTimeLog(models.Model):
    """Stores daily planned vs actual study time for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_time_logs",
    )
    task = models.ForeignKey(
        "roadmaps.Task",
        on_delete=models.SET_NULL,
        related_name="study_time_logs",
        null=True,
        blank=True,
    )
    date = models.DateField()
    planned_minutes = models.PositiveIntegerField(default=120)
    actual_minutes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date"],
                name="unique_study_time_log_per_user_per_date",
            )
        ]

    @property
    def deficit_minutes(self) -> int:
        """How many minutes the user is behind the daily plan for this log."""
        return max(0, self.planned_minutes - self.actual_minutes)

    @property
    def is_falling_behind(self) -> bool:
        """True when actual study minutes are below planned minutes."""
        return self.actual_minutes < self.planned_minutes

    def __str__(self) -> str:
        return (
            f"StudyTimeLog(user={self.user_id}, date={self.date}, "
            f"planned={self.planned_minutes}, actual={self.actual_minutes})"
        )
