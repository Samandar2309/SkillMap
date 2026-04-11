from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from profiles.models import Profile

from .models import Choice, Question, TestAttempt, UserResponse


User = get_user_model()


class TestSystemAPITests(TestCase):
    questions_url = "/api/v1/tests/questions/"
    submit_url = "/api/v1/tests/submit/"

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

    def _set_onboarded(self, user, value: bool) -> None:
        profile = Profile.objects.get(user=user)
        profile.is_onboarded = value
        profile.save(update_fields=["is_onboarded", "updated_at"])

    def test_not_onboarded_user_gets_403_for_questions_and_submit(self):
        user = self._create_user("not-onboarded@example.com")
        self._set_onboarded(user, False)

        client = APIClient()
        client.force_authenticate(user=user)

        questions_response = client.get(self.questions_url)
        self.assertEqual(questions_response.status_code, status.HTTP_403_FORBIDDEN)

        submit_response = client.post(self.submit_url, {"answers": []}, format="json")
        self.assertEqual(submit_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_onboarded_user_can_fetch_questions_and_submit_with_correct_score(self):
        user = self._create_user("onboarded@example.com")
        self._set_onboarded(user, True)

        question_1 = Question.objects.create(text="2 + 2 = ?", skill_category="Math")
        question_2 = Question.objects.create(text="Binary of 2?", skill_category="Logic")

        choice_1_bad = Choice.objects.create(question=question_1, text="3", points=0)
        choice_1_good = Choice.objects.create(question=question_1, text="4", points=5)
        choice_2_bad = Choice.objects.create(question=question_2, text="11", points=0)
        choice_2_good = Choice.objects.create(question=question_2, text="10", points=7)

        client = APIClient()
        client.force_authenticate(user=user)

        questions_response = client.get(self.questions_url)
        self.assertEqual(questions_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(questions_response.data), 2)

        returned_choices = {
            key
            for item in questions_response.data
            for key in item["choices"][0].keys()
        }
        self.assertNotIn("points", returned_choices)

        payload = {
            "answers": [
                {"question_id": question_1.id, "choice_id": choice_1_good.id},
                {"question_id": question_2.id, "choice_id": choice_2_good.id},
            ]
        }
        submit_response = client.post(self.submit_url, payload, format="json")

        self.assertEqual(submit_response.status_code, status.HTTP_201_CREATED)
        self.assertIn("attempt_id", submit_response.data)
        self.assertEqual(submit_response.data["total_score"], 12)

        attempt = TestAttempt.objects.get(id=submit_response.data["attempt_id"])
        self.assertEqual(attempt.user, user)
        self.assertEqual(attempt.total_score, 12)

        responses = UserResponse.objects.filter(attempt=attempt)
        self.assertEqual(responses.count(), 2)
        self.assertTrue(
            responses.filter(question=question_1, selected_choice=choice_1_good).exists()
        )
        self.assertTrue(
            responses.filter(question=question_2, selected_choice=choice_2_good).exists()
        )

        self.assertTrue(choice_1_bad.points == 0 and choice_2_bad.points == 0)
