from __future__ import annotations

from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Profile
from .serializers import OnboardingSerializer, ProfileSerializer


@extend_schema_view(
    get=extend_schema(responses={200: ProfileSerializer}),
    put=extend_schema(request=ProfileSerializer, responses={200: ProfileSerializer}),
    patch=extend_schema(request=ProfileSerializer, responses={200: ProfileSerializer}),
)
class ProfileDetailView(RetrieveUpdateAPIView):
    """Retrieve or update the authenticated user's profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        if getattr(self, "swagger_fake_view", False):
            return Profile()
        profile = getattr(self.request.user, "profile", None)
        if profile is None:
            raise NotFound("Profile does not exist for the current user.")
        return profile


@extend_schema_view(
    put=extend_schema(request=OnboardingSerializer, responses={200: ProfileSerializer}),
    patch=extend_schema(request=OnboardingSerializer, responses={200: ProfileSerializer}),
)
class OnboardingView(UpdateAPIView):
    """Complete onboarding for the authenticated user's existing profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = OnboardingSerializer

    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        if getattr(self, "swagger_fake_view", False):
            return Profile()
        profile = getattr(self.request.user, "profile", None)
        if profile is None:
            raise NotFound("Profile does not exist for the current user.")
        return profile

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            ProfileSerializer(serializer.instance).data,
            status=status.HTTP_200_OK,
        )
