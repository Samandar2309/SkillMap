from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import Question, TestAttempt, UserResponse
from .permissions import IsOnboarded
from .serializers import QuestionSerializer, TestSubmitResponseSerializer, TestSubmitSerializer


class QuestionListView(ListAPIView):
    """Returns all active aptitude questions with their choices."""

    permission_classes = [IsAuthenticated, IsOnboarded]
    serializer_class = QuestionSerializer

    @extend_schema(responses={200: QuestionSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Question.objects.filter(is_active=True).prefetch_related("choices")


class SubmitTestView(APIView):
    """Creates a test attempt and stores selected answers in one transaction."""

    permission_classes = [IsAuthenticated, IsOnboarded]

    @extend_schema(request=TestSubmitSerializer, responses={201: TestSubmitResponseSerializer})
    def post(self, request) -> Response:
        serializer = TestSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers = serializer.validated_data["answers"]

        with transaction.atomic():
            attempt = TestAttempt.objects.create(user=request.user)

            responses = []
            total_score = 0
            for answer in answers:
                question = answer["question"]
                choice = answer["choice"]
                responses.append(
                    UserResponse(
                        attempt=attempt,
                        question=question,
                        selected_choice=choice,
                    )
                )
                total_score += choice.points

            UserResponse.objects.bulk_create(responses)
            attempt.total_score = total_score
            attempt.save(update_fields=["total_score"])

        return Response(
            {"attempt_id": attempt.id, "total_score": attempt.total_score},
            status=status.HTTP_201_CREATED,
        )

