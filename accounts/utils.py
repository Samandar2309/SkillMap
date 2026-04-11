from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def build_verification_link(user, request=None):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("accounts-verify-email")

    if request is not None:
        base_url = request.build_absolute_uri(path)
    else:
        base_url = f"{getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:8000')}{path}"

    return f"{base_url}?uid={uid}&token={token}"


def send_verification_email(user, request=None):
    verification_link = build_verification_link(user, request=request)
    subject = "Verify your SkillMap AI account"
    message = (
        "Thanks for registering on SkillMap AI. "
        "Use the link below to verify your email:\n\n"
        f"{verification_link}\n\n"
        "If you did not create this account, please ignore this email."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@skillmap.local"),
        recipient_list=[user.email],
        fail_silently=False,
    )

