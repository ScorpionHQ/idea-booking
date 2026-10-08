from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class BookingStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ACTIVE_STATUSES = (PENDING, APPROVED)
    CHOICES = [
        (PENDING, _("بانتظار موافقة المشرف")),
        (APPROVED, _("معتمد")),
        (REJECTED, _("مرفوض")),
        (CANCELLED, _("ملغى")),
    ]


class Booking(models.Model):
    idea = models.ForeignKey(
        "ideas.ProjectIdea",
        verbose_name=_("الفكرة"),
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("الطالب الحائز"),
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    note = models.TextField(
        _("ملاحظة من الطالب"), blank=True,
        help_text=_("رسالة قصيرة للمشرف (اختياري)"),
    )
    status = models.CharField(
        _("الحالة"), max_length=20,
        choices=BookingStatus.CHOICES,
        default=BookingStatus.PENDING, db_index=True,
    )
    created_at = models.DateTimeField(_("تاريخ الحجز"), auto_now_add=True)
    updated_at = models.DateTimeField(_("آخر تحديث"), auto_now=True)

    class Meta:
        verbose_name = _("حجز فكرة")
        verbose_name_plural = _("حجوزات الأفكار")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["idea"],
                condition=models.Q(status__in=("pending", "approved")),
                name="one_active_booking_per_idea",
            ),
            models.UniqueConstraint(
                fields=["student"],
                condition=models.Q(status__in=("pending", "approved")),
                name="one_active_booking_per_student",
            ),
        ]

    def __str__(self):
        return f"{self.student.display_name} → {self.idea.title}"

    @property
    def is_active(self):
        return self.status in BookingStatus.ACTIVE_STATUSES

    @property
    def team_size(self):
        """إجمالي أعضاء الفريق = الطالب الحائز + الأعضاء المكتوبون."""
        return 1 + self.members.count()

    def clean(self):
        super().clean()
        if self.idea_id and self.status in BookingStatus.ACTIVE_STATUSES:
            if self.idea.status == self.idea.STATUS_CLOSED:
                raise ValidationError({"idea": _("لا يمكن حجز فكرة مغلقة.")})
            if (
                self.student_id
                and Booking.objects.filter(
                    student=self.student,
                    status__in=BookingStatus.ACTIVE_STATUSES,
                )
                .exclude(pk=self.pk)
                .exists()
            ):
                raise ValidationError(
                    _("لديك حجز نشط بالفعل — ألغِه أولاً لحجز فكرة أخرى.")
                )


class BookingMember(models.Model):
    ROLE_LEADER = "leader"
    ROLE_MEMBER = "member"
    ROLE_CHOICES = [
        (ROLE_LEADER, _("قائد الفريق")),
        (ROLE_MEMBER, _("عضو")),
    ]

    booking = models.ForeignKey(
        Booking,
        verbose_name=_("الحجز"),
        on_delete=models.CASCADE,
        related_name="members",
    )
    full_name = models.CharField(_("الاسم الكامل"), max_length=150)
    university_number = models.CharField(_("الرقم الجامعي"), max_length=30, blank=True)
    role = models.CharField(
        _("الدور داخل الفريق"), max_length=20,
        choices=ROLE_CHOICES, default=ROLE_MEMBER,
    )
    created_at = models.DateTimeField(_("تاريخ الإضافة"), auto_now_add=True)

    class Meta:
        verbose_name = _("عضو فريق")
        verbose_name_plural = _("أعضاء الفريق")
        ordering = ["id"]

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
