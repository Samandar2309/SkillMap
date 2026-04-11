from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/v1/accounts/", include("accounts.urls")),
    path("api/v1/profiles/", include("profiles.urls")),
    path("api/v1/tests/", include("test_system.urls")),
    path("api/v1/ai/", include("ai_engine.urls")),
    path("api/v1/roadmaps/", include("roadmaps.urls")),
    path("api/v1/progress/", include("progress.urls")),
    path("api/v1/recommendations/", include("recommendations.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)