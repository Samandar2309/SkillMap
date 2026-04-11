from django.urls import path

from .views import GenerateRoadmapAPIView, RoadmapTaskStatusAPIView


urlpatterns = [
    path("generate/", GenerateRoadmapAPIView.as_view(), name="ai-generate-roadmap"),
    path("tasks/<str:task_id>/", RoadmapTaskStatusAPIView.as_view(), name="ai-roadmap-task-status"),
]

