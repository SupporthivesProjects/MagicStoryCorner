from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import AIModel, ChildAgeRange, StoryBookPage, StoryEnd, StorySetting, StoryPlot, StoryTheme, StoryTone, ImageStyle, LanguageOption, NarratorVoice, StoryBook, StoryLength
from django.utils.html import format_html


@admin.register(AIModel)
class AIModelAdmin(ImportExportModelAdmin):
    list_display = (
        "name", "alias","emoji", "type", "family", "temperature",
        "is_active", "created_at", "updated_at"
    )
    search_fields = ("name", "alias", "family")
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    ordering = ("family", "type")
    fieldsets = (
        (None, {
            "fields": (
                "name", "emoji", "alias","type","family","apikey",  "temperature", "endpoint", "parameters",  "is_active",
            )
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
        }),
    )


@admin.register(ChildAgeRange)
class ChildAgeRangeAdmin(ImportExportModelAdmin):
    list_display = ("name", "content","emoji", "cost", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    def Icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; display:block; margin-left: -5px;" />', obj.icon.url)
        return "-"
    Icon.short_description = "Icon"
    fieldsets = (
        (None, {"fields": ("name","emoji", "content", "cost", "is_active")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )


@admin.register(StorySetting)
class StorySettingAdmin(ImportExportModelAdmin):
    list_display = ("name","content","emoji", "cost", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    def Icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; display:block; margin-left: -5px;" />', obj.icon.url)
        return "-"
    Icon.short_description = "Icon"
    fieldsets = (
        (None, {"fields": ("name", "emoji", "content", "cost", "is_active")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )


@admin.register(StoryPlot)
class StoryPlotAdmin(ImportExportModelAdmin):
    list_display = ("name","content", "emoji", "cost", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    def Icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; display:block; margin-left: -5px;" />', obj.icon.url)
        return "-"
    Icon.short_description = "Icon"
    fieldsets = (
        (None, {"fields": ("name","emoji", "content", "cost", "is_active")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )


@admin.register(StoryTheme)
class StoryThemeAdmin(ImportExportModelAdmin):
    list_display = ("name","content","emoji", "cost", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    def Icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; display:block; margin-left: -5px;" />', obj.icon.url)
        return "-"
    Icon.short_description = "Icon"
    fieldsets = (
        (None, {"fields": ("name","emoji", "content", "cost", "is_active")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )


@admin.register(StoryTone)
class StoryToneAdmin(ImportExportModelAdmin):
    list_display = ("name","content","emoji", "cost", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    def Icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; display:block; margin-left: -5px;" />', obj.icon.url)
        return "-"
    Icon.short_description = "Icon"
    fieldsets = (
        (None, {"fields": ("name","emoji", "content", "cost", "is_active")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )


@admin.register(ImageStyle)
class ImageStyleAdmin(ImportExportModelAdmin):
    list_display = ("name", "content","Icon", "cost", "is_active", "created_at", "updated_at")  # Use Icon method here
    search_fields = ("name",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def Icon(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return format_html(
                '<img src="{}" style="width:45px; height:45px; object-fit:cover; display:block;" />',
                obj.image.url
            )
        return "-"
    Icon.short_description = "Image"

    fieldsets = (
        (None, {"fields": ("name", "image", "content", "cost", "is_active")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )


@admin.register(LanguageOption)
class LanguageOptionAdmin(ImportExportModelAdmin):
    list_display = ("name","content","emoji", "cost", "is_active", "created_at", "updated_at")
    search_fields = ("name", "code")
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    def Icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; display:block; margin-left: -5px;" />', obj.icon.url)
        return "-"
    Icon.short_description = "Icon"
    fieldsets = (
        (None, {"fields": ("name","emoji",  "content", "cost", "is_active")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )


@admin.register(NarratorVoice)
class NarratorVoiceAdmin(ImportExportModelAdmin):
    list_display = ("name", "vid", "AudioPlayer", "model", "cost", "is_active", "created_at")
    search_fields = ("name", "model__name")
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at", "AudioPlayer")
    def Icon(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; display:block; margin-left: -5px;" />',
                obj.icon.url
            )
        return "-"
    Icon.short_description = "Icon"
    def AudioPlayer(self, obj):
        url = obj.voice if obj.voice else (obj.upload.url if obj.upload else None)
        if url:
            return format_html(
                '<audio controls style="width:200px;">'
                '<source src="{}" type="audio/mpeg">'
                'Your browser does not support the audio element.'
                '</audio>',
                url
            )
        return "-"
    AudioPlayer.short_description = "Voice"
    fieldsets = (
        (None, {"fields": ("name", "emoji","icon","vid", "gender", "voice", "upload", "model", "cost", "is_active", "AudioPlayer")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )


@admin.register(StoryLength)
class StoryLengthAdmin(ImportExportModelAdmin):
    list_display = ("name", "content", "emoji", "min", "max", "cost", "is_active", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")
    def Icon(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; display:block; margin-left: -5px;" />', obj.icon.url)
        return "-"
    Icon.short_description = "Icon"
    fieldsets = (
        (None, {
            "fields": ("name","content", "emoji", "min", "max", "cost", "is_active")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
        }),
    )


@admin.register(StoryEnd)
class StoryEndAdmin(ImportExportModelAdmin):
    list_display = ("name", "Icon", "context", "is_active", "created_at", "updated_at")
    search_fields = ("name", "context")
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def Icon(self, obj):
        return obj.icon if obj.icon else "-"
    Icon.short_description = "Icon"

    fieldsets = (
        (None, {
            "fields": ("name", "icon", "context", "is_active")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
        }),
    )

    
class StoryBookPageInline(admin.TabularInline):
    model = StoryBookPage
    extra = 0
    fields = ("page", "text_preview", "image", "audio")
    readonly_fields = ("text_preview", "created_at", "updated_at")

    def text_preview(self, obj):
        return obj.text[:50] + ("..." if len(obj.text) > 50 else "")
    text_preview.short_description = "Text"


@admin.register(StoryBookPage)
class StoryBookPageAdmin(ImportExportModelAdmin):
    list_display = ("book", "prompt", "page", "text_preview", "image", "audio", "is_active", "created_at")
    search_fields = ("book__title", "text")
    ordering = ("book", "page")
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    def text_preview(self, obj):
        return obj.text[:50] + ("..." if len(obj.text) > 50 else "")
    text_preview.short_description = "Text"


@admin.register(StoryBook)
class StoryBookAdmin(ImportExportModelAdmin):
    list_display = ("title", "user", "status", "language", "length", "created_at")
    list_editable = ("status",)
    search_fields = ("title", "user__username")
    inlines = [StoryBookPageInline]
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {
            "fields": ("user", "title", "slug", "description", "image", "pdf", "status")
        }),
        ("Story Details", {
            "fields": (
                "prompt",
                "tokens",
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