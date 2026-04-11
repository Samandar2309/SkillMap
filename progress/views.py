from __future__ import annotations

from django.db.models import Count, Q
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from roadmaps.models import Task

from .models import UserProgress
from .serializers import (
    DashboardStatsSerializer,
    LeaderboardEntrySerializer,
    StudyTimeLogSerializer,
    UserProgressSerializer,
)


class MyDashboardStatsView(APIView):
    """Returns user gamification counters and roadmap completion analytics."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: DashboardStatsSerializer})
    def get(self, request) -> Response:
        progress, _ = UserProgress.objects.get_or_create(user=request.user)

        roadmap = getattr(request.user, "roadmap", None)
        if roadmap is None:
            completed_tasks_count = 0
            total_tasks_count = 0
        else:
            aggregate = Task.objects.filter(phase__roadmap=roadmap).aggregate(
                total_tasks_count=Count("id"),
                completed_tasks_count=Count("id", filter=Q(is_completed=True)),
            )
            completed_tasks_count = aggregate["completed_tasks_count"] or 0
            total_tasks_count = aggregate["total_tasks_count"] or 0

        completion_percentage = 0.0
        if total_tasks_count > 0:
            completion_percentage = round((completed_tasks_count / total_tasks_count) * 100, 2)

        payload = {
            "progress": UserProgressSerializer(progress).data,
            "roadmap_completion_percentage": completion_percentage,
            "completed_tasks_count": completed_tasks_count,
            "total_tasks_count": total_tasks_count,
        }
        serializer = DashboardStatsSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LeaderboardView(ListAPIView):
    """Returns top users ranked by gamification points."""

    permission_classes = [IsAuthenticated]
    serializer_class = LeaderboardEntrySerializer

    @extend_schema(responses={200: LeaderboardEntrySerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return (
            UserProgress.objects.select_related("user")
            .only("user__email", "total_points", "current_streak")
            .order_by("-total_points", "-current_streak", "user__email")[:10]
        )


class LogStudyTimeView(APIView):
    """Create or update today's study-time log for the authenticated user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=StudyTimeLogSerializer, responses={201: StudyTimeLogSerializer})
    def post(self, request) -> Response:
        serializer = StudyTimeLogSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        return Response(
            StudyTimeLogSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )
