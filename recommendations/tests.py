"""Unit and integration tests for recommendations app."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from profiles.models import Profile

from .models import RecommendationResource
from .services import RecommendationService

User = get_user_model()


class RecommendationServiceFilteringTests(TestCase):
    """Tests for recommendation filtering by direction and English level."""

    def setUp(self):
        self.service = RecommendationService()

    def _create_user(self, direction: str = "backend", level: str = "B1") -> User:
        """Create user with profile."""
        user = User.objects.create_user(
            email=f"test-{direction}-{level}@example.com",
            password="TestPass123!",
        )
        profile = Profile.objects.get(user=user)
        profile.direction = direction
        profile.english_level = level
        profile.save()
        return user

    def test_filter_by_exact_direction(self):
        """Test recommendations filtered by exact direction match."""
        user = self._create_user(direction="backend")
        recommendations = self.service.get_recommendations_for_user(user)

        self.assertGreater(len(recommendations), 0)
        for rec in recommendations:
            self.assertIn(rec["direction"], ("backend", "general"))

    def test_filter_by_english_level_range(self):
        """Test recommendations respect English level boundaries."""
        user = self._create_user(direction="backend", level="A2")
        recommendations = self.service.get_recommendations_for_user(user)

        for rec in recommendations:
            min_rank = self.service.LEVEL_RANK[rec["min_english_level"]]
            max_rank = self.service.LEVEL_RANK[rec["max_english_level"]]
            user_rank = self.service.LEVEL_RANK["A2"]
            self.assertTrue(min_rank <= user_rank <= max_rank)

    def test_filter_fallback_to_general_direction(self):
        """Test fallback to 'general' when direction not found."""
        user = self._create_user(direction="exotic_niche_direction")
        recommendations = self.service.get_recommendations_for_user(user)

        self.assertGreater(len(recommendations), 0)
        for rec in recommendations:
            self.assertIn(rec["direction"], ("general",))

    def test_sorting_by_priority(self):
        """Test recommendations sorted by priority (lower first)."""
        user = self._create_user()
        recommendations = self.service.get_recommendations_for_user(user)

        for i in range(len(recommendations) - 1):
            self.assertLessEqual(
                recommendations[i]["priority"],
                recommendations[i + 1]["priority"],
            )


    def test_normalize_level_defaults_to_a2(self):
        """Test invalid English level defaults to A2."""
        normalized = self.service._normalize_level("INVALID")
        self.assertEqual(normalized, "A2")

    def test_normalize_level_case_insensitive(self):
        """Test level normalization is case-insensitive."""
        normalized = self.service._normalize_level("b1")
        self.assertEqual(normalized, "B1")

    def test_normalize_direction_handles_whitespace(self):
        """Test direction normalization strips whitespace."""
        normalized = self.service._normalize_direction("  backend  ")
        self.assertEqual(normalized, "backend")

    def test_uses_db_resources_if_available(self):
        """Test that database resources are used when available."""
        user = self._create_user(direction="general")

        RecommendationResource.objects.create(
            direction="general",
            title="Custom DB Resource",
            url="https://example.com",
            min_english_level="A1",
            max_english_level="C2",
            priority=1,
            is_active=True,
        )

        recommendations = self.service.get_recommendations_for_user(user)
        titles = [rec["title"] for rec in recommendations]
        self.assertGreater(len(titles), 0)
        self.assertIn("Custom DB Resource", titles)
        self.assertIn("Custom DB Resource", titles)

    def test_inactive_resources_excluded(self):
        """Test that inactive resources are excluded."""
        user = self._create_user(direction="backend")

        RecommendationResource.objects.create(
            direction="backend",
            title="Inactive Resource",
            url="https://example.com",
            min_english_level="A1",
            max_english_level="C2",
            priority=50,
            is_active=False,
        )

        recommendations = self.service.get_recommendations_for_user(user)

        titles = [rec["title"] for rec in recommendations]
        self.assertNotIn("Inactive Resource", titles)

    def test_high_level_user_gets_advanced_resources(self):
        """Test C2 user gets advanced recommendations."""
        user = self._create_user(direction="backend", level="C2")
        recommendations = self.service.get_recommendations_for_user(user)

        for rec in recommendations:
            max_rank = self.service.LEVEL_RANK[rec["max_english_level"]]
            c2_rank = self.service.LEVEL_RANK["C2"]
            self.assertGreaterEqual(max_rank, c2_rank)

    def test_low_level_user_limited_options(self):
        """Test A1 user has limited but suitable options."""
        user = self._create_user(direction="backend", level="A1")
        recommendations = self.service.get_recommendations_for_user(user)

        self.assertGreater(len(recommendations), 0)
        for rec in recommendations:
            min_rank = self.service.LEVEL_RANK[rec["min_english_level"]]
            self.assertEqual(min_rank, 1)


class RecommendationsViewTests(TestCase):
    """API tests for recommendations endpoint."""

    endpoint = "/api/v1/recommendations/my/"

    def setUp(self):
        self.client = APIClient()

    def _create_authenticated_user(self) -> tuple[User, str]:
        """Create verified user with profile and return access token."""
        user = User.objects.create_user(
            email="api@example.com",
            password="TestPass123!",
        )
        user.is_verified = True
        user.save()

        profile = Profile.objects.get(user=user)
        profile.direction = "backend"
        profile.english_level = "B1"
        profile.save()

        refresh = RefreshToken.for_user(user)
        return user, str(refresh.access_token)

    def test_get_recommendations_authenticated(self):
        """Test authenticated access to recommendations endpoint."""
        user, token = self._create_authenticated_user()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)

    def test_get_recommendations_unauthenticated(self):
        """Test unauthenticated access returns 401."""
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_recommendations_match_user_profile(self):
        """Test recommendations are personalized by profile."""
        user, token = self._create_authenticated_user()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for rec in response.data["results"]:
            self.assertIn(rec["direction"], ("backend", "general"))

    def test_response_has_required_fields(self):
        """Test each recommendation has all required fields."""
        user, token = self._create_authenticated_user()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(self.endpoint)

        required_fields = {
            "direction",
            "min_english_level",
            "max_english_level",
            "title",
            "description",
            "url",
            "resource_type",
            "priority",
        }

        for rec in response.data["results"]:
            self.assertTrue(required_fields.issubset(rec.keys()))

    def test_missing_profile_returns_400(self):
        """Test missing profile returns 400 Bad Request."""
        user = User.objects.create_user(
            email="noprofile@example.com",
            password="TestPass123!",
        )
        user.is_verified = True
        user.save()
        Profile.objects.filter(user=user).delete()

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        response = self.client.get(self.endpoint)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

