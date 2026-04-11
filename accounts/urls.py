from django.urls import path

from .views import LoginView, RegisterView, UserProfileView, VerifyEmailView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="accounts-register"),
    path("login/", LoginView.as_view(), name="accounts-login"),
    path("verify-email/", VerifyEmailView.as_view(), name="accounts-verify-email"),
    path("me/", UserProfileView.as_view(), name="accounts-me"),
]

