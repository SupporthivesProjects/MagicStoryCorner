from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from payments.models import Order, Currency
from storybook.utils.models import DefaultFields
import os
import uuid
import secrets
import string
from django.utils import timezone


def user_profile_picture_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"profile_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    return os.path.join('users', 'profiles', str(instance.user.id), filename)

def get_default_currency():
    currency = Currency.objects.filter(is_default=True).first()
    return currency.id if currency else None


class Profile(DefaultFields):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile = models.CharField(max_length=15, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True, choices=[("male", "Male"), ("female", "Female"), ("other", "Other")], help_text="Gender identity")
    bio = models.TextField(blank=True, null=True, help_text="Short bio or description about the user")
    profession = models.CharField(max_length=100, blank=True, null=True, help_text="User’s profession or role")
    email_verified_at = models.DateTimeField(null=True, blank=True, help_text="Date and time when the email was verified")
    email_verified = models.BooleanField(default=False, help_text="Indicates whether the user's email has been verified")
    email_token = models.CharField(max_length=255, null=True, blank=True, help_text="Unique token used for verifying the user's email address")
    wallet = models.PositiveIntegerField(default=0, help_text="Current token balance")
    line_1 = models.CharField(max_length=255, blank=True, null=True, help_text="Primary street address or house number")
    line_2 = models.CharField(max_length=255, blank=True, null=True, help_text="Apartment, suite, or additional address info")
    city = models.CharField(max_length=100, blank=True, null=True, help_text="City or town name")
    postal = models.CharField(max_length=20, blank=True, null=True, help_text="Postal or ZIP code")
    state = models.CharField(max_length=100, blank=True, null=True, help_text="State or province name")
    country = models.CharField(max_length=100, blank=True, null=True, help_text="Country name")
    picture = models.ImageField(upload_to=user_profile_picture_path, blank=True, null=True)
    currency = models.ForeignKey(Currency,on_delete=models.CASCADE,default=get_default_currency)

    class Meta:
        db_table = "profiles"

    def __str__(self):
        return self.user.username
    


class Wallet(DefaultFields):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wallets")
    type = models.CharField(max_length=10, choices=[("recharge", "Recharge"), ("deduct", "Deduct")], default="recharge", help_text="Last wallet action type")
    amount = models.PositiveIntegerField(default=0, help_text="Token amount that was recharged or deducted in the last transaction")
    balance = models.PositiveIntegerField(default=0, help_text="Current token balance")
    message = models.CharField(max_length=255, blank=True, null=True, help_text="Optional message or note for this transaction")
    
    class Meta:
        db_table = "wallets"

    def __str__(self):
        return f"{self.user.username} - tokens ({self.get_type_display()})"


class DailyClaim(DefaultFields):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="daily_claim")
    last_claim = models.DateTimeField(null=True, blank=True)
    claim_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = "daily_claims"
    
    def __str__(self):
        return f"{self.user.username}"
    
    def can_claim(self):
        if not self.last_claim:
            return True
        
        today = timezone.localdate()
        last_date = timezone.localtime(self.last_claim).date()

        return today > last_date


class Referral(DefaultFields):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referrals")
    referred = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral")
    code = models.CharField(max_length=12, db_index=True)
    purchased = models.BooleanField(default=False)
    rewarded = models.BooleanField(default=False)
    reward_at = models.DateTimeField(null=True, blank=True)
    tokens = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = "referrals"
        indexes = [
            models.Index(fields=['referrer', 'rewarded']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.referrer.username} -> {self.referred.username}"


class ReferralCode(DefaultFields):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="ref_code")
    code = models.CharField(max_length=12, unique=True, db_index=True)
    referral_count = models.PositiveIntegerField(default=0)
    tokens_earned = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = "referral_codes"
    
    def __str__(self):
        return f"{self.user.username} - {self.code}"
    
    @staticmethod
    def generate():
        while True:
            code = uuid.uuid4().hex[:8].upper()
            if not ReferralCode.objects.filter(code=code).exists():
                return code
    
    def get_link(self):
        from legals.models import Website
        website = Website.objects.filter(is_active=True).first()
        base_url = website.website
        base_url = base_url.rstrip('/')
        return f"{base_url}/payments/package-pricing/?ref={self.code}"