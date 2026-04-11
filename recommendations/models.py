"""Recommendation domain models."""

from __future__ import annotations

from django.db import models


ENGLISH_LEVEL_CHOICES = (
    ("A1", "A1"),
    ("A2", "A2"),
    ("B1", "B1"),
    ("B2", "B2"),
    ("C1", "C1"),
    ("C2", "C2"),
)

RESOURCE_TYPE_CHOICES = (
    ("course", "Course"),
    ("video", "Video"),
    ("article", "Article"),
    ("practice", "Practice"),
    ("book", "Book"),
)


class RecommendationResource(models.Model):
    """Curated learning resource for specific directions and language levels."""

    direction = models.CharField(
        max_length=120,
        db_index=True,
        help_text="Career direction (e.g., backend, frontend, data science)",
    )
    min_english_level = models.CharField(
        max_length=2,
        choices=ENGLISH_LEVEL_CHOICES,
        default="A1",
        help_text="Minimum required English level",
    )
    max_english_level = models.CharField(
        max_length=2,
        choices=ENGLISH_LEVEL_CHOICES,
        default="C2",
        help_text="Maximum English level for which this resource is suitable",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField()
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        default="course",
    )
    priority = models.PositiveSmallIntegerField(
        default=100,
        help_text="Lower value = higher priority in recommendations",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["priority", "id"]
        indexes = [
            models.Index(fields=["direction", "is_active"]),
            models.Index(fields=["min_english_level", "max_english_level"]),
        ]
        verbose_name = "recommendation resource"
        verbose_name_plural = "recommendation resources"

    def __str__(self) -> str:
        return f"{self.direction}: {self.title}"
