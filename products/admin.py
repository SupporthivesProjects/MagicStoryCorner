from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Configuration, ProductBook, ProductBookPage, ProductBookPurchase

@admin.register(Configuration)
class ConfigurationAdmin(ImportExportModelAdmin):
    list_display = ("chars_per_page", "max_pages", "workers", "updated_at")
    search_fields = ("verbose_name",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    ordering = ("-created_at",)

    fieldsets = (
        ("Content Settings", {
            "fields": ("chars_per_page", "max_pages")
        }),
        ("Generation & Retry Settings", {
            "fields": ("img_retries", "tts_retries", "story_retries", "min_story_len")
        }),
        ("Processing Settings", {
            "fields": ("workers", "consistency_checks")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
        }),
    )
    
class ProductBookPageInline(admin.TabularInline):
    model = ProductBookPage
    extra = 0
    fields = ("page", "text_preview", "image", "audio")
    readonly_fields = ("text_preview", "created_at", "updated_at")

    def text_preview(self, obj):
        return obj.text[:50] + ("..." if len(obj.text) > 50 else "")
    text_preview.short_description = "Text"


@admin.register(ProductBook)
class ProductBookAdmin(ImportExportModelAdmin):
    list_display = ("title", "prompt", "tokens", "agegroup", "theme", "language", "status", "created_at")
    search_fields = ("title", "description")
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    inlines = [ProductBookPageInline]

    fieldsets = (
        ("Basic Info", {
            "fields": ("title","char_img", "currency", "tokens", "slug", "description", "image", "pdf", "status")
        }),
        ("Story Details", {
            "fields": (
                "prompt",
                "agegroup",
                "setting",
                "plot",
                "theme",
                "tone",
                "length",
                "imagestyle",
                "language",
                "narrator",
                "storyend",
            )
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
        }),
    )


@admin.register(ProductBookPage)
class ProductBookPageAdmin(ImportExportModelAdmin):
    list_display = ("book", "page", "text_preview", "image", "audio", "created_at")
    search_fields = ("book__title", "text")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("book", "page")

    fieldsets = (
        ("Page Info", {
            "fields": ("book", "page", "text", "image", "audio")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    def text_preview(self, obj):
        return obj.text[:50] + ("..." if len(obj.text) > 50 else "")
    text_preview.short_description = "Text"


@admin.register(ProductBookPurchase)
class ProductBookPurchaseAdmin(ImportExportModelAdmin):
    list_display = ("user", "book", "created_at")
    search_fields = ("user__username", "book__title")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    ordering = ("-created_at",)

    fieldsets = (
        ("Purchase Info", {
            "fields": ("user", "book")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
        }),
    )

    def save_model(self, request, obj, form, change):
        from django.contrib.auth.models import AnonymousUser

        user = request.user if not isinstance(request.user, AnonymousUser) else None
        username = user.username if user else None

        if not obj.pk:
            obj.created_by = username
        obj.updated_by = username
        super().save_model(request, obj, form, change)
