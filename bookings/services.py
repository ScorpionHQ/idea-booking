"""منطق عمل الحجوزات — كل قواعد الحجز والموافقة في مكان واحد."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils.translation import gettext as _

from ideas.models import ProjectIdea

from .models import Booking, BookingMember, BookingStatus


def create_booking(*, idea: ProjectIdea, student, note: str, members: list) -> Booking:
    """
    إنشاء حجز جديد لفكرة.

    members: قائمة dicts فيها full_name / university_number / role
    قواعد العمل:
      - الفكرة يجب أن تكون معتمدة (متاحة)
      - لا يجوز أن يوجد حجز نشط على الفكرة
      - لا يجوز أن يكون لدى الطالب حجز نشط آخر
      - 1 (الحائز) + الأعضاء <= max_members
    """
    idea = ProjectIdea.objects.select_for_update().get(pk=idea.pk)

    if idea.status != ProjectIdea.STATUS_APPROVED:
        raise ValidationError(_("هذه الفكرة غير متاحة للحجز حاليًا."))

    if Booking.objects.filter(idea=idea, status__in=BookingStatus.ACTIVE_STATUSES).exists():
        raise ValidationError(_("هذه الفكرة محجوزة بالفعل — اختر فكرة أخرى."))

    if Booking.objects.filter(
        student=student, status__in=BookingStatus.ACTIVE_STATUSES
    ).exists():
        raise ValidationError(_("لديك حجز نشط بالفعل — ألغِه أولًا لحجز فكرة أخرى."))

    members = [m for m in members if (m.get("full_name") or "").strip()]
    team_size = 1 + len(members)
    if team_size > idea.max_members:
        raise ValidationError(
            _("حجم الفريق ({size}) يتجاوز الحد الأقصى ({max}).").format(
                size=team_size, max=idea.max_members
            )
        )

    with transaction.atomic():
        booking = Booking.objects.create(idea=idea, student=student, note=note)
        BookingMember.objects.bulk_create(
            [
                BookingMember(
                    booking=booking,
                    full_name=m["full_name"].strip(),
                    university_number=(m.get("university_number") or "").strip(),
                    role=m.get("role") or BookingMember.ROLE_MEMBER,
                )
                for m in members
            ]
        )
    return booking


def cancel_booking(*, booking: Booking, user) -> None:
    """الطالب يلغي حجزه (نجم أو مؤكد)."""
    if booking.student_id != user.pk and not user.is_admin_role:
        raise PermissionDenied
    if not booking.is_active:
        raise ValidationError(_("هذا الحجز ليس نشطًا — لا يمكن إلغاؤه."))

    was_approved = booking.status == BookingStatus.APPROVED
    with transaction.atomic():
        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        if was_approved and booking.idea.status == ProjectIdea.STATUS_BOOKED:
            booking.idea.status = ProjectIdea.STATUS_APPROVED
            booking.idea.save(update_fields=["status", "updated_at"])


def approve_booking(*, booking: Booking, user) -> None:
    """المشرف المعتمد على الفكرة يوافق → تُقفل الفكرة."""
    idea = booking.idea
    if not user.is_admin_role and idea.supervisor_id != user.pk:
        raise PermissionDenied
    if booking.status != BookingStatus.PENDING:
        raise ValidationError(_("هذا الحجز ليس بانتظار الموافقة."))

    with transaction.atomic():
        booking.status = BookingStatus.APPROVED
        booking.save(update_fields=["status", "updated_at"])
        if idea.status == ProjectIdea.STATUS_APPROVED:
            idea.status = ProjectIdea.STATUS_BOOKED
            idea.save(update_fields=["status", "updated_at"])


def reject_booking(*, booking: Booking, user) -> None:
    """المشرف يرفض الحجز → يبقى بإمكان الآخرين حجز الفكرة."""
    idea = booking.idea
    if not user.is_admin_role and idea.supervisor_id != user.pk:
        raise PermissionDenied
    if booking.status != BookingStatus.PENDING:
        raise ValidationError(_("هذا الحجز ليس بانتظار الموافقة."))

    booking.status = BookingStatus.REJECTED
    booking.save(update_fields=["status", "updated_at"])
