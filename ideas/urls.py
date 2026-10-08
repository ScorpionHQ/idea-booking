from django.urls import path

from . import views

app_name = "ideas"

urlpatterns = [
    path("", views.idea_list, name="list"),
    path("add/", views.idea_manage, name="add"),
    path("<str:slug>/", views.idea_detail, name="detail"),
    path("<str:slug>/book/", views.idea_book, name="book"),
    path("<str:slug>/edit/", views.idea_manage, name="edit"),
    path("<str:slug>/delete/", views.idea_delete, name="delete"),
]
