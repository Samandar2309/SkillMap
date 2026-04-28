from django.contrib import admin

from .models import (
    Category,
    Direction,
    Goal,
    StudentProfile,
    Choice,
    Question,
    TestAttempt,
    UserResponse,
)


# ==========================================
# 1. ONBOARDING MODELLARI (Admin)
# ==========================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category")
    search_fields = ("name", "category__name")
    list_filter = ("category",)
    # N+1 muammosini oldini olish uchun
    list_select_related = ("category",)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name",)
    # Admin paneldan maqsad nomini yozganda, slug avtomatik to'ldiriladi
    prepopulated_fields = {"slug": ("name",)}


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "direction",
        "goal",
        "get_skill_level",
        "hours_per_day",
        "is_onboarding_completed"
    )
    list_filter = (
        "is_onboarding_completed",
        "skill_level",
        "english_level",
        "category",
    )
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at",)
    list_select_related = ("user", "category", "direction", "goal")

    # Katta databazalarda userlarni qidirish qotib qolmasligi uchun
    raw_id_fields = ("user",)

    # Admin paneldagi formani chiroyli bloklarga bo'lish (Pro yondashuv)
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("user", "is_onboarding_completed", "created_at")
        }),
        ("Tanlangan yo'nalish va maqsad", {
            "fields": ("category", "direction", "goal")
        }),
        ("Daraja va imkoniyatlar", {
            "fields": ("skill_level", "english_level", "hours_per_day")
        }),
    )

    @admin.display(description="Bilim darajasi")
    def get_skill_level(self, obj):
        return obj.get_skill_level_display()


# ==========================================
# 2. TEST VA DARAJA ANIQLASH (Admin)
# ==========================================

class ChoiceInline(admin.TabularInline):
    """Savolning ichida javob variantlarini bittada qo'shish uchun"""
    model = Choice
    extra = 4  # Odatda 4 ta variant bo'ladi (A, B, C, D)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "text_short", "skill_category", "is_active")
    search_fields = ("text", "skill_category")
    list_filter = ("is_active", "skill_category")
    list_editable = ("is_active",)  # Ro'yxatdan turib savolni yoqib/o'chirish imkoniyati
    inlines = [ChoiceInline]

    @admin.display(description="Savol matni")
    def text_short(self, obj):
        # Savol juda uzun bo'lsa, ro'yxatda qisqartirib ko'rsatish
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text


class UserResponseInline(admin.TabularInline):
    """
    Pro Tip: TestAttempt ichiga kirganda, foydalanuvchi aynan qaysi
    savolga qaysi variantni belgilaganini bitta sahifada ko'rish uchun.
    """
    model = UserResponse
    extra = 0
    readonly_fields = ("question", "selected_choice")
    can_delete = False  # Javoblarni adminga o'chirishga ruxsat bermaslik

    def has_add_permission(self, request, obj=None):
        return False  # Admin test javobini qo'lda qo'sha olmasligi kerak


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_score", "created_at")
    search_fields = ("user__email", "user__username")
    list_filter = ("created_at",)
    readonly_fields = ("user", "total_score", "created_at")
    list_select_related = ("user",)
    inlines = [UserResponseInline]  # Test ichiga javoblarni ulaymiz


@admin.register(UserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt", "question_short", "selected_choice")
    list_filter = ("question__skill_category",)
    search_fields = ("attempt__user__email", "question__text")
    list_select_related = ("attempt", "question", "selected_choice", "attempt__user")

    @admin.display(description="Savol")
    def question_short(self, obj):
        return f"Urunish #{obj.attempt_id} | {obj.question.text[:30]}..."