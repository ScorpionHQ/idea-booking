from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("mine/", views.my_bookings, name="mine"),
    path("<int:pk>/cancel/", views.booking_cancel, name="cancel"),
]

supervisor_urlpatterns = [
    path("", views.supervisor_dashboard, name="dashboard"),
    path("decide/<int:pk>/<str:action>/", views.booking_decide, name="decide"),
]
