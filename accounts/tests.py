from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class CustomUserManagerTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def _build_user_kwargs(self, email="user@example.com", username="testuser"):
        """Build kwargs that work with both username-based and username-less user models."""

        kwargs = {"email": email}
        try:
            self.User._meta.get_field("username")
        except FieldDoesNotExist:
            return kwargs

        kwargs["username"] = username
        return kwargs


class UserManagerTests(CustomUserManagerTests):
    def test_create_user_successfully_creates_user_with_default_flags(self):
        password = "StrongPassword123!"
        user = self.User.objects.create_user(
            password=password,
            **self._build_user_kwargs(email="newuser@example.com"),
        )

        self.assertIsNotNone(user.pk)
        self.assertEqual(user.email, "newuser@example.com")
        self.assertFalse(getattr(user, "is_verified"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(password))

    def test_create_user_raises_value_error_without_email(self):
        with self.assertRaisesMessage(ValueError, "The email field must be set."):
            self.User.objects.create_user(email=None, password="StrongPassword123!")

    def test_create_superuser_successfully_creates_user_with_admin_flags(self):
        password = "StrongPassword123!"
        user = self.User.objects.create_superuser(
            password=password,
            **self._build_user_kwargs(email="admin@example.com", username="adminuser"),
        )

        self.assertIsNotNone(user.pk)
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertTrue(getattr(user, "is_verified"))
        self.assertTrue(user.check_password(password))

    def test_create_superuser_raises_value_error_when_is_staff_is_false(self):
        with self.assertRaisesMessage(ValueError, "Superuser must have is_staff=True."):
            self.User.objects.create_superuser(
                password="StrongPassword123!",
                is_staff=False,
                **self._build_user_kwargs(email="badstaff@example.com", username="badstaff"),
            )

    def test_create_superuser_raises_value_error_when_is_superuser_is_false(self):
        with self.assertRaisesMessage(ValueError, "Superuser must have is_superuser=True."):
            self.User.objects.create_superuser(
                password="StrongPassword123!",
                is_superuser=False,
                **self._build_user_kwargs(email="badsuper@example.com", username="badsuper"),
            )


class UserModelTests(CustomUserManagerTests):
    def test_str_returns_email(self):
        user = self.User.objects.create_user(
            password="StrongPassword123!",
            **self._build_user_kwargs(email="string@example.com", username="stringuser"),
        )

        self.assertEqual(str(user), user.email)


class UserAdminTests(CustomUserManagerTests):
    def test_admin_change_page_loads_for_custom_user(self):
        admin_user = self.User.objects.create_superuser(
            password="StrongPassword123!",
            **self._build_user_kwargs(email="admin-test@example.com", username="admintest"),
        )
        target_user = self.User.objects.create_user(
            password="StrongPassword123!",
            **self._build_user_kwargs(email="target@example.com", username="target"),
        )

        self.client.force_login(admin_user)

        url = reverse("admin:accounts_user_change", args=[target_user.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


class LoginAPITests(CustomUserManagerTests):
    login_url = "/api/v1/accounts/login/"

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_verified_user_can_login(self):
        user = self.User.objects.create_user(
            password="StrongPassword123!",
            is_verified=True,
            **self._build_user_kwargs(email="verified@example.com", username="verified"),
        )

        response = self.client.post(
            self.login_url,
            {"email": user.email, "password": "StrongPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_unverified_user_gets_401_with_clear_message(self):
        user = self.User.objects.create_user(
            password="StrongPassword123!",
            is_verified=False,
            **self._build_user_kwargs(email="unverified@example.com", username="unverified"),
        )

        response = self.client.post(
            self.login_url,
            {"email": user.email, "password": "StrongPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

