from __future__ import annotations

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver


User = get_user_model()


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    """Create an empty profile for every newly created user."""

    if not created:
        return

    Profile = apps.get_model("profiles", "Profile")
    Profile.objects.get_or_create(user=instance)

