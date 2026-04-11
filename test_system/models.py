from __future__ import annotations

from django.conf import settings
from django.db import models


class Question(models.Model):
    """A single aptitude question shown to users."""

    text = models.TextField()
    skill_category = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Question #{self.pk}: {self.skill_category}"


class Choice(models.Model):
    """A selectable answer option tied to a question."""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    text = models.CharField(max_length=255)
    points = models.IntegerField(default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"Choice #{self.pk} for Question #{self.question_id}"


class TestAttempt(models.Model):
    """Stores a submitted aptitude test attempt for one user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_attempts",
    )
    total_score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Attempt #{self.pk} by {self.user} ({self.total_score})"


class UserResponse(models.Model):
    """Stores one answered question inside a test attempt."""

    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_question_per_attempt",
            )
        ]

    def __str__(self) -> str:
        return (
            f"Response #{self.pk}: attempt={self.attempt_id}, "
            f"question={self.question_id}, choice={self.selected_choice_id}"
        )
