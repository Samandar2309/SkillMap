"""Roadmap generation and persistence service with schema mapping."""

from __future__ import annotations

import math
import logging
from collections.abc import Mapping
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Phase, Roadmap, Task

User = get_user_model()
logger = logging.getLogger(__name__)


class RoadmapBuilderService:
    """Builds and persists a roadmap from AI JSON with robust schema mapping.
    
    Handles multiple key naming variations from different LLM providers,
    gracefully fills missing data with sensible defaults.
    """

    # Schema keys mappings for flexibility
    ROADMAP_TITLE_KEYS = ("title", "roadmap_title", "name", "roadmap_name")
    ROADMAP_ESTIMATED_MONTH_KEYS = (
        "estimated_months",
        "estimated_duration_months",
        "duration_months",
        "total_months",
    )
    PHASES_KEYS = ("phases", "roadmap_phases", "steps", "milestones")
    PHASE_TITLE_KEYS = ("title", "phase_title", "name", "phase_name")
    PHASE_ORDER_KEYS = ("order", "phase_order", "position", "sequence")
    PHASE_TASKS_KEYS = ("tasks", "items", "activities", "lessons")
    TASK_TITLE_KEYS = ("title", "task_title", "name", "activity")
    TASK_DESCRIPTION_KEYS = ("description", "details", "objective", "what_to_learn")
    TASK_RESOURCE_KEYS = ("resource_link", "resource_url", "url", "link", "reference")

    @staticmethod
    def _get_first(
        payload: Mapping[str, Any], keys: tuple[str, ...], default: Any = None
    ) -> Any:
        """Extract first non-empty value from payload using multiple key variations."""
        for key in keys:
            value = payload.get(key)
            if value not in (None, ""):
                return value
        return default

    @staticmethod
    def _to_positive_int(value: Any, default: int) -> int:
        """Convert value to positive integer, fallback to default."""
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def _to_str(value: Any, default: str = "") -> str:
        """Convert value to non-empty string, fallback to default."""
        if value is None:
            return default
        text = str(value).strip()
        return text or default

    def _resolve_estimated_months(
        self, payload: Mapping[str, Any], phases_payload: list[Any]
    ) -> int:
        """Calculate roadmap duration from explicit value or phase durations."""
        explicit = self._get_first(payload, self.ROADMAP_ESTIMATED_MONTH_KEYS)
        if explicit is not None:
            return self._to_positive_int(explicit, default=3)

        weeks_total = 0
        for phase_data in phases_payload:
            if isinstance(phase_data, Mapping):
                weeks_total += self._to_positive_int(
                    phase_data.get("duration_weeks"), default=0
                )

        if weeks_total > 0:
            return max(1, math.ceil(weeks_total / 4))

        return 3

    def _normalize_phases(self, raw_phases: Any) -> list[dict[str, Any]]:
        """Normalize and validate phases from AI response."""
        if not isinstance(raw_phases, list):
            raw_phases = []

        normalized: list[dict[str, Any]] = []
        for index, raw_phase in enumerate(raw_phases, start=1):
            if not isinstance(raw_phase, Mapping):
                continue

            phase_title = self._to_str(
                self._get_first(raw_phase, self.PHASE_TITLE_KEYS),
                default=f"Phase {index}",
            )
            phase_order = self._to_positive_int(
                self._get_first(raw_phase, self.PHASE_ORDER_KEYS),
                default=index,
            )

            raw_tasks = self._get_first(raw_phase, self.PHASE_TASKS_KEYS, default=[])
            if not isinstance(raw_tasks, list):
                raw_tasks = []

            tasks: list[dict[str, str]] = []
            for task_index, raw_task in enumerate(raw_tasks, start=1):
                if not isinstance(raw_task, Mapping):
                    continue

                task_title = self._to_str(
                    self._get_first(raw_task, self.TASK_TITLE_KEYS),
                    default=f"Task {task_index}",
                )
                task_description = self._to_str(
                    self._get_first(raw_task, self.TASK_DESCRIPTION_KEYS),
                    default="",
                )
                task_resource = self._to_str(
                    self._get_first(raw_task, self.TASK_RESOURCE_KEYS),
                    default="",
                )

                tasks.append(
                    {
                        "title": task_title,
                        "description": task_description,
                        "resource_link": task_resource,
                    }
                )

            if not tasks:
                tasks.append(
                    {
                        "title": "Kickoff learning plan",
                        "description": "Define goals and create a study schedule for this phase.",
                        "resource_link": "",
                    }
                )

            normalized.append(
                {
                    "title": phase_title,
                    "order": phase_order,
                    "tasks": tasks,
                }
            )

        if not normalized:
            normalized = [
                {
                    "title": "Getting Started",
                    "order": 1,
                    "tasks": [
                        {
                            "title": "Set a weekly learning plan",
                            "description": "Break your goal into weekly milestones.",
                            "resource_link": "",
                        }
                    ],
                }
            ]

        return normalized

    @transaction.atomic
    def build_from_json(self, user: User, json_data: dict[str, Any]) -> Roadmap:
        """Build and persist roadmap from AI JSON with schema mapping.
        
        Args:
            user: Target user for roadmap
            json_data: Raw JSON from LLM provider (may have varying key names)
        
        Returns:
            Persisted Roadmap instance with phases and tasks
        
        Raises:
            ValueError: If json_data is not a dict
        """
        if not isinstance(json_data, Mapping):
            raise ValueError("json_data must be a dictionary.")

        # Lock the user row so concurrent roadmap generations for the same user
        # cannot delete/recreate roadmaps out of order.
        user = User.objects.select_for_update().get(pk=user.pk)

        roadmap_title = self._to_str(
            self._get_first(json_data, self.ROADMAP_TITLE_KEYS),
            default="Personalized Learning Roadmap",
        )
        phases_payload = self._get_first(json_data, self.PHASES_KEYS, default=[])
        normalized_phases = self._normalize_phases(phases_payload)
        estimated_months = self._resolve_estimated_months(json_data, normalized_phases)

        logger.info(
            f"Building roadmap for user {user.id}: title={roadmap_title}, "
            f"phases={len(normalized_phases)}, months={estimated_months}"
        )

        # Delete existing roadmap for this user
        deleted_count, _ = Roadmap.objects.filter(user=user).delete()
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} existing roadmap(s) for user {user.id}")

        # Create new roadmap
        roadmap = Roadmap.objects.create(
            user=user,
            title=roadmap_title,
            estimated_months=estimated_months,
            is_completed=False,
        )

        # Bulk create phases
        phase_instances = [
            Phase(
                roadmap=roadmap,
                title=phase_data["title"],
                order=phase_data["order"],
                is_completed=False,
            )
            for phase_data in normalized_phases
        ]
        created_phases = Phase.objects.bulk_create(phase_instances)

        if not created_phases or any(phase.pk is None for phase in created_phases):
            created_phases = list(
                Phase.objects.filter(roadmap=roadmap).order_by("order", "id")
            )

        # Bulk create tasks
        tasks_to_create: list[Task] = []
        for phase, phase_data in zip(created_phases, normalized_phases):
            for task_data in phase_data["tasks"]:
                tasks_to_create.append(
                    Task(
                        phase=phase,
                        title=task_data["title"],
                        description=task_data["description"],
                        resource_link=task_data["resource_link"],
                        is_completed=False,
                    )
                )

        if tasks_to_create:
            Task.objects.bulk_create(tasks_to_create)

        logger.info(
            f"Successfully built roadmap {roadmap.id} with "
            f"{len(created_phases)} phases and {len(tasks_to_create)} tasks"
        )

        return roadmap



