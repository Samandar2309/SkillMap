from django.contrib import admin

from .models import Choice, Question, TestAttempt, UserResponse


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "skill_category", "is_active")
    search_fields = ("text", "skill_category")
    list_filter = ("is_active", "skill_category")
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "text", "points")
    search_fields = ("text",)
    list_filter = ("question__skill_category",)


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "total_score", "created_at")
    search_fields = ("user__email",)
    list_filter = ("created_at",)


@admin.register(UserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt", "question", "selected_choice")
    list_filter = ("question__skill_category",)
