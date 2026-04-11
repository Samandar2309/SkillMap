from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import UserProgress


User = get_user_model()


class GamificationService:
    """Encapsulates point and streak updates for completed roadmap tasks."""

    POINTS_PER_TASK = 10

    @transaction.atomic
    def record_task_completion(self, user: User) -> UserProgress:
        progress, _ = UserProgress.objects.select_for_update().get_or_create(user=user)

        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        progress.total_points += self.POINTS_PER_TASK

        if progress.last_activity_date == today:
            pass
        elif progress.last_activity_date == yesterday:
            progress.current_streak += 1
        else:
            progress.current_streak = 1

        if progress.current_streak > progress.longest_streak:
            progress.longest_streak = progress.current_streak

        progress.last_activity_date = today
        progress.save(
            update_fields=[
                "total_points",
                "current_streak",
                "longest_streak",
                "last_activity_date",
            ]
        )
        return progress

