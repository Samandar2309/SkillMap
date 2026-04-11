from django.urls import path

from .views import MyRoadmapView, TaskUpdateView


urlpatterns = [
    path("me/", MyRoadmapView.as_view(), name="roadmap-me"),
    path("tasks/<int:pk>/", TaskUpdateView.as_view(), name="roadmap-task-update"),
]

