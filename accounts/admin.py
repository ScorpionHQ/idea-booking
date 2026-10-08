from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "first_name", "university_number", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    fieldsets = DjangoUserAdmin.fieldsets + (
        (_("بيانات المنصة"), {"fields": ("role", "university_number", "phone")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (_("بيانات المنصة"), {"fields": ("role", "university_number", "phone")}),
    )
