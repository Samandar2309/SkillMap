from __future__ import annotations

from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from roadmaps.models import Task

from .models import UserProgress
from .services import GamificationService


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_progress(sender, instance, created, **kwargs):
    """Ensure every newly registered user has a progress record."""

    if not created:
        return

    UserProgress.objects.get_or_create(user=instance)


@receiver(pre_save, sender=Task)
def capture_previous_task_completion_state(sender, instance, **kwargs):
    """Capture previous completion state to detect False -> True transitions."""

    if not instance.pk:
        instance._previous_is_completed = False
        return

    TaskModel = apps.get_model("roadmaps", "Task")
    instance._previous_is_completed = (
        TaskModel._default_manager.filter(pk=instance.pk).values_list("is_completed", flat=True).first()
    )


@receiver(post_save, sender=Task)
def award_points_on_task_completion(sender, instance, created, **kwargs):
    """Award points and update streak when a task becomes completed."""

    if created:
        return

    previous_value = getattr(instance, "_previous_is_completed", False)
    changed_to_completed = (not previous_value) and bool(instance.is_completed)

    if not changed_to_completed:
        return

    user = instance.phase.roadmap.user
    GamificationService().record_task_completion(user)

