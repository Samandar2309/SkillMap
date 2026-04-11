from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from roadmaps.services import RoadmapBuilderService

from .models import StudyTimeLog, UserProgress
from .services import GamificationService
from .tasks import check_inactive_users_and_send_emails


User = get_user_model()


class ProgressBaseTestCase(TestCase):
    def create_user(
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

    def build_simple_roadmap(self, user):
        return RoadmapBuilderService().build_from_json(
            user,
            {
                "title": "Progress Roadmap",
                "estimated_months": 4,
                "phases": [
                    {
                        "title": "Phase 1",
                        "order": 1,
                        "tasks": [
                            {"title": "Task 1", "description": "Learn basics"},
                            {"title": "Task 2", "description": "Practice"},
                        ],
                    },
                    {
                        "title": "Phase 2",
                        "order": 2,
                        "tasks": [
                            {"title": "Task 3", "description": "Build project"},
                            {"title": "Task 4", "description": "Deploy"},
                        ],
                    },
                ],
            },
        )


class GamificationServiceTests(ProgressBaseTestCase):
    def test_same_day_completion_adds_points_without_streak_change(self):
        user = self.create_user("same-day@example.com")
        progress = UserProgress.objects.get(user=user)
        today = timezone.localdate()
        progress.total_points = 20
        progress.current_streak = 3
        progress.longest_streak = 5
        progress.last_activity_date = today
        progress.save(
            update_fields=[
                "total_points",
                "current_streak",
                "longest_streak",
                "last_activity_date",
            ]
        )

        GamificationService().record_task_completion(user)
        progress.refresh_from_db()

        self.assertEqual(progress.total_points, 30)
        self.assertEqual(progress.current_streak, 3)
        self.assertEqual(progress.longest_streak, 5)
        self.assertEqual(progress.last_activity_date, today)

    def test_consecutive_day_completion_increments_streak(self):
        user = self.create_user("consecutive@example.com")
        progress = UserProgress.objects.get(user=user)
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        progress.current_streak = 2
        progress.longest_streak = 2
        progress.last_activity_date = yesterday
        progress.save(
            update_fields=["current_streak", "longest_streak", "last_activity_date"]
        )

        GamificationService().record_task_completion(user)
        progress.refresh_from_db()

        self.assertEqual(progress.total_points, 10)
        self.assertEqual(progress.current_streak, 3)
        self.assertEqual(progress.longest_streak, 3)
        self.assertEqual(progress.last_activity_date, today)

    def test_skipped_day_resets_current_streak(self):
        user = self.create_user("skip-day@example.com")
        progress = UserProgress.objects.get(user=user)
        old_day = timezone.localdate() - timedelta(days=3)
        progress.current_streak = 7
        progress.longest_streak = 7
        progress.last_activity_date = old_day
        progress.save(
            update_fields=["current_streak", "longest_streak", "last_activity_date"]
        )

        GamificationService().record_task_completion(user)
        progress.refresh_from_db()

        self.assertEqual(progress.total_points, 10)
        self.assertEqual(progress.current_streak, 1)
        self.assertEqual(progress.longest_streak, 7)


class ProgressSignalsAndViewsTests(ProgressBaseTestCase):
    dashboard_url = "/api/v1/progress/my-stats/"
    leaderboard_url = "/api/v1/progress/leaderboard/"

    def test_task_completion_signal_updates_points_once(self):
        user = self.create_user("signal-task@example.com")
        roadmap = self.build_simple_roadmap(user)
        task = roadmap.phases.first().tasks.first()

        progress = UserProgress.objects.get(user=user)
        self.assertEqual(progress.total_points, 0)

        task.is_completed = True
        task.save(update_fields=["is_completed"])
        progress.refresh_from_db()
        self.assertEqual(progress.total_points, 10)

        task.title = "Task 1 Updated"
        task.save(update_fields=["title"])
        progress.refresh_from_db()
        self.assertEqual(progress.total_points, 10)

    def test_my_dashboard_stats_completion_percentage(self):
        user = self.create_user("dashboard@example.com")
        roadmap = self.build_simple_roadmap(user)
        tasks = list(roadmap.phases.prefetch_related("tasks").first().tasks.all())
        tasks[0].is_completed = True
        tasks[0].save(update_fields=["is_completed"])

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(self.dashboard_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_tasks_count"], 4)
        self.assertEqual(response.data["completed_tasks_count"], 1)
        self.assertEqual(response.data["roadmap_completion_percentage"], 25.0)
        self.assertEqual(response.data["progress"]["total_points"], 10)

    def test_leaderboard_uses_single_query(self):
        scores = [300, 250, 200, 180, 150, 120, 100, 90, 80, 70, 60]
        users = [self.create_user(f"leader-{idx}@example.com") for idx in range(len(scores))]

        for user, score in zip(users, scores):
            progress = UserProgress.objects.get(user=user)
            progress.total_points = score
            progress.current_streak = score // 10
            progress.save(update_fields=["total_points", "current_streak"])

        client = APIClient()
        client.force_authenticate(user=users[0])

        with self.assertNumQueries(1):
            response = client.get(self.leaderboard_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)
        self.assertGreaterEqual(response.data[0]["total_points"], response.data[1]["total_points"])

    def test_concurrent_task_completion_prevents_race_condition(self):
        """Test select_for_update prevents race condition on progress update."""
        user = self.create_user("race@example.com")
        progress = UserProgress.objects.get(user=user)
        self.assertEqual(progress.total_points, 0)

        service = GamificationService()
        service.record_task_completion(user)
        service.record_task_completion(user)

        progress.refresh_from_db()
        self.assertEqual(progress.total_points, 20)
        self.assertEqual(progress.current_streak, 1)


class StudyTimeLogAPITests(ProgressBaseTestCase):
    log_time_url = "/api/v1/progress/log-time/"

    def test_log_time_creates_daily_entry_and_calculates_lag(self):
        user = self.create_user("time-log@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            self.log_time_url,
            {"planned_minutes": 120, "actual_minutes": 30},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StudyTimeLog.objects.filter(user=user).count(), 1)
        self.assertTrue(response.data["is_falling_behind"])
        self.assertEqual(response.data["deficit_minutes"], 90)


class MotivationTaskTests(ProgressBaseTestCase):
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_task_sends_email_to_inactive_users(self):
        inactive_user = self.create_user("inactive@example.com")
        active_user = self.create_user("active@example.com")

        StudyTimeLog.objects.create(
            user=inactive_user,
            date=timezone.localdate() - timedelta(days=3),
            planned_minutes=120,
            actual_minutes=0,
        )
        StudyTimeLog.objects.create(
            user=active_user,
            date=timezone.localdate(),
            planned_minutes=120,
            actual_minutes=90,
        )

        result = check_inactive_users_and_send_emails.apply(args=()).get()

        self.assertEqual(result["checked_users"], 2)
        self.assertEqual(result["emailed_users"], 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Bugun boshlash uchun eng yaxshi kun!", mail.outbox[0].body)
        self.assertIn("inactive@example.com", mail.outbox[0].to)
