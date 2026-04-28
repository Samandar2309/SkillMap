from __future__ import annotations

from django.conf import settings
from django.db import models


# ==========================================
# 1. ASOSIY YO'NALISHLAR VA MAQSADLAR (Dinamik)
# ==========================================

class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Kategoriya nomi")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "1. Kategoriyalar"

    def __str__(self):
        return self.name


class Direction(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="directions",
                                 verbose_name="Kategoriya")
    name = models.CharField(max_length=255, verbose_name="Yo'nalish nomi")

    class Meta:
        unique_together = ("category", "name")
        verbose_name = "Yo'nalish"
        verbose_name_plural = "2. Yo'nalishlar"

    def __str__(self):
        return f"{self.category.name} -> {self.name}"


class Goal(models.Model):
    """Foydalanuvchi maqsadlari (Admin paneldan qo'shiladi)"""
    name = models.CharField(max_length=255, verbose_name="Maqsad nomi", help_text="Masalan: Ish topish, Freelance")
    slug = models.SlugField(unique=True, help_text="AI ga yuborish uchun kalit so'z (masalan: job, freelance)")

    class Meta:
        verbose_name = "Maqsad"
        verbose_name_plural = "3. Maqsadlar"

    def __str__(self):
        return self.name


# ==========================================
# 2. FOYDALANUVCHI PROFILI (Onboarding)
# ==========================================

class StudentProfile(models.Model):
    """Barcha onboarding ma'lumotlarini o'zida saqlovchi markaziy model"""

    class EnglishLevel(models.TextChoices):
        A1 = "A1", "Boshlang'ich (A1)"
        A2 = "A2", "Elementar (A2)"
        B1 = "B1", "O'rta (B1)"
        B2 = "B2", "O'rta-yuqori (B2)"
        C1 = "C1", "Mukammal (C1)"

    class SkillLevel(models.TextChoices):
        BEGINNER = "beginner", "Noldan boshlayman"
        INTERMEDIATE = "intermediate", "Baza bor (Test orqali aniqlanadi)"
        ADVANCED = "advanced", "Tajribalimman"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile",
                                verbose_name="Foydalanuvchi")

    # 1, 2 va 3-bosqichlar: Yo'nalish va Maqsad (Dinamik)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 verbose_name="Tanlagan kategoriyasi")
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="Tanlagan yo'nalishi")
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Asosiy maqsadi")

    # 4 va 5-bosqichlar: Daraja, Til va Vaqt (Statik)
    skill_level = models.CharField(max_length=20, choices=SkillLevel.choices, null=True, blank=True,
                                   verbose_name="Bilim darajasi")
    english_level = models.CharField(max_length=2, choices=EnglishLevel.choices, null=True, blank=True,
                                     verbose_name="Ingliz tili darajasi")
    hours_per_day = models.PositiveIntegerField(default=2, verbose_name="Kunlik ajratadigan vaqti (soat)")

    is_onboarding_completed = models.BooleanField(default=False, verbose_name="Onboarding tugaganmi?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")

    class Meta:
        verbose_name = "Talaba profili"
        verbose_name_plural = "4. Talabalar profillari"

    def __str__(self):
        return f"{self.user} - {self.direction} ({self.get_skill_level_display()})"


# ==========================================
# 3. TEST VA DARAJA ANIQLASH (Skill Test)
# ==========================================

class Question(models.Model):
    """Foydalanuvchining bilimini tekshirish uchun savollar"""
    text = models.TextField(verbose_name="Savol matni")
    skill_category = models.CharField(max_length=100, verbose_name="Qobiliyat turi",
                                      help_text="Masalan: Python Basics, REST API")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi?")

    class Meta:
        ordering = ["id"]
        verbose_name = "Savol"
        verbose_name_plural = "5. Savollar"

    def __str__(self) -> str:
        return f"Savol #{self.pk}: {self.skill_category}"


class Choice(models.Model):
    """Savol uchun javob variantlari"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices",
                                 verbose_name="Tegishli savol")
    text = models.CharField(max_length=255, verbose_name="Javob matni")
    points = models.IntegerField(default=0, verbose_name="Beriladigan ball")

    class Meta:
        ordering = ["id"]
        verbose_name = "Javob varianti"
        verbose_name_plural = "6. Javob variantlari"

    def __str__(self) -> str:
        return f"Variant #{self.pk} (Savol #{self.question_id})"


class TestAttempt(models.Model):
    """Bitta foydalanuvchining test ishlash urunishi"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="test_attempts",
                             verbose_name="Foydalanuvchi")
    total_score = models.IntegerField(default=0, verbose_name="Umumiy ball")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Topshirilgan vaqt")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Test urunishi"
        verbose_name_plural = "7. Test urunishlari"

    def __str__(self) -> str:
        return f"Urunish #{self.pk} - {self.user} ({self.total_score} ball)"


class UserResponse(models.Model):
    """Foydalanuvchi belgilagan har bir javob"""
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name="responses",
                                verbose_name="Test urunishi")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Savol")
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, verbose_name="Tanlangan javob")

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"],
                name="unique_question_per_attempt",
            )
        ]
        verbose_name = "Foydalanuvchi javobi"
        verbose_name_plural = "8. Foydalanuvchi javoblari"

    def __str__(self) -> str:
        return f"Javob #{self.pk}: {self.question_id}-savol -> {self.selected_choice_id}-variant"