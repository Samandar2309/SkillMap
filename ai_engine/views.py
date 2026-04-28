"""API endpoints for AI-powered roadmap generation."""

from __future__ import annotations

import logging
from uuid import UUID

from celery.exceptions import CeleryError
from celery.result import AsyncResult
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .exceptions import InvalidJSONOutputError, LLMConnectionError, LLMTimeoutError
from .services import RoadmapGeneratorService
from .tasks import generate_roadmap_task
from .serializers import RoadmapTaskResponseSerializer, RoadmapTaskStatusSerializer

logger = logging.getLogger(__name__)
TASK_OWNER_CACHE_PREFIX = "ai_engine:roadmap_task_owner"
TASK_OWNER_TTL_SECONDS = 60 * 60 * 24


def _task_owner_cache_key(task_id: str) -> str:
    return f"{TASK_OWNER_CACHE_PREFIX}:{task_id}"


class GenerateRoadmapAPIView(APIView):
    """Trigger async roadmap generation for current user.
    
    Returns immediately with task_id for polling or webhook integration.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
    serializer_class = RoadmapTaskResponseSerializer

    @extend_schema(request=None, responses={202: RoadmapTaskResponseSerializer})
    def post(self, request) -> Response:
        """Queue roadmap generation task.
        
        Returns:
            202 Accepted with task_id for status polling
            503 Service Unavailable if Celery broker unreachable
        """
        try:
            RoadmapGeneratorService().build_prompt(request.user)

            async_result = generate_roadmap_task.delay(request.user.id)
            logger.info(
                "Queued roadmap generation task %s for user %s",
                async_result.id,
                request.user.id,
            )

            if not async_result.id:
                raise CeleryError("Task id was not returned by broker.")

            cache.set(
                _task_owner_cache_key(str(async_result.id)),
                request.user.id,
                timeout=TASK_OWNER_TTL_SECONDS,
            )

            return Response(
                {
                    "task_id": async_result.id,
                    "status": "queued",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except CeleryError as exc:
            logger.error("Celery broker error for user %s: %s", request.user.id, exc)
            return Response(
                {"detail": "Roadmap generation queue is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except LLMTimeoutError as exc:
            logger.warning("Groq timeout for user %s: %s", request.user.id, exc)
            return Response(
                {"detail": "Groq request timed out."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except LLMConnectionError as exc:
            logger.warning("Groq connection failure for user %s: %s", request.user.id, exc)
            return Response(
                {"detail": "Failed to connect to Groq provider."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except InvalidJSONOutputError as exc:
            logger.warning("Groq schema validation failed for user %s: %s", request.user.id, exc)
            return Response(
                {"detail": "LLM output schema validation failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as exc:
            logger.info("Roadmap generation prerequisites missing for user %s: %s", request.user.id, exc)
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Unexpected roadmap generation error for user %s", request.user.id)
            return Response(
                {"detail": "Roadmap generation failed to start."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class RoadmapTaskStatusAPIView(APIView):
    """Return Celery task state for frontend polling."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    @extend_schema(responses={200: RoadmapTaskStatusSerializer})
    def get(self, request, task_id: str) -> Response:
        try:
            UUID(str(task_id))
        except ValueError:
            return Response(
                {"detail": "Invalid task id format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            owner_user_id = cache.get(_task_owner_cache_key(task_id))
            if owner_user_id is None or int(owner_user_id) != int(request.user.id):
                return Response(
                    {"detail": "Task not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            async_result = AsyncResult(task_id)
            payload: dict[str, object] = {
                "task_id": task_id,
                "state": async_result.state,
                "status": async_result.status,
            }

            if async_result.successful():
                payload["result"] = async_result.result
            elif async_result.failed():
                payload["error"] = str(async_result.result)
            elif async_result.result is not None:
                payload["result"] = async_result.result

            return Response(payload, status=status.HTTP_200_OK)
        except (CeleryError, ImportError) as exc:
            logger.error("Task status backend unavailable for task %s: %s", task_id, exc)
            return Response(
                {"detail": "Task status backend is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


