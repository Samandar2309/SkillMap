from django.urls import path

from .views import QuestionListView, SubmitTestView


urlpatterns = [
    path("questions/", QuestionListView.as_view(), name="test-questions"),
    path("submit/", SubmitTestView.as_view(), name="test-submit"),
]
