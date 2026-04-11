from __future__ import annotations

from django.conf import settings
from django.db import models


ENGLISH_LEVEL_CHOICES = (
    ("A1", "A1"),
    ("A2", "A2"),
    ("B1", "B1"),
    ("B2", "B2"),
    ("C1", "C1"),
    ("C2", "C2"),
)


class Profile(models.Model):
    """Stores onboarding and profile metadata for a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    direction = models.CharField(max_length=100, blank=True)
    english_level = models.CharField(
        max_length=2,
        choices=ENGLISH_LEVEL_CHOICES,
        blank=True,
    )
    current_goal = models.TextField(blank=True)
    is_onboarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "profile"
        verbose_name_plural = "profiles"

    def __str__(self) -> str:
        return getattr(self.user, "email", str(self.user))
