from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from ideas.models import ProjectIdea

from .models import Booking, BookingStatus
from .services import approve_booking, cancel_booking, reject_booking


@login_required
def my_bookings(request):
    bookings = (
        Booking.objects.filter(student=request.user)
        .select_related("idea", "idea__category", "idea__supervisor")
        .prefetch_related("members")
    )
    return render(request, "bookings/my_bookings.html", {"bookings": bookings})


@login_required
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method != "POST":
        return redirect("bookings:mine")
    try:
        cancel_booking(booking=booking, user=request.user)
        messages.success(request, "تم إلغاء الحجز — أصبحت الفكرة متاحة من جديد.")
    except (PermissionDenied, ValidationError) as exc:
        if isinstance(exc, PermissionDenied):
            raise
        messages.error(request, " ".join(exc.messages))
    return redirect("bookings:mine")


@login_required
def supervisor_dashboard(request):
    """لوحة المشرف: أفكاره + الحجوزات بانتظار قراره."""
    if not request.user.is_supervisor:
        raise PermissionDenied

    if request.user.is_admin_role:
        # المدير يرى كل الحجوزات المعلقة وكل الأفكار
        my_ideas = ProjectIdea.objects.all()
        pending = Booking.objects.filter(status=BookingStatus.PENDING)
    else:
        my_ideas = request.user.supervised_ideas.all()
        pending = Booking.objects.filter(
            status=BookingStatus.PENDING, idea__in=my_ideas
        )

    pending = pending.select_related("idea", "student").prefetch_related("members")
    my_ideas = my_ideas.select_related("category").prefetch_related("bookings")

    return render(
        request,
        "bookings/supervisor_dashboard.html",
        {"pending_bookings": pending, "my_ideas": my_ideas},
    )


@login_required
def booking_decide(request, pk, action):
    """موافقة أو رفض حجز (POST فقط)."""
    if request.method != "POST":
        return redirect("supervisor:dashboard")
    booking = get_object_or_404(Booking.objects.select_related("idea"), pk=pk)
    try:
        if action == "approve":
            approve_booking(booking=booking, user=request.user)
            messages.success(
                request, f"تم اعتماد حجز «{booking.idea.title}» وقفل الفكرة."
            )
        elif action == "reject":
            reject_booking(booking=booking, user=request.user)
            messages.warning(
                request, f"تم رفض حجز «{booking.idea.title}» — الفكرة متاحة من جديد."
            )
        else:
            messages.error(request, "إجراء غير معروف.")
    except (PermissionDenied, ValidationError) as exc:
        if isinstance(exc, PermissionDenied):
            raise
        messages.error(request, " ".join(exc.messages))
    return redirect("supervisor:dashboard")
