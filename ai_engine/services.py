from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from test_system.models import TestAttempt

from .exceptions import InvalidJSONOutputError
from .llm_providers import GeminiProvider
from .serializers import GeneratedRoadmapSerializer


User = get_user_model()


class RoadmapGeneratorService:
    """Service layer for generating validated career roadmaps via LLM."""

    def build_prompt(self, user: User) -> str:
        profile = getattr(user, "profile", None)
        if profile is None:
            raise ValueError("Profile does not exist for the current user.")

        latest_attempt = (
            TestAttempt.objects.filter(user=user)
            .order_by("-created_at")
            .only("total_score")
            .first()
        )
        if latest_attempt is None:
            raise ValueError("No test attempt found for the current user.")

        current_goal = profile.current_goal or "Not provided"
        english_level = profile.english_level or "Not provided"
        total_score = latest_attempt.total_score

        return (
            "You are an IT Career Coach. Generate a practical learning roadmap.\n"
            "Return ONLY JSON. No markdown, no explanation text.\n\n"
            f"User context:\n"
            f"- Goal: {current_goal}\n"
            f"- English level: {english_level}\n"
            f"- Aptitude total score: {total_score}\n\n"
            "Required JSON schema:\n"
            "{\n"
            "  \"roadmap_title\": \"string\",\n"
            "  \"summary\": \"string\",\n"
            "  \"phases\": [\n"
            "    {\n"
            "      \"title\": \"string\",\n"
            "      \"objective\": \"string\",\n"
            "      \"duration_weeks\": 1,\n"
            "      \"tasks\": [\n"
            "        {\n"
            "          \"title\": \"string\",\n"
            "          \"description\": \"string\",\n"
            "          \"estimated_days\": 1\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Constraints:\n"
            "- phases must contain at least 3 items\n"
            "- each phase must contain at least 3 tasks\n"
            "- keep tasks concrete and outcome-oriented\n"
        )

    def generate_for_user(self, user: User) -> dict[str, Any]:
        prompt = self.build_prompt(user)
        provider = GeminiProvider()
        raw_output = provider.generate_json(prompt)

        serializer = GeneratedRoadmapSerializer(data=raw_output)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as exc:
            raise InvalidJSONOutputError(f"LLM output schema validation failed: {exc}") from exc

        return dict(serializer.validated_data)

