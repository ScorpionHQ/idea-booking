from django.contrib import admin

from .models import Booking, BookingMember


class BookingMemberInline(admin.TabularInline):
    model = BookingMember
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("idea", "student", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("idea__title", "student__username", "student__first_name")
    inlines = [BookingMemberInline]
