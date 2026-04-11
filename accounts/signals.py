from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_placeholder(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        profile_model = apps.get_model("profiles", "Profile")
    except LookupError:
        return

    # Keep this generic so accounts app works whether Profile is already implemented or not.
    user_relation_field = None
    for field in profile_model._meta.fields:
        if isinstance(field, models.OneToOneField) and field.related_model == sender:
            user_relation_field = field.name
            break

    if user_relation_field is None:
        return

    profile_model.objects.get_or_create(**{user_relation_field: instance})

