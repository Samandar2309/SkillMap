from __future__ import annotations

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import Profile
from test_system.models import TestAttempt

from .exceptions import LLMTimeoutError


User = get_user_model()


class GenerateRoadmapAPITests(TestCase):
    """Tests for roadmap generation endpoint with mocked Gemini calls."""

    url = "/api/v1/ai/generate/"

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

    def _prepare_user_context(self, email: str) -> User:
        user = self._create_user(email)
        profile = Profile.objects.get(user=user)
        profile.current_goal = "Become a backend engineer"
        profile.english_level = "B1"
        profile.save(update_fields=["current_goal", "english_level", "updated_at"])
        TestAttempt.objects.create(user=user, total_score=72)
        return user

    @patch("ai_engine.services.GeminiProvider.generate_json")
    def test_generate_roadmap_success(self, mock_generate_json):
        mock_generate_json.return_value = {
            "roadmap_title": "Backend Engineer Path",
            "summary": "A practical 3-phase backend roadmap.",
            "phases": [
                {
                    "title": "Fundamentals",
                    "objective": "Build strong Python and web basics.",
                    "duration_weeks": 4,
                    "tasks": [
                        {
                            "title": "Python Syntax",
                            "description": "Practice core language features.",
                            "estimated_days": 4,
                        },
                        {
                            "title": "HTTP Basics",
                            "description": "Learn request/response lifecycle.",
                            "estimated_days": 3,
                        },
                        {
                            "title": "Git Workflow",
                            "description": "Use branching and pull requests.",
                            "estimated_days": 2,
                        },
                    ],
                },
                {
                    "title": "Django Core",
                    "objective": "Build secure REST APIs.",
                    "duration_weeks": 5,
                    "tasks": [
                        {
                            "title": "Models",
                            "description": "Design normalized schemas.",
                            "estimated_days": 4,
                        },
                        {
                            "title": "DRF",
                            "description": "Implement serializers and views.",
                            "estimated_days": 4,
                        },
                        {
                            "title": "JWT",
                            "description": "Add token-based auth.",
                            "estimated_days": 3,
                        },
                    ],
                },
                {
                    "title": "Production",
                    "objective": "Prepare deployable backend services.",
                    "duration_weeks": 4,
                    "tasks": [
                        {
                            "title": "Testing",
                            "description": "Write robust API tests.",
                            "estimated_days": 3,
                        },
                        {
                            "title": "CI/CD",
                            "description": "Automate checks and deployment.",
                            "estimated_days": 3,
                        },
                        {
                            "title": "Monitoring",
                            "description": "Add logs and alerts.",
                            "estimated_days": 2,
                        },
                    ],
                },
            ],
        }

        user = self._prepare_user_context("ai-success@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["roadmap_title"], "Backend Engineer Path")
        self.assertEqual(len(response.data["phases"]), 3)

    @patch("ai_engine.services.GeminiProvider.generate_json")
    def test_generate_roadmap_timeout_returns_502(self, mock_generate_json):
        mock_generate_json.side_effect = LLMTimeoutError("Gemini request timed out.")

        user = self._prepare_user_context("ai-timeout@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("detail", response.data)

    @patch("ai_engine.services.GeminiProvider.generate_json")
    def test_generate_roadmap_invalid_json_returns_400(self, mock_generate_json):
        mock_generate_json.return_value = {"unexpected": "schema"}

        user = self._prepare_user_context("ai-invalid@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_generate_roadmap_async_returns_task_id(self):
        """Test async generation endpoint returns task_id not result."""
        user = self._prepare_user_context("ai-async@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("task_id", response.data)
        self.assertEqual(response.data["status"], "queued")

    def test_generate_roadmap_requires_authentication(self):
        """Test endpoint requires authentication."""
        client = APIClient()
        response = client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_generate_roadmap_without_test_attempt_returns_400(self):
        """Test missing aptitude attempt is rejected before Celery execution."""
        user = self._create_user("ai-no-attempt@example.com")
        profile = Profile.objects.get(user=user)
        profile.current_goal = "Become a backend engineer"
        profile.english_level = "B1"
        profile.save(update_fields=["current_goal", "english_level", "updated_at"])

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)


class RoadmapTaskStatusAPITests(TestCase):
    status_url = "/api/v1/ai/tasks/{task_id}/"

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

    def test_status_with_invalid_task_id_returns_400(self):
        user = self._create_user("status-invalid@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(self.status_url.format(task_id="1"))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    @patch("ai_engine.views.AsyncResult", side_effect=ModuleNotFoundError("No module named 'redis'"))
    def test_status_backend_unavailable_returns_503(self, _mock_async_result):
        user = self._create_user("status-backend@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        task_id = "11111111-1111-1111-1111-111111111111"
        response = client.get(self.status_url.format(task_id=task_id))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("detail", response.data)


