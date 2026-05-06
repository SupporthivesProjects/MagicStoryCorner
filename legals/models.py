from django.db import models
from storybook.utils.models import DefaultFields
from django.utils.text import slugify
import os



LEGAL_TYPE_CHOICES = [("terms", "Terms & Conditions"), ("privacy", "Privacy Policy"), ("cookies", "Cookie Policy")]

class LegalContent(DefaultFields):
    type = models.CharField(max_length=20, choices=LEGAL_TYPE_CHOICES, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        db_table = "legals"
        ordering = ["type"]

    def __str__(self):
        return self.get_type_display()



def logo_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    company_slug = slugify(instance.company)
    return f'websites/{company_slug}/logo{ext}'


def header_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    company_slug = slugify(instance.company)
    return f'websites/{company_slug}/header{ext}'


def footer_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    company_slug = slugify(instance.company)
    return f'websites/{company_slug}/footer{ext}'


def signature_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    company_slug = slugify(instance.company)
    return f'websites/{company_slug}/signature{ext}'



class Website(DefaultFields):
    company = models.CharField(max_length=255, unique=True, help_text="Enter the name of the company.")
    domain = models.CharField(max_length=255, help_text="Enter the name of the domain (e.g. www.littlestorybox.com).")
    website = models.URLField(max_length=500, help_text="Enter the website domain (e.g., https://littlestorybox.com).")
    email = models.EmailField(max_length=255, blank=True, null=True, help_text="Enter the contact email address.")
    mobile = models.CharField(max_length=20, blank=True, null=True, help_text="Enter the contact mobile number (e.g., +1234567890).")
    address = models.TextField(blank=True, null=True, help_text="Enter the company or website address.")
    logo = models.ImageField(upload_to=logo_upload_path, blank=True, null=True, help_text="Upload the company or website logo.")
    header = models.ImageField(upload_to=header_upload_path, blank=True, null=True, help_text="Upload the header image for the website.")
    footer = models.ImageField(upload_to=footer_upload_path, blank=True, null=True, help_text="Upload the footer image for the website.")
    signature = models.ImageField(upload_to=signature_upload_path, blank=True, null=True, help_text="Upload the signature image.")
    recaptcha_site_key = models.CharField(max_length=255, blank=True, null=True, help_text="Google reCAPTCHA site key")
    recaptcha_secret_key = models.CharField(max_length=255, blank=True, null=True, help_text="Google reCAPTCHA secret key")
    smtp_host = models.CharField(max_length=255, blank=True, null=True, help_text="SMTP host (e.g., smtp.gmail.com)")
    smtp_port = models.PositiveIntegerField(blank=True, null=True, help_text="SMTP port (e.g., 587)")
    smtp_username = models.CharField(max_length=255, blank=True, null=True, help_text="SMTP username/email")
    smtp_password = models.CharField(max_length=255, blank=True, null=True, help_text="SMTP password")
    smtp_use_tls = models.BooleanField(default=True, help_text="Use TLS for SMTP")
    
    api_key = models.CharField(max_length=500, blank=True, null=True, help_text="General API key")
    api_secret = models.CharField(max_length=500, blank=True, null=True, help_text="General API secret")
    
    payment_gateway = models.CharField(max_length=50, blank=True, null=True, help_text="Payment gateway (e.g., Stripe, PayPal, Razorpay)")
    payment_key = models.CharField(max_length=500, blank=True, null=True, help_text="Payment gateway public/publishable key")
    payment_secret = models.CharField(max_length=500, blank=True, null=True, help_text="Payment gateway secret key")
    
    sms_provider = models.CharField(max_length=50, blank=True, null=True, help_text="SMS provider (e.g., Twilio)")
    sms_api_key = models.CharField(max_length=255, blank=True, null=True, help_text="SMS API key")
    sms_api_secret = models.CharField(max_length=255, blank=True, null=True, help_text="SMS API secret")
    sms_sender_id = models.CharField(max_length=50, blank=True, null=True, help_text="SMS sender ID")
    
    google_analytics_id = models.CharField(max_length=50, blank=True, null=True, help_text="Google Analytics tracking ID")
    facebook_pixel_id = models.CharField(max_length=50, blank=True, null=True, help_text="Facebook Pixel ID")
    
    social_facebook = models.URLField(max_length=500, blank=True, null=True, help_text="Facebook page URL")
    social_twitter = models.URLField(max_length=500, blank=True, null=True, help_text="Twitter/X profile URL")
    social_instagram = models.URLField(max_length=500, blank=True, null=True, help_text="Instagram profile URL")
    social_linkedin = models.URLField(max_length=500, blank=True, null=True, help_text="LinkedIn profile URL")
    social_youtube = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube channel URL")
    
    maintenance_mode = models.BooleanField(default=False, help_text="Enable maintenance mode")
    maintenance_message = models.TextField(blank=True, null=True, help_text="Maintenance mode message")
    
    class Meta:
        db_table = 'websites'
    
    def __str__(self):
        return self.company
    
    @property
    def base_url(self):
        return self.website.rstrip('/')

    def _full_url(self, field):
        if field and field.url:
            return f"{self.base_url}{field.url}"
        return None

    @property
    def logo_url(self):
        return self._full_url(self.logo)

    @property
    def header_url(self):
        return self._full_url(self.header)

    @property
    def footer_url(self):
        return self._full_url(self.footer)

    @property
    def signature_url(self):
        return self._full_url(self.signature)