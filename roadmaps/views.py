from __future__ import annotations

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Roadmap, Task
from .serializers import RoadmapErrorSerializer, RoadmapSerializer, TaskSerializer, TaskUpdateSerializer


@extend_schema_view(
    get=extend_schema(responses={200: RoadmapSerializer, 404: RoadmapErrorSerializer}),
)
class MyRoadmapView(APIView):
	"""Returns the current user's roadmap with nested phases and tasks."""

	permission_classes = [IsAuthenticated]

	def get(self, request) -> Response:
		try:
			roadmap = self.get_object()
		except (Roadmap.DoesNotExist, ObjectDoesNotExist):
			return Response(
				{"detail": "Roadmap not generated yet.", "code": "ROADMAP_MISSING"},
				status=status.HTTP_404_NOT_FOUND,
			)

		return Response(RoadmapSerializer(roadmap).data, status=status.HTTP_200_OK)

	def get_queryset(self):
		if getattr(self, "swagger_fake_view", False):
			return Roadmap.objects.none()
		return Roadmap.objects.prefetch_related("phases__tasks")

	def get_object(self):
		if getattr(self, "swagger_fake_view", False):
			return Roadmap()
		return self.get_queryset().get(user=self.request.user)

@extend_schema_view(
    patch=extend_schema(request=TaskUpdateSerializer, responses={200: TaskSerializer, 404: RoadmapErrorSerializer}),
)
class TaskUpdateView(UpdateAPIView):
	"""Allows users to patch completion state of their own roadmap tasks."""

	permission_classes = [IsAuthenticated]
	serializer_class = TaskUpdateSerializer
	http_method_names = ["patch"]

	def patch(self, request, *args, **kwargs):
		return super().patch(request, *args, **kwargs)

	def update(self, request, *args, **kwargs):
		partial = kwargs.pop("partial", False)
		with transaction.atomic():
			try:
				instance = self.get_queryset().select_for_update().get(pk=kwargs["pk"])
			except Task.DoesNotExist as exc:
				raise NotFound("Task not found.") from exc
			serializer = self.get_serializer(instance, data=request.data, partial=partial)
			serializer.is_valid(raise_exception=True)
			self.perform_update(serializer)

		return Response(TaskSerializer(serializer.instance).data, status=status.HTTP_200_OK)

	def get_queryset(self):
		# Handle Swagger schema generation with AnonymousUser
		if getattr(self, 'swagger_fake_view', False):
			return Task.objects.none()
		
		return Task.objects.select_related("phase__roadmap").filter(phase__roadmap__user=self.request.user)
