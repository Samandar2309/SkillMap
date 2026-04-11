"""Custom user model for email-only authentication."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Custom user model with email as unique identifier.
    
    Removes username field to enforce email-only authentication.
    Inherits password, is_active, is_staff, is_superuser from AbstractUser.
    """

    username = None
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email
