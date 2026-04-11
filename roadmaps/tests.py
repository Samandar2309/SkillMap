from __future__ import annotations

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Phase, Roadmap, Task
from .services import RoadmapBuilderService


User = get_user_model()


class RoadmapBuilderServiceTests(TestCase):
	"""Tests for bulk roadmap persistence and replacement semantics."""

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

		kwargs["username"] = username if username != "user" else email.split("@")[0]
		return User.objects.create_user(**kwargs)

	def _sample_json(self, title: str = "Backend Roadmap") -> dict:
		return {
			"title": title,
			"estimated_months": 6,
			"phases": [
				{
					"title": "Core Foundations",
					"order": 1,
					"tasks": [
						{"title": "Python Basics", "description": "Syntax and control flow"},
						{"title": "HTTP Concepts", "description": "Methods and status codes"},
					],
				},
				{
					"title": "Django REST",
					"order": 2,
					"tasks": [
						{"title": "Models", "description": "Design entities"},
						{"title": "APIView", "description": "Build secure endpoints"},
					],
				},
			],
		}

	def test_builder_uses_bulk_create_and_replaces_old_roadmap(self):
		user = self._create_user("roadmap-builder@example.com")
		service = RoadmapBuilderService()

		first = service.build_from_json(user, self._sample_json("First"))
		self.assertEqual(Roadmap.objects.filter(user=user).count(), 1)

		with patch.object(Phase.objects, "bulk_create", wraps=Phase.objects.bulk_create) as phase_bulk:
			with patch.object(Task.objects, "bulk_create", wraps=Task.objects.bulk_create) as task_bulk:
				second = service.build_from_json(user, self._sample_json("Second"))

		phase_bulk.assert_called_once()
		task_bulk.assert_called_once()

		self.assertEqual(Roadmap.objects.filter(user=user).count(), 1)
		self.assertNotEqual(first.id, second.id)
		self.assertEqual(second.title, "Second")
		self.assertEqual(Phase.objects.filter(roadmap=second).count(), 2)
		self.assertEqual(Task.objects.filter(phase__roadmap=second).count(), 4)
		self.assertFalse(Roadmap.objects.filter(id=first.id).exists())


class RoadmapViewsTests(TestCase):
	"""API tests for roadmap retrieval behavior, performance and task update security."""

	roadmap_url = "/api/v1/roadmaps/me/"

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

		kwargs["username"] = username if username != "user" else email.split("@")[0]
		return User.objects.create_user(**kwargs)

	def _build_roadmap(self, user) -> Roadmap:
		service = RoadmapBuilderService()
		return service.build_from_json(
			user,
			{
				"title": "Production Backend Plan",
				"estimated_months": 5,
				"phases": [
					{
						"title": "Phase One",
						"order": 1,
						"tasks": [
							{"title": "Task A", "description": "Do A"},
							{"title": "Task B", "description": "Do B"},
						],
					},
					{
						"title": "Phase Two",
						"order": 2,
						"tasks": [
							{"title": "Task C", "description": "Do C"},
							{"title": "Task D", "description": "Do D"},
						],
					},
				],
			},
		)

	def test_my_roadmap_missing_fallback(self):
		user = self._create_user("missing-roadmap@example.com")
		client = APIClient()
		client.force_authenticate(user=user)

		response = client.get(self.roadmap_url)

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertEqual(response.data["detail"], "Roadmap not generated yet.")
		self.assertEqual(response.data["code"], "ROADMAP_MISSING")

	def test_my_roadmap_fetch_is_prefetch_optimized(self):
		user = self._create_user("prefetch@example.com")
		self._build_roadmap(user)

		client = APIClient()
		client.force_authenticate(user=user)

		with self.assertNumQueries(3):
			response = client.get(self.roadmap_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data["phases"]), 2)

	def test_user_cannot_patch_other_users_task(self):
		user_a = self._create_user("user-a@example.com")
		user_b = self._create_user("user-b@example.com")
		roadmap_b = self._build_roadmap(user_b)
		foreign_task = Task.objects.filter(phase__roadmap=roadmap_b).first()
		self.assertIsNotNone(foreign_task)

		client = APIClient()
		client.force_authenticate(user=user_a)

		response = client.patch(
			f"/api/v1/roadmaps/tasks/{foreign_task.id}/",
			{"is_completed": True},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		foreign_task.refresh_from_db()
		self.assertFalse(foreign_task.is_completed)


class RoadmapBuilderSchemaMappingTests(TestCase):
	"""Tests for schema mapping with multiple key variations."""

	def setUp(self):
		self.service = RoadmapBuilderService()
		self.User = get_user_model()

	def _create_user(self, email: str = "schema@example.com"):
		kwargs = {"email": email, "password": "TestPass123!"}
		try:
			self.User._meta.get_field("username")
		except FieldDoesNotExist:
			return self.User.objects.create_user(**kwargs)
		kwargs["username"] = email.split("@")[0]
		return self.User.objects.create_user(**kwargs)

	def test_maps_roadmap_title_key(self):
		"""Test mapping of roadmap title from various key names."""
		user = self._create_user("title1@example.com")
		json_data = {
			"roadmap_title": "Custom Backend Path",
			"estimated_months": 6,
			"phases": [
				{
					"title": "Phase 1",
					"order": 1,
					"tasks": [{"title": "Task 1"}],
				}
			],
		}

		roadmap = self.service.build_from_json(user, json_data)
		self.assertEqual(roadmap.title, "Custom Backend Path")

	def test_fallback_to_title_key(self):
		"""Test fallback to 'title' key if roadmap_title missing."""
		user = self._create_user("title2@example.com")
		json_data = {
			"title": "Fallback Title",
			"estimated_months": 3,
			"phases": [
				{
					"title": "Phase 1",
					"order": 1,
					"tasks": [{"title": "Task 1"}],
				}
			],
		}

		roadmap = self.service.build_from_json(user, json_data)
		self.assertEqual(roadmap.title, "Fallback Title")

	def test_default_title_if_missing(self):
		"""Test default title if no title key found."""
		user = self._create_user("title3@example.com")
		json_data = {
			"estimated_months": 3,
			"phases": [
				{
					"title": "Phase 1",
					"order": 1,
					"tasks": [{"title": "Task 1"}],
				}
			],
		}

		roadmap = self.service.build_from_json(user, json_data)
		self.assertEqual(roadmap.title, "Personalized Learning Roadmap")

	def test_maps_phase_title_variations(self):
		"""Test phase title mapping from various keys."""
		user = self._create_user("phase1@example.com")
		json_data = {
			"title": "Test",
			"estimated_months": 3,
			"phases": [
				{
					"phase_title": "Frontend Basics",
					"order": 1,
					"tasks": [{"title": "Task 1"}],
				}
			],
		}

		roadmap = self.service.build_from_json(user, json_data)
		phase = roadmap.phases.first()
		self.assertEqual(phase.title, "Frontend Basics")

	def test_maps_task_description_variations(self):
		"""Test task description mapping from various keys."""
		user = self._create_user("desc1@example.com")
		json_data = {
			"title": "Test",
			"estimated_months": 3,
			"phases": [
				{
					"title": "Phase 1",
					"order": 1,
					"tasks": [
						{
							"title": "Task 1",
							"details": "Learn the basics",
						}
					],
				}
			],
		}

		roadmap = self.service.build_from_json(user, json_data)
		task = roadmap.phases.first().tasks.first()
		self.assertEqual(task.description, "Learn the basics")

	def test_maps_resource_url_variations(self):
		"""Test resource URL mapping from various keys."""
		user = self._create_user("url1@example.com")
		json_data = {
			"title": "Test",
			"estimated_months": 3,
			"phases": [
				{
					"title": "Phase 1",
					"order": 1,
					"tasks": [
						{
							"title": "Task 1",
							"resource_url": "https://example.com",
						}
					],
				}
			],
		}

		roadmap = self.service.build_from_json(user, json_data)
		task = roadmap.phases.first().tasks.first()
		self.assertEqual(task.resource_link, "https://example.com")

	def test_handles_missing_optional_fields(self):
		"""Test graceful handling of missing description and resource_link."""
		user = self._create_user("minimal@example.com")
		json_data = {
			"title": "Minimal",
			"estimated_months": 3,
			"phases": [
				{
					"title": "Phase 1",
					"order": 1,
					"tasks": [{"title": "Task 1"}],
				}
			],
		}

		roadmap = self.service.build_from_json(user, json_data)
		task = roadmap.phases.first().tasks.first()
		self.assertEqual(task.description, "")
		self.assertEqual(task.resource_link, "")

	def test_creates_default_task_if_empty(self):
		"""Test default task created if phase has no tasks."""
		user = self._create_user("empty@example.com")
		json_data = {
			"title": "Test",
			"estimated_months": 3,
			"phases": [
				{
					"title": "Empty Phase",
					"order": 1,
					"tasks": [],
				}
			],
		}

		roadmap = self.service.build_from_json(user, json_data)
		phase = roadmap.phases.first()
		task = phase.tasks.first()
		self.assertIsNotNone(task)
		self.assertEqual(task.title, "Kickoff learning plan")

	def test_rejects_non_dict_json(self):
		"""Test ValueError raised for non-dict json_data."""
		user = self._create_user("invalid@example.com")
		with self.assertRaisesMessage(ValueError, "must be a dictionary"):
			self.service.build_from_json(user, "not a dict")

