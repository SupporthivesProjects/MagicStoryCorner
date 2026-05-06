from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import LegalContent, Website

@admin.register(LegalContent)
class LegalContentAdmin(ImportExportModelAdmin):
    list_display = ("type", "title", "is_active", "updated_at")
    search_fields = ("title", "content")
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {
            "fields": ("type", "title", "is_active")
        }),
        ("Content", {
            "fields": ("content",)
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at"),
        }),
    )

@admin.register(Website)
class WebsiteAdmin(ImportExportModelAdmin):
    list_display = ("company", "domain", "website", "email", "mobile", "maintenance_mode", "is_active", "created_at")
    search_fields = ("company", "domain", "website", "email")
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("is_active", "maintenance_mode", "payment_gateway", "sms_provider")

    fieldsets = (
        ("Company Info", {
            "fields": ("company", "domain", "website")
        }),
        ("Contact Details", {
            "fields": ("email", "mobile", "address")
        }),
        ("Images", {
            "fields": ("logo", "header", "footer", "signature")
        }),
        ("reCAPTCHA Configuration", {
            "classes": ("collapse",),
            "fields": ("recaptcha_site_key", "recaptcha_secret_key")
        }),
        ("SMTP Configuration", {
            "classes": ("collapse",),
            "fields": ("smtp_host", "smtp_port", "smtp_username", "smtp_password", "smtp_use_tls")
        }),
        ("API Configuration", {
            "classes": ("collapse",),
            "fields": ("api_key", "api_secret")
        }),
        ("Payment Gateway", {
            "classes": ("collapse",),
            "fields": ("payment_gateway", "payment_key", "payment_secret")
        }),
        ("SMS Configuration", {
            "classes": ("collapse",),
            "fields": ("sms_provider", "sms_api_key", "sms_api_secret", "sms_sender_id")
        }),
        ("Analytics & Tracking", {
            "classes": ("collapse",),
            "fields": ("google_analytics_id", "facebook_pixel_id")
        }),
        ("Social Media Links", {
            "classes": ("collapse",),
            "fields": ("social_facebook", "social_twitter", "social_instagram", "social_linkedin", "social_youtube")
        }),
        ("Maintenance Mode", {
            "fields": ("maintenance_mode", "maintenance_message")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )