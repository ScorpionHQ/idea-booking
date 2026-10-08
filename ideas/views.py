from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import BookingStatus
from bookings.services import create_booking

from .forms import IdeaFilterForm, IdeaForm
from .models import ProjectIdea


def idea_list(request):
    form = IdeaFilterForm(request.GET or None)
    ideas = ProjectIdea.objects.select_related("category", "supervisor").prefetch_related(
        "bookings"
    )

    if form.is_valid():
        q = form.cleaned_data.get("q")
        if q:
            ideas = ideas.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        if form.cleaned_data.get("category"):
            ideas = ideas.filter(category=form.cleaned_data["category"])
        if form.cleaned_data.get("status"):
            ideas = ideas.filter(status=form.cleaned_data["status"])
        else:
            # للمستخدم العادي نُظهر المعتمدة والمحجوزة (التي تظهر حالتها) والمغلقة أيضًا
            pass

    context = {
        "form": form,
        "ideas": ideas,
        "status_labels": dict(ProjectIdea.STATUS_CHOICES),
    }
    return render(request, "ideas/idea_list.html", context)


def idea_detail(request, slug):
    idea = get_object_or_404(
        ProjectIdea.objects.select_related("category", "supervisor"), slug=slug
    )
    active_booking = idea.active_booking

    my_booking = None
    if request.user.is_authenticated:
        my_booking = idea.bookings.filter(student=request.user).first()

    can_book = bool(
        request.user.is_authenticated
        and not request.user.is_supervisor
        and idea.is_available
        and active_booking is None
        and (my_booking is None or not my_booking.is_active)
    )

    context = {
        "idea": idea,
        "active_booking": active_booking,
        "my_booking": my_booking,
        "can_book": can_book,
        "members_range": range(1, max(idea.max_members - 1, 0) + 1),
    }
    return render(request, "ideas/idea_detail.html", context)


@login_required
def idea_book(request, slug):
    idea = get_object_or_404(ProjectIdea, slug=slug)
    if request.method != "POST":
        return redirect(idea)

    members = []
    names = request.POST.getlist("member_name")
    numbers = request.POST.getlist("member_number")
    for i, name in enumerate(names):
        members.append(
            {
                "full_name": name,
                "university_number": numbers[i] if i < len(numbers) else "",
                "role": "member",
            }
        )

    try:
        booking = create_booking(
            idea=idea,
            student=request.user,
            note=request.POST.get("note", "").strip(),
            members=members,
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        return redirect("ideas:detail", slug=slug)

    messages.success(
        request,
        f"تم إرسال حجزك لفكرة «{idea.title}» بانتظار موافقة المشرف.",
    )
    return redirect("bookings:mine")


@login_required
def idea_manage(request, slug=None):
    """إضافة فكرة جديدة أو تعديل فكرة موجودة (للمشرفين فقط)."""
    if not request.user.is_supervisor:
        raise PermissionDenied

    idea = get_object_or_404(ProjectIdea, slug=slug) if slug else None

    if idea and not request.user.is_admin_role and idea.supervisor_id != request.user.pk:
        raise PermissionDenied

    if request.method == "POST":
        form = IdeaForm(request.POST, instance=idea, user=request.user)
        if form.is_valid():
            saved = form.save()
            if idea:
                messages.success(request, f"تم تحديث فكرة «{saved.title}».")
            else:
                messages.success(request, f"تمت إضافة فكرة «{saved.title}».")
            return redirect(saved.get_absolute_url())
    else:
        form = IdeaForm(instance=idea, user=request.user)

    return render(
        request,
        "ideas/idea_form.html",
        {"form": form, "idea": idea},
    )


@login_required
def idea_delete(request, slug):
    if not request.user.is_supervisor:
        raise PermissionDenied
    idea = get_object_or_404(ProjectIdea, slug=slug)
    if idea.supervisor_id != request.user.pk and not request.user.is_admin_role:
        raise PermissionDenied
    if request.method == "POST":
        if idea.bookings.filter(status__in=BookingStatus.ACTIVE_STATUSES).exists():
            messages.error(request, "لا يمكن حذف فكرة عليها حجوزات نشطة.")
            return redirect(idea)
        title = idea.title
        idea.delete()
        messages.success(request, f"تم حذف فكرة «{title}».")
        return redirect("ideas:list")
    return render(request, "ideas/idea_confirm_delete.html", {"idea": idea})
