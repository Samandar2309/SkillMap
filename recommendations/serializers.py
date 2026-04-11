"""Serializers for recommendation endpoints."""

from rest_framework import serializers


class RecommendationItemSerializer(serializers.Serializer):
    """Serializes a single recommendation resource."""

    direction = serializers.CharField(label="Direction", help_text="Target career direction.")
    min_english_level = serializers.CharField(
        label="Minimum English level",
        help_text="Minimum CEFR level compatible with this resource.",
    )
    max_english_level = serializers.CharField(
        label="Maximum English level",
        help_text="Maximum CEFR level compatible with this resource.",
    )
    title = serializers.CharField(label="Title", help_text="Resource title.")
    description = serializers.CharField(
        allow_blank=True,
        label="Description",
        help_text="Short explanation of the resource.",
    )
    url = serializers.URLField(label="URL", help_text="Resource URL.")
    resource_type = serializers.CharField(label="Resource type", help_text="Type of resource such as course or article.")
    priority = serializers.IntegerField(label="Priority", help_text="Lower value means higher priority.")


class RecommendationListResponseSerializer(serializers.Serializer):
    """Serialized pageless response for recommendation endpoint."""

    count = serializers.IntegerField(label="Count", help_text="Number of recommended resources.")
    results = RecommendationItemSerializer(many=True, label="Results", help_text="List of recommended resources.")

