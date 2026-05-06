from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Coupon, Order, OrderItem, PackageType, Package, PaymentTransaction, Currency
import json


@admin.register(Coupon)
class CouponAdmin(ImportExportModelAdmin):
    list_display = ("name", "code", "discount", "startdate", "enddate","is_active")
    search_fields = ("name", "code")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (None, {
            "fields": ("name", "code", "discount", "startdate", "enddate","is_active")
        }),
    )
    
@admin.register(PackageType)
class PackageTypeAdmin(ImportExportModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        (None, {
            "fields": ("name", "description")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )



@admin.register(Package)
class PackageAdmin(ImportExportModelAdmin):
    list_display = ("name", "packagetype",  "price", "tokens","order", "is_popular", "is_active", "created_at")
    search_fields = ("name", "packagetype__name")
    ordering = ("order", "price")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        (None, {
            "fields": ("packagetype", "name",  "description", "currency", "price","tokens", "order", "is_popular", "is_active", "image")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("package", "quantity", "price", "discount", "tokens", "currency")
    can_delete = True


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("created_at", "updated_at")
    fields = ("package", "quantity", "price", "discount", "tokens", "currency")
    can_delete = True


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    list_display = ("id","user","quantity","discount","gst","total","tokens","status","created_at")
    search_fields = ("user__username", "user__email", "coupon")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (None, {
            "fields": (
                "user", "quantity", "discount", "coupon", "referral", "gst", "total",
                "tokens", "status", "currency"
            )
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at")
        }),
    )
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user.username  
        obj.updated_by = request.user.username     
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(ImportExportModelAdmin):
    list_display = ("id","order","package","quantity","currency","price","discount","tokens","created_at")
    search_fields = ("order__id", "package__name", "order__user__username")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("order", "package", "quantity", "price", "discount", "tokens", "currency")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )



@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(ImportExportModelAdmin):
    list_display = ("id", "user", "order", "created_at", "short_response")
    search_fields = ("user__username", "user__email", "order__id")
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        (None, {
            "fields": ("user", "order", "response")
        }),
        ("Audit Info", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at")
        }),
    )

    def short_response(self, obj):
        if obj.response:
            text = json.dumps(obj.response)
            return text[:75] + "..." if len(text) > 75 else text
        return "-"
    short_response.short_description = "Response"

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "symbol", "exchange_rate", "is_default")
    list_filter = ("is_default",)
    search_fields = ("code", "name")
    ordering = ("-is_default", "code")