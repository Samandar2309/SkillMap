from django.urls import path

from .views import (
    CategoryListView,
    DirectionListView,
    GoalListView,
    SubmitOnboardingView,
    QuestionListView,
    SubmitTestView,
)

# app_name = "onboarding" # Agar loyihada bir nechta app bo'lsa, buni yoqib qo'yish yaxshi amaliyot

urlpatterns = [
    # ==========================================
    # 1. ONBOARDING API ENDPOINT'LARI (Yangi)
    # ==========================================
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("directions/", DirectionListView.as_view(), name="direction-list"),
    path("goals/", GoalListView.as_view(), name="goal-list"),

    # User barcha ma'lumotlarni tanlab bo'lgach, shu manzilga POST yuboradi
    path("onboarding/submit/", SubmitOnboardingView.as_view(), name="onboarding-submit"),

    # ==========================================
    # 2. TEST VA DARAJA ANIQLASH API (Sizniki)
    # ==========================================
    path("questions/", QuestionListView.as_view(), name="test-questions"),
    path("submit/", SubmitTestView.as_view(), name="test-submit"),
]