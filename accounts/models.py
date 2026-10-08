from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    ROLE_STUDENT = "student"
    ROLE_SUPERVISOR = "supervisor"
    ROLE_ADMIN = "admin"
    ROLE_CHOICES = [
        (ROLE_STUDENT, _("طالب")),
        (ROLE_SUPERVISOR, _("مشرف")),
        (ROLE_ADMIN, _("مدير")),
    ]

    role = models.CharField(
        _("الدور"), max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT
    )
    university_number = models.CharField(
        _("الرقم الجامعي"), max_length=30, blank=True, db_index=True
    )
    phone = models.CharField(_("رقم الهاتف"), max_length=30, blank=True)

    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("المستخدمون")

    @property
    def is_supervisor(self):
        return self.role == self.ROLE_SUPERVISOR or self.is_staff

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN or self.is_staff

    @property
    def display_name(self):
        full = self.get_full_name()
        return full or self.username
