import traceback
import uuid

from django.conf import settings
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from django.contrib import messages

from logs.models import Log
from legals.models import Website


def send_verification_email(request, user):
    profile = user.profile

    try:
        with transaction.atomic():
            token = uuid.uuid4().hex
            profile.email_token = token
            profile.email_verified = False
            profile.email_verified_at = None
            profile.save(update_fields=["email_token", "email_verified", "email_verified_at"])

            base_url = request.build_absolute_uri("/")[:-1]
            verify_url = base_url + reverse("user_verify_email", args=[token])

            website = Website.objects.filter(is_active=True).first()
            if not website:
                raise ValueError("No active website found")

            html_content = render_to_string(
                "accounts/emails/verification.html",
                {
                    "user": user,
                    "verify_url": verify_url,
                    "website": website,
                }
            )

            subject = "Verify your email address"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email, website.email]

            email = EmailMultiAlternatives(subject, "", from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send()

    except Exception as e:
        Log.objects.create(
            title="Verification Email Error",
            type="error",
            message=f"{user.email}: {str(e)}",
        )


def send_verified_email(user):
    website = Website.objects.filter(is_active=True).first()

    try:
        html_content = render_to_string(
            "accounts/emails/verified.html",
            {
                "user": user,
                "website": website,
            }
        )

        subject = "Your email has been verified"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email, website.email]

        email = EmailMultiAlternatives(subject, "", from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()

    except Exception as e:
        Log.objects.create(
            title="Verified Email Send Error",
            type="error",
            message=f"{user.email}: {str(e)}",
        )


def send_forgot_password_email(request, user):
    profile = user.profile

    try:
        with transaction.atomic():
            token = uuid.uuid4().hex
            profile.email_token = token
            profile.email_verified_at = timezone.now()
            profile.save(update_fields=["email_token", "email_verified_at"])

            base_url = request.build_absolute_uri("/")[:-1]
            reset_url = base_url + reverse("user_set_password", args=[token])

            website = Website.objects.filter(is_active=True).first()
            if not website:
                raise ValueError("No active website found")

            html_content = render_to_string(
                "accounts/emails/passwordforgot.html",
                {
                    "user": user,
                    "reset_url": reset_url,
                    "website": website,
                    "expiry_hours": 24,
                }
            )

            subject = "Password Reset Request"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email, website.email]

            email = EmailMultiAlternatives(subject, "", from_email, to_email)
            email.attach_alternative(html_content, "text/html")
            email.send()

    except Exception as e:
        Log.objects.create(
            title="Forgot Password Email Error",
            type="error",
            message=f"{user.email}: {str(e)}",
        )
        raise


def send_password_reset_success_email(user):
    profile = user.profile

    try:
        website = Website.objects.filter(is_active=True).first()

        html_content = render_to_string(
            "accounts/emails/passwordchanged.html",
            {
                "user": user,
                "website": website,
            }
        )

        subject = "Your password has been reset successfully"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email, website.email]

        email = EmailMultiAlternatives(subject, "", from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()

        profile.email_token = None
        profile.save(update_fields=["email_token"])

    except Exception as e:
        Log.objects.create(
            title="Password Reset Success Email Error",
            type="error",
            message=f"{user.email}: {str(e)}",
        )
        raise


def send_story_purchase_email(user, story):
    website = Website.objects.filter(is_active=True).first()

    try:
        html_content = render_to_string(
            "accounts/emails/storypurchase.html",
            {
                "user": user,
                "story": story,
                "website": website,
            }
        )

        subject = f"Purchase Confirmed: {story.title}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [user.email, website.email]

        email = EmailMultiAlternatives(subject, "", from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send()

    except Exception as e:
        Log.objects.create(
            title="Story Purchase Email Send Error",
            type="error",
            message=f"{user.email} - Story: {story.title} - Error: {str(e)}",
        )


def send_referral_reward_email(referrer, referred_user, tokens=100):
    website = Website.objects.filter(is_active=True).first()

    if not website or not website.email or not referrer.email:
        return False

    try:
        html_content = render_to_string(
            "accounts/emails/referral_reward_email.html",
            {
                "user": referrer,
                "referred_user": referred_user,
                "tokens": tokens,
                "website": website,
            }
        )

        subject = f"You Earned {tokens} Tokens from Your Referral"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [referrer.email, website.email]

        email = EmailMultiAlternatives(subject, "", from_email, to_email)
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        return True

    except Exception as e:
        Log.objects.create(
            title="Referral Reward Email Send Error",
            type="error",
            message=(
                f"Referrer: {referrer.email} | "
                f"Referred: {getattr(referred_user, 'email', 'N/A')} | "
                f"Error: {str(e)}"
            ),
        )
        return False
