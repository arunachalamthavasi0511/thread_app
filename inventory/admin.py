# inventory/admin.py

from django.contrib import admin
from .models import Thread, Issuance, Profile


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = (
        "shade",
        "tkt",
        "bin_no",
        "column_name",
        "available_quantity",
        "category",
        "brand",
        "registration_date",
        "created_by",
    )
    search_fields = ("shade", "tkt", "bin_no", "column_name", "brand")
    list_filter = ("category", "brand")
    ordering = ("shade", "tkt", "bin_no", "column_name")


@admin.register(Issuance)
class IssuanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "thread",
        "requested_quantity",
        "status",
        "requested_by",
        "approved_by",
        "requested_at",
        "approved_at",
        "rejection_reason",
    )
    search_fields = ("thread__shade", "thread__tkt", "requested_by__username", "approved_by__username")
    list_filter = ("status",)
    ordering = ("-requested_at",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
