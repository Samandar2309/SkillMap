from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Profile


User = get_user_model()


class ProfilesAPITests(TestCase):
    """Unit tests for profiles model signal and onboarding API."""

    def _create_user(
        self,
        email: str,
        password: str = "StrongPassword123!",
        username: str = "user",
    ):
        kwargs = {"email": email, "password": password}
        try:
            User._meta.get_field("username")
        except FieldDoesNotExist:
            return User.objects.create_user(**kwargs)

        kwargs["username"] = username
        return User.objects.create_user(**kwargs)

    def test_post_save_signal_creates_profile_for_new_user(self):
        user = self._create_user("profile@example.com")

        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.user, user)
        self.assertEqual(profile.direction, "")
        self.assertEqual(profile.english_level, "")
        self.assertEqual(profile.current_goal, "")
        self.assertFalse(profile.is_onboarded)

    def test_onboarding_requires_authentication(self):
        client = APIClient()
        response = client.patch(
            "/api/v1/profiles/onboard/",
            {
                "direction": "Backend Engineering",
                "english_level": "B1",
                "current_goal": "Build production APIs",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_onboarding_updates_existing_profile_and_sets_is_onboarded_true(self):
        user = self._create_user("onboard@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.patch(
            "/api/v1/profiles/onboard/",
            {
                "direction": "Backend Engineering",
                "english_level": "B2",
                "current_goal": "Ship a secure API platform",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)

        profile = Profile.objects.get(user=user)
        self.assertTrue(profile.is_onboarded)
        self.assertEqual(profile.direction, "Backend Engineering")
        self.assertEqual(profile.english_level, "B2")
        self.assertEqual(profile.current_goal, "Ship a secure API platform")

    def test_profile_detail_returns_authenticated_users_profile(self):
        user = self._create_user("detail@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/profiles/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], user.pk)
        self.assertFalse(response.data["is_onboarded"])
        self.assertEqual(response.data["direction"], "")
        self.assertEqual(response.data["english_level"], "")
        self.assertEqual(response.data["current_goal"], "")
