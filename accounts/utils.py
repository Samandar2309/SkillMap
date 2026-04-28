from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def _get_frontend_url() -> str:
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    frontend_url = str(frontend_url).strip().rstrip("/")
    if not frontend_url:
        frontend_url = "http://localhost:3000"
    return frontend_url


def build_verification_link(user, request=None):
    """Build verification link for frontend verify page with UUID token."""
    from apps.users.models import EmailVerification

    verification = EmailVerification.create_for_user(user)
    token = str(verification.token)
    frontend_url = _get_frontend_url()
    return f"{frontend_url}/verify-email?token={token}"


def send_verification_email(user=None, request=None, **kwargs):
    """Send verification email with a frontend verification link.

    Supports both:
    - send_verification_email(user=user_obj)
    - send_verification_email(email=email_str, token=token_str, is_resend=True)
    """
    if user is None and "email" in kwargs and "token" in kwargs:
        email = kwargs["email"]
        token = kwargs["token"]
        is_resend = kwargs.get("is_resend", False)
        verification_link = f"{_get_frontend_url()}/verify-email?token={token}"
    else:
        if user is None:
            raise ValueError("Either 'user' or 'email' and 'token' parameters required")
        email = user.email
        is_resend = kwargs.get("is_resend", False)
        verification_link = build_verification_link(user, request)

    subject = "SkillMap AI - Email manzilni tasdiqlash"
    if is_resend:
        subject = "SkillMap AI - Tasdiqlash havolasi qayta yuborildi"

    html_message = f"""<!DOCTYPE html>
<html lang=\"uz\">
<head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Email tasdiqlash</title>
</head>
<body style=\"margin:0;padding:0;background:#f4f7fb;font-family:Arial,sans-serif;color:#0f172a;\">
    <table role=\"presentation\" width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"padding:24px 12px;\">
        <tr>
            <td align=\"center\">
                <table role=\"presentation\" width=\"560\" cellspacing=\"0\" cellpadding=\"0\" style=\"max-width:560px;width:100%;background:#ffffff;border-radius:14px;border:1px solid #e2e8f0;overflow:hidden;\">
                    <tr>
                        <td style=\"padding:28px 28px 8px 28px;\">
                            <h1 style=\"margin:0;font-size:24px;line-height:1.3;\">Email manzilni tasdiqlang</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style=\"padding:0 28px 8px 28px;font-size:15px;line-height:1.7;color:#334155;\">
                            SkillMap AI hisobingizni faollashtirish uchun quyidagi tugmani bosing.
                        </td>
                    </tr>
                    <tr>
                        <td align=\"center\" style=\"padding:20px 28px;\">
                            <a href=\"{verification_link}\" style=\"display:inline-block;padding:12px 22px;background:#0ea5e9;color:#ffffff;text-decoration:none;border-radius:10px;font-weight:600;font-size:16px;\">Emailni tasdiqlash</a>
                        </td>
                    </tr>
                    <tr>
                        <td style=\"padding:0 28px 10px 28px;font-size:14px;line-height:1.6;color:#475569;\">
                            Havola 24 soat davomida amal qiladi.
                        </td>
                    </tr>
                    <tr>
                        <td style=\"padding:0 28px 20px 28px;font-size:13px;line-height:1.6;color:#64748b;word-break:break-all;\">
                            Agar tugma ishlamasa, quyidagi havolani brauzerga qo'ying:<br/>
                            <a href=\"{verification_link}\" style=\"color:#0284c7;text-decoration:none;\">{verification_link}</a>
                        </td>
                    </tr>
                    <tr>
                        <td style=\"padding:0 28px 24px 28px;font-size:12px;line-height:1.6;color:#94a3b8;border-top:1px solid #f1f5f9;\">
                            Agar bu so'rov sizga tegishli bo'lmasa, xatni e'tiborsiz qoldiring.
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    text_message = (
        "SkillMap AI hisobingizni faollashtirish uchun quyidagi havolani bosing:\n\n"
        f"{verification_link}\n\n"
        "Agar bu so'rov sizga tegishli bo'lmasa, xatni e'tiborsiz qoldiring."
    )

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@skillmap.local"),
        to=[email],
    )
    message.attach_alternative(html_message, "text/html")
    message.send(fail_silently=False)
