from django.urls import path

from .views import OnboardingView, ProfileDetailView


urlpatterns = [
    path("me/", ProfileDetailView.as_view(), name="profile-detail"),
    path("onboard/", OnboardingView.as_view(), name="profile-onboard"),
]
