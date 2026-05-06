from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Profile, Wallet, DailyClaim, Referral, ReferralCode
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html


admin.site.site_header = _('Little Story Box')
admin.site.site_title = _('Admin Panel')
admin.site.index_title = _('Welcome to Administration')


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = ("user","mobile", "picture", "dob", "gender", "bio", "profession", "wallet", "line_1", "line_2", "city", "postal", "state", "country", "currency")
    readonly_fields = ()


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    list_display = ("user", "Picture", "mobile", "gender", "profession", "wallet", "city", "email_verified")
    search_fields = ("user__username", "mobile", "profession", "city")
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at", "email_verified_at", "email_token")

    def Picture(self, obj):
        if obj.picture:
            return format_html(
                '<img src="{}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; display:block; margin-left: 0px;" />',
                obj.picture.url,
            )
        return "-"
    Picture.short_description = "Picture"

    fieldsets = (
        ("User Info", {"fields": ("user", "mobile", "picture", "dob", "gender", "bio", "profession")}),
        ("Wallet", {"fields": ("wallet",)}),
        ("Address", {"fields": ("line_1", "line_2", "city", "postal", "state", "country", "currency")}),
        ("Email Verification", {"fields": ("email_verified", "email_verified_at", "email_token")}),
        ("Audit Info", {"classes": ("collapse",), "fields": ("created_by", "updated_by", "created_at", "updated_at")}),
    )


@admin.register(Wallet)
class WalletAdmin(ImportExportModelAdmin):
    list_display = ("user", "type", "amount", "balance", "message","created_at")
    search_fields = ("user__username",)
    readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": ("user", "type", "amount", "balance","message")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at")
        }),
    )



@admin.register(DailyClaim)
class DailyClaimAdmin(ImportExportModelAdmin):
    list_display = ("user", "last_claim", "claim_count", "can_claim_status", "is_active", "created_at")
    search_fields = ("user__username", "user__email")
    list_filter = ("is_active", "last_claim", "created_at")
    readonly_fields = ("created_at", "updated_at", "can_claim_status")
    raw_id_fields = ("user",)
    
    fieldsets = (
        ("User Information", {
            "fields": ("user",)
        }),
        ("Claim Details", {
            "fields": ("last_claim", "claim_count", "can_claim_status")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )
    
    def can_claim_status(self, obj):
        if obj.can_claim():
            return format_html('<span style="color: green;">✓ Can Claim</span>')
        return format_html('<span style="color: red;">✗ Cannot Claim</span>')
    can_claim_status.short_description = "Can Claim Today"


@admin.register(Referral)
class ReferralAdmin(ImportExportModelAdmin):
    list_display = ("referrer", "referred", "code", "purchased", "rewarded", "tokens", "reward_at", "is_active", "created_at")
    search_fields = ("referrer__username", "referrer__email", "referred__username", "referred__email", "code")
    list_filter = ("purchased", "rewarded", "is_active", "created_at", "reward_at")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("referrer", "referred")
    
    fieldsets = (
        ("Referral Information", {
            "fields": ("referrer", "referred", "code")
        }),
        ("Status & Rewards", {
            "fields": ("purchased", "rewarded", "tokens", "reward_at")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('referrer', 'referred')


@admin.register(ReferralCode)
class ReferralCodeAdmin(ImportExportModelAdmin):
    list_display = ("user", "code", "referral_count", "tokens_earned", "referral_link", "is_active", "created_at")
    search_fields = ("user__username", "user__email", "code")
    list_filter = ("is_active", "created_at")
    readonly_fields = ("created_at", "updated_at", "referral_link")
    raw_id_fields = ("user",)
    
    fieldsets = (
        ("User Information", {
            "fields": ("user",)
        }),
        ("Code Details", {
            "fields": ("code", "referral_link")
        }),
        ("Statistics", {
            "fields": ("referral_count", "tokens_earned")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
        ("Timestamps", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )
    
    def referral_link(self, obj):
        link = obj.get_link()
        return format_html('<a href="{}" target="_blank">{}</a>', link, link)
    referral_link.short_description = "Referral Link"