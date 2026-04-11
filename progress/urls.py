from django.urls import path

from .views import LeaderboardView, LogStudyTimeView, MyDashboardStatsView


urlpatterns = [
    path("my-stats/", MyDashboardStatsView.as_view(), name="progress-my-stats"),
    path("leaderboard/", LeaderboardView.as_view(), name="progress-leaderboard"),
    path("log-time/", LogStudyTimeView.as_view(), name="progress-log-time"),
]
