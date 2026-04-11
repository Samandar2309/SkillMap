"""URL routing for recommendations app."""

from django.urls import path

from .views import MyRecommendationsView

urlpatterns = [
    path("my/", MyRecommendationsView.as_view(), name="recommendations-my"),
]

