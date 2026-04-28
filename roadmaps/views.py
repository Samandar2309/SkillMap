from __future__ import annotations

from django.db import transaction
from rest_framework import status
from rest_framework.generics import UpdateAPIView, ListAPIView
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Roadmap, Task
from .serializers import (
    RoadmapErrorSerializer,
    RoadmapDetailSerializer,
    RoadmapListSerializer,
    TaskSerializer,
    TaskUpdateSerializer
)


# ==========================================
# 1. FAOL REJANI KO'RISH (Hozir o'qiyotgan rejasi)
# ==========================================
@extend_schema_view(
    get=extend_schema(responses={200: RoadmapDetailSerializer, 404: RoadmapErrorSerializer}),
)
class ActiveRoadmapView(APIView):
    """
    Foydalanuvchining hozirgi faol (is_active=True) yo'l xaritasini
    barcha bosqich va darslari bilan birga qaytaradi.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        # Custom Manager (get_active_with_details) orqali N+1 muammosiz
        # bitta qatorda hamma ma'lumotni optimallashtirib tortib kelamiz
        roadmap = Roadmap.objects.get_active_with_details(user=request.user)

        if not roadmap:
            return Response(
                {
                    "detail": "Sizda hozircha faol o'quv rejasi yo'q. Onboardingni yakunlang.",
                    "code": "ROADMAP_MISSING"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(RoadmapDetailSerializer(roadmap).data, status=status.HTTP_200_OK)


# ==========================================
# 2. REJALAR TARIXI (Yangi qo'shildi)
# ==========================================
@extend_schema_view(
    get=extend_schema(responses={200: RoadmapListSerializer(many=True)}),
)
class RoadmapHistoryListView(ListAPIView):
    """Foydalanuvchining barcha (jumladan arxivlangan) rejalari ro'yxati."""
    permission_classes = [IsAuthenticated]
    serializer_class = RoadmapListSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Roadmap.objects.none()

        return (
            Roadmap.objects.annotate_progress()
            .filter(user=self.request.user)
            .order_by('-created_at')
        )


# ==========================================
# 3. DARS/TOPSHIRIQNI BAJARILDI DEB BELGILASH
# ==========================================
@extend_schema_view(
    patch=extend_schema(request=TaskUpdateSerializer, responses={200: TaskSerializer, 404: RoadmapErrorSerializer}),
)
class TaskUpdateView(UpdateAPIView):
    """
    Foydalanuvchiga faqat o'ziga tegishli darslarni 'bajarildi'
    (is_completed=True/False) holatiga o'tkazish imkonini beradi.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaskUpdateSerializer
    http_method_names = ["patch"]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        with transaction.atomic():
            try:
                # select_for_update() - bir vaqtda 2 ta so'rov kelib qolsa, bazani qulflaydi
                instance = self.get_queryset().select_for_update().get(pk=kwargs["pk"])
            except Task.DoesNotExist as exc:
                raise NotFound({"detail": "Topshiriq topilmadi.", "code": "TASK_NOT_FOUND"}) from exc

            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)

            # Yangi qiymatni saqlashdan oldin olamiz
            is_completed_new = serializer.validated_data.get('is_completed', instance.is_completed)

            # Custom Logic: Agar rost bo'lsa modeldagi mark_as_done() ni chaqiramiz
            if is_completed_new and not instance.is_completed:
                instance.mark_as_done()
            # Agar foydalanuvchi "bajarildi" pichkasini olib tashlasa, vaqtni ham tozalaymiz
            elif not is_completed_new and instance.is_completed:
                instance.is_completed = False
                instance.completed_at = None
                instance.save(update_fields=['is_completed', 'completed_at'])

        # Qaytayotganda TaskSerializer orqali to'liq ma'lumotni (shu jumladan vaqtni ham) qaytaramiz
        return Response(TaskSerializer(instance).data, status=status.HTTP_200_OK)

    def get_queryset(self):
        # Swagger generatsiyasida xatolik chiqmasligi uchun
        if getattr(self, 'swagger_fake_view', False):
            return Task.objects.none()

        # Foydalanuvchi faqat o'ziga tegishli (boshqasining emas) topshiriqni o'zgartira oladi
        return Task.objects.select_related("phase__roadmap").filter(phase__roadmap__user=self.request.user)