from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(ImportExportModelAdmin):
    list_display = ("name", "email", "mobile", "status", "is_active", "created_at")
    search_fields = ("name", "email", "mobile", "message")
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Contact Info", {
            "fields": ("name", "email", "mobile", "message", "status", "is_active")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
        }),
    )
