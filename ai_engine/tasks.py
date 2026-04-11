"""Celery tasks for async roadmap generation."""

from __future__ import annotations

import logging
from typing import Any

from celery import shared_task
from django.contrib.auth import get_user_model

from roadmaps.services import RoadmapBuilderService

from .exceptions import InvalidJSONOutputError
from .services import RoadmapGeneratorService

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_roadmap_task(self, user_id: int) -> dict[str, Any]:
    """Generate roadmap asynchronously for user.
    
    Args:
        user_id: Target user ID
    
    Returns:
        Result dict with roadmap_id, title, estimated_months
    
    Raises:
        User.DoesNotExist: If user not found
        ValueError: If user profile missing
        InvalidJSONOutputError: If LLM schema validation fails
    """
    try:
        user = User.objects.select_related("profile").get(pk=user_id)
        logger.info(f"Generating roadmap for user {user_id}")

        generated_payload = RoadmapGeneratorService().generate_for_user(user)
        logger.debug(f"LLM generation successful for user {user_id}")

        roadmap = RoadmapBuilderService().build_from_json(
            user=user, json_data=generated_payload
        )
        logger.info(f"Roadmap {roadmap.id} built successfully for user {user_id}")

        return {
            "roadmap_id": roadmap.id,
            "title": roadmap.title,
            "estimated_months": roadmap.estimated_months,
        }

    except User.DoesNotExist as exc:
        logger.error(f"User {user_id} not found")
        raise

    except ValueError as exc:
        logger.error(f"ValueError for user {user_id}: {exc}")
        raise

    except InvalidJSONOutputError as exc:
        logger.error(f"LLM schema validation failed for user {user_id}: {exc}")
        raise

    except Exception as exc:
        logger.error(f"Unexpected error generating roadmap for user {user_id}: {exc}")
        raise

