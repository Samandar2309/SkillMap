from __future__ import annotations

from django.apps import apps
from rest_framework.permissions import BasePermission


class IsOnboarded(BasePermission):
    """Allows access only to authenticated users who finished onboarding."""

    message = "Complete onboarding before accessing the test system."

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        profile_model = apps.get_model("profiles", "Profile")
        return profile_model.objects.filter(user=user, is_onboarded=True).exists()

