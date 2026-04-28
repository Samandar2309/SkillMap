from __future__ import annotations

from django.db import transaction
from celery.exceptions import CeleryError
from rest_framework import status
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from ai_engine.tasks import generate_roadmap_task

from .models import Category, Direction, Goal, Question, StudentProfile, TestAttempt, UserResponse
from .permissions import IsOnboarded
from .serializers import (
    CategorySerializer,
    DirectionSerializer,
    GoalSerializer,
    StudentProfileOnboardingSerializer,
    QuestionSerializer,
    TestSubmitResponseSerializer,
    TestSubmitSerializer,
)


# ==========================================
# 1. ONBOARDING API VIEWS (Yangi qo'shildi)
# ==========================================

class CategoryListView(ListAPIView):
    """Barcha mavjud kategoriyalarni (Dasturlash, Dizayn...) qaytaradi."""
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class DirectionListView(ListAPIView):
    """Barcha yo'nalishlarni qaytaradi. URL orqali ?category=1 deb filter qilsa bo'ladi."""
    permission_classes = [IsAuthenticated]
    serializer_class = DirectionSerializer

    def get_queryset(self):
        queryset = Direction.objects.all()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class GoalListView(ListAPIView):
    """Barcha maqsadlarni (Ish topish, Freelance...) qaytaradi."""
    permission_classes = [IsAuthenticated]
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer


class SubmitOnboardingView(GenericAPIView):
    """
    Foydalanuvchining Onboarding (1-5 bosqich) ma'lumotlarini qabul qiladi
    va profilni is_onboarding_completed=True holatiga o'tkazadi.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StudentProfileOnboardingSerializer

    @extend_schema(responses={200: StudentProfileOnboardingSerializer})
    def post(self, request, *args, **kwargs) -> Response:
        with transaction.atomic():
            profile, created = StudentProfile.objects.get_or_create(user=request.user)

            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(is_onboarding_completed=True)

        try:
            async_result = generate_roadmap_task.delay(request.user.id)
            task_id = str(async_result.id) if async_result and async_result.id else None
            if task_id is None:
                raise CeleryError("Task id was not returned by Celery.")
        except CeleryError:
            return Response(
                {
                    "message": "Onboarding completed, but roadmap queue is temporarily unavailable.",
                    "task_id": None,
                    "data": serializer.data,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "message": "Onboarding muvaffaqiyatli yakunlandi!",
                "task_id": task_id,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )


# ==========================================
# 2. TEST VA DARAJA ANIQLASH API VIEWS (Siz yozgan kod)
# ==========================================

class QuestionListView(ListAPIView):
    """Barcha faol test savollarini javob variantlari bilan qaytaradi."""

    # Foydalanuvchi faqat onboardingni tugatgandan keyingina test ishlashi mumkin
    permission_classes = [IsAuthenticated, IsOnboarded]
    serializer_class = QuestionSerializer

    @extend_schema(responses={200: QuestionSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # Variantlarni bitta so'rovda olib kelish uchun prefetch_related qoldirildi
        return Question.objects.filter(is_active=True).prefetch_related("choices")


class SubmitTestView(APIView):
    """Test urunishini yaratadi va tanlangan javoblarni bitta tranzaksiyada saqlaydi."""

    permission_classes = [IsAuthenticated, IsOnboarded]

    @extend_schema(request=TestSubmitSerializer, responses={201: TestSubmitResponseSerializer})
    def post(self, request) -> Response:
        serializer = TestSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers = serializer.validated_data["answers"]

        # Tranzaksiya: agar kodning o'rtasida xatolik chiqsa, bazaga chala ma'lumot yozilmaydi
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

            # Barcha javoblarni bitta so'rov (query) orqali bazaga saqlash
            UserResponse.objects.bulk_create(responses)

            attempt.total_score = total_score
            attempt.save(update_fields=["total_score"])

            # Qo'shimcha mantiq: Agar xohlasangiz, shu yerda total_score ga qarab
            # foydalanuvchining StudentProfile modelidagi skill_level maydonini
            # (Beginner, Intermediate) avtomatik o'zgartirib qo'yishimiz mumkin.

        return Response(
            {"attempt_id": attempt.id, "total_score": attempt.total_score},
            status=status.HTTP_201_CREATED,
        )