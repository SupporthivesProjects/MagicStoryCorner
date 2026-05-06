from decimal import Decimal
import os
from django.db import models
from storybook.utils.models import DefaultFields
from django.contrib.auth.models import User
from django.utils import timezone


class Coupon(DefaultFields):
    name = models.CharField(max_length=100, help_text="Enter a descriptive name for the coupon (e.g., 'New Year Discount').")
    code = models.CharField(max_length=50, unique=True, help_text="Enter a unique code users will apply at checkout (e.g., 'NEWYEAR2026').")
    discount = models.DecimalField(max_digits=5, decimal_places=2, help_text="Enter the discount percentage (e.g., 10")
    startdate = models.DateTimeField(default=timezone.now, help_text="The date and time when the coupon becomes active.")
    enddate = models.DateTimeField(null=True, blank=True, help_text="The date and time when the coupon expires. Leave blank for no expiry.")

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        db_table = 'coupons'

def package_image_upload_path(instance, filename):
    return f"packages/{instance.packagetype.id}/{filename}"


class PackageType(DefaultFields):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "package_types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Package(DefaultFields):
    packagetype = models.ForeignKey(PackageType, on_delete=models.CASCADE, related_name="packages")
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Package display name")
    tokens = models.PositiveIntegerField(help_text="Number of tokens included in this package")
    description = models.TextField(blank=True, null=True, help_text="Short note about what this package offers")
    currency = models.CharField(max_length=5, default="$", help_text="Currency symbol, e.g., $ or ₹")
    price = models.DecimalField(max_digits=6, decimal_places=2)
    order = models.PositiveIntegerField(default=0, help_text="Order for sorting packages")
    is_popular = models.BooleanField(default=False, help_text="Mark if this is a popular package")
    image = models.ImageField(upload_to=package_image_upload_path, blank=True, null=True)

    class Meta:
        db_table = "packages"
        ordering = ["order", "price"]

    def __str__(self):
        return f"{self.packagetype.name} - {self.tokens} tokens"
    


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SUCCESS = 'success', 'Success'
    FAILED = 'failed', 'Failed'
    CANCELLED = 'cancelled', 'Cancelled'
    REFUND = 'refund', 'Refund'


class Order(DefaultFields):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    quantity = models.PositiveIntegerField(default=1)
    currency = models.CharField(max_length=5, default="$", help_text="Currency symbol, e.g., $ or ₹")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount amount for the entire order")
    coupon = models.CharField(max_length=50, blank=True, null=True, help_text="Applied coupon code")
    referral = models.CharField(max_length=12, blank=True, null=True, help_text="Applied referral code")
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), help_text="GST amount (18%) for the order")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), help_text="Total amount for the order including GST")
    tokens = models.PositiveIntegerField(default=0, help_text="Total tokens this order will credit to the user")
    status = models.CharField(max_length=10, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} ({self.get_status_display()})"


class OrderItem(DefaultFields):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    currency = models.CharField(max_length=5, default="$", help_text="Currency symbol, e.g., $ or ₹")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tokens = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'order_items'

    def __str__(self):
        return f"{self.package} x {self.quantity} (Order #{self.order.id})"
    

class PaymentTransaction(DefaultFields):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payment_transactions")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment_transactions")
    response = models.JSONField(blank=True, null=True, help_text="Raw response from the payment gateway")

    class Meta:
        db_table = "payment_transactions"
        ordering = ['-created_at']

    def __str__(self):
        return f"PaymentTransaction #{self.id} - User: {self.user.username}, Order: {self.order.id}"


# Currency Model - Added by Jeet
class Currency(DefaultFields):
    name = models.CharField(max_length=100, help_text="Full name (e.g. US Dollar).")
    code = models.CharField(max_length=5, unique=True, help_text="ISO code (e.g. USD, EUR, GBP).")
    symbol = models.CharField(max_length=5, help_text="Symbol (e.g. $, €, £).")
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1.000000, help_text="Rate relative to USD. Use 1.0 for USD itself.")
    is_default = models.BooleanField(default=False, help_text="Site-wide default. Only one currency can be default.")
    

    class Meta:
        db_table = "currencies"
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ["-is_default", "code"]

    def __str__(self):
        return f"{self.code} ({self.symbol})"

    def save(self, *args, **kwargs):
        if self.is_default:
            Currency.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)