from __future__ import annotations

from rest_framework import serializers

from .models import (
    Category,
    Direction,
    Goal,
    StudentProfile,
    Choice,
    Question,
)


# ==========================================
# 1. ONBOARDING UCHUN SERIALIZERLAR (Yangi)
# ==========================================

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")


class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = ("id", "name", "category")


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ("id", "name", "slug")


class StudentProfileOnboardingSerializer(serializers.ModelSerializer):
    """Foydalanuvchini ro'yxatdan o'tgandan so'ng ma'lumotlarini yig'ish uchun"""

    class Meta:
        model = StudentProfile
        fields = (
            "category",
            "direction",
            "goal",
            "skill_level",
            "english_level",
            "hours_per_day"
        )

    def validate(self, attrs):
        # Agar yo'nalish tanlangan bo'lsa, u tanlangan kategoriyaga tegishli ekanligini tekshirish
        category = attrs.get('category')
        direction = attrs.get('direction')

        if direction and category and direction.category != category:
            raise serializers.ValidationError({
                "direction": "Tanlangan yo'nalish ushbu kategoriyaga tegishli emas."
            })
        return attrs


# ==========================================
# 2. TEST VA DARAJA ANIQLASH SERIALIZERLARI (Sizniki - O'zbekchalashtirilgan)
# ==========================================

class ChoiceSerializer(serializers.ModelSerializer):
    """Javob variantlari (ballar yashirilgan holda)"""

    text = serializers.CharField(label="Javob matni", help_text="Foydalanuvchiga ko'rinadigan javob varianti.")

    class Meta:
        model = Choice
        fields = ("id", "text")


class QuestionSerializer(serializers.ModelSerializer):
    """Test savollari va uning variantlari"""

    choices = ChoiceSerializer(many=True, read_only=True)
    text = serializers.CharField(label="Savol matni", help_text="Foydalanuvchiga ko'rsatiladigan savol.")
    skill_category = serializers.CharField(
        label="Qobiliyat turi",
        help_text="Savollarni mavzular bo'yicha guruhlash uchun (masalan: Python, REST API).",
    )

    class Meta:
        model = Question
        fields = ("id", "text", "skill_category", "choices")


class AnswerItemSerializer(serializers.Serializer):
    """Bitta savolga berilgan javob strukturasini tekshirish"""

    question_id = serializers.IntegerField(
        min_value=1,
        label="Savol ID",
        help_text="Javob berilayotgan savolning ID raqami.",
    )
    choice_id = serializers.IntegerField(
        min_value=1,
        label="Javob ID",
        help_text="Tanlangan javob variantining ID raqami.",
    )


class TestSubmitSerializer(serializers.Serializer):
    """Test yakunlanganda yuboriladigan javoblarni qabul qilish va tekshirish"""

    answers = AnswerItemSerializer(
        many=True,
        write_only=True,
        label="Javoblar",
        help_text="Foydalanuvchi tomonidan belgilangan javoblar ro'yxati.",
    )

    def validate_answers(self, value: list[dict[str, int]]) -> list[dict[str, object]]:
        if not value:
            raise serializers.ValidationError("Kamida bitta javob kiritilishi shart.")

        question_ids = [item["question_id"] for item in value]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("Bitta savolga faqat bir marta javob berish mumkin.")

        active_questions = Question.objects.filter(id__in=question_ids, is_active=True)
        questions_map = {question.id: question for question in active_questions}
        if len(questions_map) != len(question_ids):
            raise serializers.ValidationError("Savollardan biri noto'g'ri yoki faol emas.")

        choice_ids = [item["choice_id"] for item in value]
        choices_map = {
            choice.id: choice
            for choice in Choice.objects.filter(id__in=choice_ids).select_related("question")
        }
        if len(choices_map) != len(choice_ids):
            raise serializers.ValidationError("Tanlangan javoblardan biri noto'g'ri.")

        validated_answers = []
        for item in value:
            question = questions_map[item["question_id"]]
            choice = choices_map[item["choice_id"]]

            if choice.question_id != question.id:
                raise serializers.ValidationError(
                    "Tanlangan variant ushbu savolga tegishli emas."
                )
            validated_answers.append({"question": question, "choice": choice})

        return validated_answers


class TestSubmitResponseSerializer(serializers.Serializer):
    """Test muvaffaqiyatli topshirilgach qaytariladigan javob"""

    attempt_id = serializers.IntegerField(label="Urunish ID", help_text="Yaratilgan test urunishining ID raqami.")
    total_score = serializers.IntegerField(label="Umumiy ball",
                                           help_text="To'g'ri javoblar uchun hisoblangan umumiy ball.")