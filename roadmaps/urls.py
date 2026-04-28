from django.urls import path

from .views import (
    ActiveRoadmapView,
    RoadmapHistoryListView,
    TaskUpdateView,
)

# app_name = "roadmaps" # Agar loyihada bir nechta app bo'lsa, buni yoqib qo'yish yaxshi amaliyot

urlpatterns = [
    # ==========================================
    # 1. ROADMAP (YO'L XARITASI) ENDPOINTLARI
    # ==========================================

    # Foydalanuvchining ayni paytdagi faol (is_active=True) rejasini olish
    path("me/", ActiveRoadmapView.as_view(), name="roadmap-me"),

    # Foydalanuvchining barcha rejalari tarixini (arxivni ham) olish
    path("history/", RoadmapHistoryListView.as_view(), name="roadmap-history"),

    # ==========================================
    # 2. TASK (TOPSHIRIQ) ENDPOINTLARI
    # ==========================================

    # Darsni "Bajarildi" (is_completed=True/False) holatiga o'tkazish
    path("tasks/<int:pk>/", TaskUpdateView.as_view(), name="roadmap-task-update"),
]