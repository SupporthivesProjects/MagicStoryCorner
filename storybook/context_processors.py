
from django.conf import settings
from stories.models import (
    AIModel, ChildAgeRange, StorySetting, StoryPlot, StoryTheme,
    StoryTone, StoryLength, ImageStyle, LanguageOption, NarratorVoice,
    StoryEnd, StoryBook, StoryBookPage
)
from accounts.models import Profile
from pages.models import Contact
from payments.models import (
    Coupon, PackageType, Package, Order, OrderItem, PaymentTransaction
)
from products.models import ProductBook, ProductBookPage, ProductBookPurchase
from legals.models import Website

from django.contrib.auth import get_user_model

User = get_user_model()

def model_counts(request):
    return {
        'ai_model_count': AIModel.objects.count(),
        'age_range_count': ChildAgeRange.objects.count(),
        'story_setting_count': StorySetting.objects.count(),
        'story_plot_count': StoryPlot.objects.count(),
        'story_theme_count': StoryTheme.objects.count(),
        'story_tone_count': StoryTone.objects.count(),
        'story_length_count': StoryLength.objects.count(),
        'image_style_count': ImageStyle.objects.count(),
        'language_count': LanguageOption.objects.count(),
        'narrator_voice_count': NarratorVoice.objects.count(),
        'story_end_count': StoryEnd.objects.count(),
        'storybook_count': StoryBook.objects.count(),
        'storybook_page_count': StoryBookPage.objects.count(),
        'storybook_pending_count': StoryBook.objects.filter(status='pending').count(),
        'storybook_completed_count': StoryBook.objects.filter(status='completed').count(),
        'storybook_failed_count': StoryBook.objects.filter(status='failed').count(),
        'coupon_count': Coupon.objects.count(),
        'package_type_count': PackageType.objects.count(),
        'package_count': Package.objects.count(),
        'order_count': Order.objects.count(),
        'order_item_count': OrderItem.objects.count(),
        'payment_transaction_count': PaymentTransaction.objects.count(),
        'product_book_count': ProductBook.objects.count(),
        'product_pending_count': ProductBook.objects.filter(status='pending').count(),
        'product_completed_count': ProductBook.objects.filter(status='completed').count(),
        'product_failed_count': ProductBook.objects.filter(status='failed').count(),
        'product_book_page_count': ProductBookPage.objects.count(),
        'product_book_purchase_count': ProductBookPurchase.objects.count(),
        'total_users_count': User.objects.filter(is_staff=False, is_superuser=False).count(),
    }


def white_header(request):
    header_white_pages = [ 'error_404','error_500','error_403','error_400'
        'privacy_policy', 'terms_conditions', 'library_list', 'purchase_history', 'cookies_policy','user_login','user_verify_email','user_set_password','user_forgot_password','user_verification_pending','resend_verification','user_register', 'user_dashboard', 'howItWorks', 'contactUs',
        'billing_information', 'order_summary',
        'payment', 'about','payment_success', 'payment_failed','product_book_list','story_book_view','library_view','purchase_history','product_book_view_purchased',
    ]
    return {
        'header_white_pages': header_white_pages
    }

def story_header(request):
    story_pages = ['story_book_create','story_book_view','story_book_download']
    return {
        'story_header_pages': story_pages
    }

def get_active_website(request):
    website = Website.objects.filter(is_active=True).first()
    
    if not website:
        return {
            'site_name': '',
            'website': None,
            'RECAPTCHA_PUBLIC_KEY': getattr(settings, 'RECAPTCHA_PUBLIC_KEY', ''),
        }
    
    return {
        'site_name': website.company,
        'website': website,
        'site_domain': website.domain,
        'site_url': website.website,
        'site_email': website.email,
        'site_mobile': website.mobile,
        'site_address': website.address,
        'site_logo': website.logo_url if website.logo_url else '',
        'site_header': website.header_url if website.header_url else '',
        'site_footer': website.footer_url if website.footer_url else '',
        'site_signature': website.signature_url if website.signature_url else '',
        'RECAPTCHA_PUBLIC_KEY': website.recaptcha_site_key or getattr(settings, 'RECAPTCHA_PUBLIC_KEY', ''),
        'RECAPTCHA_SECRET_KEY': website.recaptcha_secret_key or getattr(settings, 'RECAPTCHA_SECRET_KEY', ''),
        'GOOGLE_ANALYTICS_ID': website.google_analytics_id,
        'FACEBOOK_PIXEL_ID': website.facebook_pixel_id,
        'social_links': {
            'facebook': website.social_facebook,
            'twitter': website.social_twitter,
            'instagram': website.social_instagram,
            'linkedin': website.social_linkedin,
            'youtube': website.social_youtube,
        },
        'maintenance_mode': website.maintenance_mode,
        'maintenance_message': website.maintenance_message,
    }

