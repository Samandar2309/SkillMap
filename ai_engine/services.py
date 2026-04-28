from __future__ import annotations

from typing import Any, cast

from django.contrib.auth import get_user_model
from rest_framework import serializers

from test_system.models import StudentProfile

from .exceptions import InvalidJSONOutputError
from .providers import GroqProvider, create_groq_provider
from .serializers import GeneratedRoadmapSerializer


User = get_user_model()


class RoadmapGeneratorService:
    """Service layer for generating validated career roadmaps via LLM."""

    def build_prompt(self, user: User) -> str:
        profile = (
            StudentProfile.objects.only("goal__name", "english_level", "hours_per_day")
            .select_related("goal")
            .filter(user=user)
            .first()
        )
        if profile is None:
            raise ValueError("Student profile does not exist for the current user.")

        current_goal = profile.goal.name if profile.goal_id else "Not provided"
        english_level = profile.english_level or "Not provided"
        hours_per_day = profile.hours_per_day or 2

        return (
            "You are a senior IT career coach. Generate a practical learning roadmap.\n"
            "Return ONLY valid JSON. No markdown, no commentary, no code fences.\n\n"
            "User context:\n"
            f"- Goal: {current_goal}\n"
            f"- English level: {english_level}\n"
            f"- Study hours per day: {hours_per_day}\n\n"
            "JSON schema:\n"
            "{\n"
            '  "title": "string",\n'
            '  "estimated_months": 1,\n'
            '  "phases": [\n'
            "    {\n"
            '      "title": "string",\n'
            '      "objective": "string",\n'
            '      "duration_weeks": 1,\n'
            '      "tasks": [\n'
            "        {\n"
            '          "title": "string",\n'
            '          "description": "string",\n'
            '          "estimated_days": 1\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "Constraints:\n"
            "- phases must contain at least 3 items\n"
            "- each phase must contain at least 3 tasks\n"
            "- keep tasks concrete, measurable, and outcome-oriented\n"
        )

    def generate_roadmap(self, user: User) -> dict[str, Any]:
        prompt = self.build_prompt(user)
        provider = create_groq_provider()
        result = provider.generate_json(prompt)
        raw_output = result.data

        serializer = GeneratedRoadmapSerializer(data=raw_output)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as exc:
            raise InvalidJSONOutputError(f"LLM output schema validation failed: {exc}") from exc

        return cast(dict[str, Any], dict(serializer.validated_data))

    def generate_for_user(self, user: User) -> dict[str, Any]:
        return self.generate_roadmap(user)

