"""Celery tasks for progress monitoring and motivational reminders."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import Prefetch
from django.utils import timezone

from .models import StudyTimeLog

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True)
def check_inactive_users_and_send_emails(self) -> dict[str, int]:
    """Send motivational emails to users inactive for more than 2 days."""

    today = timezone.localdate()
    inactivity_cutoff = today - timedelta(days=2)

    checked_users = 0
    emailed_users = 0
    errors = 0

    users = (
        User.objects.filter(is_active=True)
        .select_related("progress")
        .prefetch_related(
            Prefetch(
                "study_time_logs",
                queryset=StudyTimeLog.objects.only("user_id", "date").order_by("-date"),
            )
        )
    )

    for user in users:
        checked_users += 1

        study_logs = list(user.study_time_logs.all())
        last_study_log_date = study_logs[0].date if study_logs else None

        try:
            progress = user.progress
            last_progress_activity = progress.last_activity_date
        except ObjectDoesNotExist:
            last_progress_activity = None

        activity_dates: list[date] = [
            value
            for value in (last_study_log_date, last_progress_activity)
            if isinstance(value, date)
        ]

        last_activity_date = max(activity_dates) if activity_dates else None
        is_inactive = (
            last_activity_date is None or last_activity_date <= inactivity_cutoff
        )

        if not is_inactive or not user.email:
            continue

        subject = "SkillMap - Motivational Reminder"
        message = "Bugun boshlash uchun eng yaxshi kun! Siz 2 kun orqadasiz."
        html_message = (
            "<p><strong>Bugun boshlash uchun eng yaxshi kun!</strong> "
            "Siz 2 kun orqadasiz.</p>"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@skillmap.local"),
                recipient_list=[user.email],
                fail_silently=False,
                html_message=html_message,
            )
            emailed_users += 1
            logger.info("Motivational email sent to user %s", user.id)
        except SMTPException as exc:
            errors += 1
            logger.warning("SMTP error while emailing user %s: %s", user.id, exc)
        except Exception as exc:  # pragma: no cover
            errors += 1
            logger.exception("Unexpected email error for user %s: %s", user.id, exc)

    return {
        "checked_users": checked_users,
        "emailed_users": emailed_users,
        "errors": errors,
    }

