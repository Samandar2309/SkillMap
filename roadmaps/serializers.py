from __future__ import annotations

from rest_framework import serializers

from .models import Phase, Roadmap, Task


class TaskSerializer(serializers.ModelSerializer):
    """Bitta dars/topshiriq ma'lumotlarini qaytaruvchi serializer."""

    class Meta:
        model = Task
        # Pro Tip: fields = "__all__" yozish xavfsizlik va aniqlik jihatidan yomon amaliyot.
        # Har doim maydonlarni aniq ko'rsatish kerak.
        fields = (
            "id",
            "day_number",
            "title",
            "description",
            "resource_link",
            "extra_resources",
            "is_completed",
            "completed_at"
        )
        read_only_fields = ("is_completed", "completed_at")


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Faqat topshiriqni 'bajarildi' holatiga o'tkazish uchun ishlatiladi."""

    is_completed = serializers.BooleanField(
        label="Bajarildimi",
        help_text="Topshiriqni bajarildi (True) deb belgilash.",
    )

    class Meta:
        model = Task
        fields = ("id", "is_completed")
        read_only_fields = ("id",)


class PhaseSerializer(serializers.ModelSerializer):
    """Roadmap ichidagi bosqichlar (modullar) va ularning darslari."""

    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Phase
        fields = ("id", "title", "order", "is_completed", "tasks")


class RoadmapListSerializer(serializers.ModelSerializer):
    """
    PRO TIP: Ro'yxat (List) uchun yengillashtirilgan serializer.
    Foydalanuvchi o'z rejalarini ko'rganda minglab tasklarni bittada yuklab
    serverni qotirmasligi uchun faqat asosiy ma'lumotlar qaytariladi.
    """
    # Modeldagi @property bo'lgan progress_percentage ni API ga chiqarish
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Roadmap
        fields = (
            "id",
            "title",
            "estimated_months",
            "is_active",
            "is_completed",
            "progress_percentage",  # Qo'shildi (9-bosqich uchun)
            "created_at",
        )


class RoadmapDetailSerializer(serializers.ModelSerializer):
    """
    Rejaning ichiga kirganda (Detail) barcha bosqich va darslarni qaytaradi.
    """
    phases = PhaseSerializer(many=True, read_only=True)
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Roadmap
        fields = (
            "id",
            "title",
            "estimated_months",
            "is_active",
            "is_completed",
            "progress_percentage",
            "created_at",
            "phases",  # Barcha darslar shu yerda keladi
        )


class RoadmapErrorSerializer(serializers.Serializer):
    """API xatoliklari uchun standartlashtirilgan javob."""

    detail = serializers.CharField(label="Izoh", help_text="Tushunarli xatolik matni.")
    code = serializers.CharField(
        required=False,
        allow_blank=True,
        label="Xatolik kodi",
        help_text="Tizim uchun maxsus xato kodi (masalan: roadmap_not_found).",
    )