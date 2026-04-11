"""Django admin configuration for recommendations app."""

from django.contrib import admin

from .models import RecommendationResource


@admin.register(RecommendationResource)
class RecommendationResourceAdmin(admin.ModelAdmin):
    """Admin interface for curated learning resources."""

    list_display = (
        "id",
        "direction",
        "title",
        "resource_type",
        "min_english_level",
        "max_english_level",
        "priority",
        "is_active",
        "created_at",
    )
    list_filter = (
        "direction",
        "resource_type",
        "is_active",
        "min_english_level",
        "max_english_level",
        "created_at",
    )
    search_fields = ("title", "description", "url", "direction")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Basic Info",
            {
                "fields": ("title", "description", "url", "resource_type"),
            },
        ),
        (
            "Filtering",
            {
                "fields": ("direction", "min_english_level", "max_english_level"),
            },
        ),
        (
            "Visibility",
            {
                "fields": ("is_active", "priority"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

