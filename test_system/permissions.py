from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import BasePermission


class IsOnboarded(BasePermission):
    """
    Faqatgina ro'yxatdan o'tgan va onboarding jarayonini (1-5 bosqichlarni)
    to'liq yakunlagan foydalanuvchilarga ruxsat beruvchi klass.
    """

    message = "Tizimdan to'liq foydalanish uchun dastlab onboarding (yo'nalish va maqsadni tanlash) jarayonini yakunlashingiz kerak."

    def has_permission(self, request, view) -> bool:
        user = request.user

        # 1. Foydalanuvchi tizimga kirganligini tekshirish
        if not user or not user.is_authenticated:
            return False

        # 2. Yagona source of truth: faqat StudentProfile flagini tekshiramiz.
        try:
            return bool(user.student_profile.is_onboarding_completed)
        except ObjectDoesNotExist:
            return False
