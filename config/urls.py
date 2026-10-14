from django.contrib import admin
from django.urls import include, path

from .health import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", health, name="health"),
    path("api/v1/", include("fleet.urls")),
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("bookings.urls")),
]
