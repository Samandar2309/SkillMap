"""Recommendation service with filtering logic."""

from __future__ import annotations

import logging
from typing import Any

from .models import RecommendationResource

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for generating personalized recommendations based on profile.
    
    Filters resources by user's direction and English level, with fallback
    to default catalog if database is empty.
    """

    LEVEL_RANK = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
    DEFAULT_DIRECTION = "general"

    DEFAULT_CATALOG: list[dict[str, Any]] = [
        {
            "direction": "backend",
            "min_english_level": "A2",
            "max_english_level": "B2",
            "title": "Django for Beginners",
            "description": "Practical intro to Django ORM, views, and REST API basics.",
            "url": "https://www.djangoproject.com/start/",
            "resource_type": "course",
            "priority": 10,
        },
        {
            "direction": "backend",
            "min_english_level": "B1",
            "max_english_level": "C2",
            "title": "REST API Design Best Practices",
            "description": "API versioning, error handling, auth, pagination, and idempotency.",
            "url": "https://restfulapi.net/",
            "resource_type": "article",
            "priority": 20,
        },
        {
            "direction": "backend",
            "min_english_level": "A1",
            "max_english_level": "B1",
            "title": "Python Official Documentation",
            "description": "Reference guide for Python standard library and language features.",
            "url": "https://docs.python.org/3/",
            "resource_type": "article",
            "priority": 5,
        },
        {
            "direction": "frontend",
            "min_english_level": "A2",
            "max_english_level": "C2",
            "title": "MDN Web Docs: Learn Web Development",
            "description": "Comprehensive HTML, CSS, JavaScript learning path with interactive examples.",
            "url": "https://developer.mozilla.org/en-US/docs/Learn",
            "resource_type": "course",
            "priority": 10,
        },
        {
            "direction": "frontend",
            "min_english_level": "B1",
            "max_english_level": "C2",
            "title": "React Official Documentation",
            "description": "Building interactive UIs with React hooks, components, and state management.",
            "url": "https://react.dev/",
            "resource_type": "course",
            "priority": 15,
        },
        {
            "direction": "data science",
            "min_english_level": "B1",
            "max_english_level": "C2",
            "title": "Kaggle Micro-courses",
            "description": "Hands-on data science, machine learning, and Python in interactive notebooks.",
            "url": "https://www.kaggle.com/learn",
            "resource_type": "practice",
            "priority": 10,
        },
        {
            "direction": "data science",
            "min_english_level": "B2",
            "max_english_level": "C2",
            "title": "Fast.ai Practical Deep Learning",
            "description": "Top-down approach to deep learning with practical projects.",
            "url": "https://www.fast.ai/",
            "resource_type": "course",
            "priority": 20,
        },
        {
            "direction": "general",
            "min_english_level": "A1",
            "max_english_level": "C2",
            "title": "Roadmap.sh Career Paths",
            "description": "Role-based skill trees with curated learning resources and tools.",
            "url": "https://roadmap.sh/",
            "resource_type": "article",
            "priority": 5,
        },
        {
            "direction": "general",
            "min_english_level": "A1",
            "max_english_level": "C2",
            "title": "freeCodeCamp",
            "description": "Free coding tutorials covering various languages and frameworks.",
            "url": "https://www.freecodecamp.org/",
            "resource_type": "course",
            "priority": 8,
        },
    ]

    def _normalize_level(self, english_level: str | None) -> str:
        """Normalize and validate English level."""
        level = (english_level or "A2").upper()
        return level if level in self.LEVEL_RANK else "A2"

    def _normalize_direction(self, direction: str | None) -> str:
        """Normalize and clean direction string."""
        value = (direction or "").strip().lower()
        return value if value else self.DEFAULT_DIRECTION

    def _is_level_match(self, user_level: str, min_level: str, max_level: str) -> bool:
        """Check if user level is within resource's level range."""
        rank = self.LEVEL_RANK[user_level]
        return self.LEVEL_RANK[min_level] <= rank <= self.LEVEL_RANK[max_level]

    def _filter_items(
        self,
        items: list[dict[str, Any]],
        direction: str,
        level: str,
    ) -> list[dict[str, Any]]:
        """Filter and sort resources by direction and English level."""
        directional = [item for item in items if item["direction"] == direction]
        if not directional:
            logger.debug(
                f"No resources for direction '{direction}', falling back to '{self.DEFAULT_DIRECTION}'"
            )
            directional = [
                item for item in items if item["direction"] == self.DEFAULT_DIRECTION
            ]

        matched = [
            item
            for item in directional
            if self._is_level_match(
                level,
                item["min_english_level"],
                item["max_english_level"],
            )
        ]

        return sorted(matched, key=lambda item: item.get("priority", 100))

    def get_recommendations_for_user(self, user) -> list[dict[str, Any]]:
        """Get personalized recommendations for user based on profile.
        
        Args:
            user: Django user instance with profile relation
        
        Returns:
            List of recommendation dicts sorted by priority
        
        Raises:
            ValueError: If user has no profile
        """
        profile = getattr(user, "profile", None)
        if profile is None:
            raise ValueError("Profile does not exist for the current user.")

        direction = self._normalize_direction(profile.direction)
        level = self._normalize_level(profile.english_level)

        logger.debug(
            f"Fetching recommendations for user {user.id}: direction={direction}, level={level}"
        )

        db_items = list(
            RecommendationResource.objects.filter(is_active=True).values(
                "direction",
                "min_english_level",
                "max_english_level",
                "title",
                "description",
                "url",
                "resource_type",
                "priority",
            )
        )

        source = db_items if db_items else self.DEFAULT_CATALOG
        recommendations = self._filter_items(source, direction=direction, level=level)

        logger.info(
            f"Generated {len(recommendations)} recommendations for user {user.id}"
        )
        return recommendations

