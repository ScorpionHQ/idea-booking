from django.contrib import admin
from django.urls import include, path

from bookings.urls import supervisor_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("bookings/", include("bookings.urls")),
    path("supervisor/", include((supervisor_urlpatterns, "supervisor"))),
    path("", include("ideas.urls")),
]
