from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Log

@admin.register(Log)
class LogAdmin(ImportExportModelAdmin):
    list_display = ('title', 'type', 'message', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            "fields": ("title", "type", "message", "is_active")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
        }),
    )
