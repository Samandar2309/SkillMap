"""API views for personalized recommendations."""

from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .serializers import RecommendationListResponseSerializer, RecommendationItemSerializer
from .services import RecommendationService

logger = logging.getLogger(__name__)


class MyRecommendationsView(APIView):
    """Retrieve personalized recommendations for authenticated user.
    
    Filters available learning resources based on user's direction
    and English language level from their profile.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: RecommendationListResponseSerializer})
    def get(self, request) -> Response:
        """Get personalized recommendations.
        
        Returns:
            200 OK with count and results list
            400 Bad Request if user profile missing
        """
        service = RecommendationService()

        try:
            recommendations = service.get_recommendations_for_user(request.user)
        except ValueError as exc:
            logger.warning(f"Profile missing for user {request.user.id}: {exc}")
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = RecommendationItemSerializer(recommendations, many=True).data
        logger.info(f"Returned {len(data)} recommendations to user {request.user.id}")

        return Response(
            {
                "count": len(data),
                "results": data,
            },
            status=status.HTTP_200_OK,
        )


