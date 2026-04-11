# Accounts App - SkillMap AI

A production-ready authentication and user management module built with Django REST Framework.

---

## Overview

The `accounts` app provides a secure and scalable authentication system using JWT and email-based identity. It is designed as the core user service for the SkillMap AI platform.

---

## Key Features

- Custom `User` model extending `AbstractUser`
- Email-based authentication (`USERNAME_FIELD = "email"`)
- Secure JWT authentication using SimpleJWT
- User registration and login endpoints
- Email verification system (token-based)
- Login restricted for unverified users
- Authenticated user profile endpoint (`/me/`)
- Automatic profile placeholder creation via Django signals
- Clean, modular architecture for production projects

---

## Authentication Flow

1. User registers via `/register/`
2. System sends a verification link (console email backend in local setup)
3. User verifies email via `/verify-email/`
4. Only verified users can log in
5. JWT tokens are issued on successful login

---

## API Endpoints

| Method   | Endpoint                         | Description              |
| -------- | -------------------------------- | ------------------------ |
| POST     | `/api/v1/accounts/register/`     | Register new user        |
| POST     | `/api/v1/accounts/login/`        | Login and get JWT tokens |
| GET/POST | `/api/v1/accounts/verify-email/` | Verify email             |
| GET      | `/api/v1/accounts/me/`           | Get current user info    |

---

## Installation and Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Run server:

```bash
python manage.py runserver
```

---

## Testing

Run tests:

```bash
python manage.py test accounts
```

---

## Email Configuration

Local development uses Django console email backend:

```python
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

All verification links are printed in terminal output.

---

## Important Settings

Custom user model:

```python
AUTH_USER_MODEL = "accounts.User"
```

JWT configuration used in this project:

```python
from datetime import timedelta

SIMPLE_JWT = {
	"ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
	"REFRESH_TOKEN_LIFETIME": timedelta(days=7),
	"ROTATE_REFRESH_TOKENS": False,
	"BLACKLIST_AFTER_ROTATION": False,
	"AUTH_HEADER_TYPES": ("Bearer",),
}
```

---

## Security Considerations

- Passwords are hashed with Django's secure hashing system
- JWT tokens are used for stateless API authentication
- Email verification is required before login
- Serializer-level validation enforces email and password rules

---

## Project Structure

```text
accounts/
|- models.py
|- managers.py
|- serializers.py
|- views.py
|- urls.py
|- utils.py
|- signals.py
|- tests.py
```

---

## Future Improvements

- Refresh token rotation
- Rate limiting (register/login)
- SMTP provider integration (SendGrid, SES, etc.)
- Password reset and account recovery
- Social authentication (Google, GitHub)

---

## Author

SkillMap AI Backend System

