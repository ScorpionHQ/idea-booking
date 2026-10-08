from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_("اسم التصنيف"), max_length=100, unique=True)
    slug = models.SlugField(_("المعرّف"), max_length=120, allow_unicode=True, unique=True)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)

    class Meta:
        verbose_name = _("تصنيف")
        verbose_name_plural = _("التصنيفات")
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProjectIdea(models.Model):
    STATUS_APPROVED = "approved"
    STATUS_BOOKED = "booked"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_APPROVED, _("معتمدة — متاحة للحجز")),
        (STATUS_BOOKED, _("محجوزة")),
        (STATUS_CLOSED, _("مغلقة")),
    ]

    title = models.CharField(_("عنوان الفكرة"), max_length=200)
    slug = models.SlugField(_("المعرّف"), max_length=220, unique=True, allow_unicode=True)
    description = models.TextField(_("الوصف"))
    category = models.ForeignKey(
        Category,
        verbose_name=_("التصنيف"),
        on_delete=models.PROTECT,
        related_name="ideas",
    )
    supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("المشرف"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_ideas",
    )
    max_members = models.PositiveSmallIntegerField(
        _("أقصى عدد لأعضاء الفريق"), default=5
    )
    status = models.CharField(
        _("الحالة"), max_length=20, choices=STATUS_CHOICES,
        default=STATUS_APPROVED, db_index=True,
    )
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("آخر تحديث"), auto_now=True)

    class Meta:
        verbose_name = _("فكرة مشروع")
        verbose_name_plural = _("أفكار المشاريع")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "idea"
            slug = base
            n = 1
            while ProjectIdea.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("ideas:detail", args=[self.slug])

    @property
    def is_available(self):
        return self.status == self.STATUS_APPROVED

    @property
    def active_booking(self):
        """الحجز النشط (بانتظار الموافقة أو معتمد) على هذه الفكرة إن وُجد."""
        from bookings.models import Booking, BookingStatus

        return (
            Booking.objects.filter(
                idea=self, status__in=BookingStatus.ACTIVE_STATUSES
            )
            .select_related("student")
            .prefetch_related("members")
            .first()
        )
