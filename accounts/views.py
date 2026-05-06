from datetime import datetime
from io import BytesIO
from pathlib import Path

import asyncio
import base64
import os
import re
import subprocess
import tempfile
import time
import requests
from PIL import Image
import openai

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files import File
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Max, Q
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from playwright.async_api import async_playwright
from rest_framework.authtoken.models import Token
# from weasyprint import HTML, CSS

from accounts.decorators import login_required, verified_required
from legals.models import Website
from logs.models import Log
from payments.models import *
from products.builder import ProductBookBuilder
from products.models import *
from stories.helper.views import get_story_options
from stories.models import *
from .models import Profile
from django.core.paginator import Paginator
from django.db.models import Q, Count
from accounts.emails.helpers import send_forgot_password_email, send_password_reset_success_email, send_verification_email, send_verified_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from accounts.models import DailyClaim, Wallet, ReferralCode, Referral
from django.utils import timezone
from django.shortcuts import redirect
from payments.models import Currency
from accounts.models import Profile
from rest_framework.authtoken.models import Token
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from accounts.context_processors import loggedin_user


@require_http_methods(["POST"])
def set_currency(request):
    code = request.POST.get("currency")

    if not code:
        return redirect(request.META.get("HTTP_REFERER", "/"))

    currency = Currency.objects.filter(code__iexact=code.strip()).first()
    if not currency:
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # 🔥 Get user from your auth system
    user = loggedin_user(request).get("logged_in_user")

    # ✅ Save in profile (only if user exists)
    if user:
        profile = Profile.objects.filter(user=user).first()
        if profile:
            profile.currency = currency
            profile.save()
    messages.success(request, "Currency changed successfully")

    # ✅ Always save in session
    request.session["currency"] = currency.code

    return redirect(request.META.get("HTTP_REFERER", "/"))
# def set_currency(request):
#     code = request.POST.get("currency")

#     if not code:
#         return redirect(request.META.get("HTTP_REFERER", "/"))

#     currency = Currency.objects.filter(code__iexact=code.strip()).first()
#     if not currency:
#         raise Exception("CURRENCY NOT FOUND")

#     # 🔥 Get user
#     user = loggedin_user(request).get("logged_in_user")
#     if not user:
#         raise Exception("USER NOT FOUND")

#     # 🔥 Get profile AFTER user
#     profile = Profile.objects.filter(user=user).first()
#     if not profile:
#         raise Exception("PROFILE NOT FOUND")

#     # ✅ Save
#     profile.currency = currency
#     profile.save()

#     # ✅ Session
#     request.session["currency"] = currency.code

#     return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@require_http_methods(["GET"])
def get_referral_code(request):
    try:
        ref_code, created = ReferralCode.objects.get_or_create(
            user=request.user,
            defaults={'code': ReferralCode.generate()}
        )
        
        return JsonResponse({
            'success': True,
            'code': ref_code.code,
            'link': ref_code.get_link(),
            'referral_count': ref_code.referral_count,
            'tokens_earned': ref_code.tokens_earned
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate referral code'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_referral_stats(request):
    try:
        ref_code, created = ReferralCode.objects.get_or_create(
            user=request.user,
            defaults={'code': ReferralCode.generate()}
        )
        
        pending_referrals = Referral.objects.filter(
            referrer=request.user, 
            purchased=True, 
            rewarded=False
        ).count()
        
        total_referrals = Referral.objects.filter(referrer=request.user).count()
        
        return JsonResponse({
            'success': True,
            'referral_count': ref_code.referral_count,
            'tokens_earned': ref_code.tokens_earned,
            'pending_referrals': pending_referrals,
            'total_referrals': total_referrals
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch referral stats'
        }, status=500)


@require_http_methods(["GET"])
def validate_referral_code(request):
    code = request.GET.get('ref', '').strip().upper()
    
    if not code:
        return JsonResponse({
            'success': True,
            'valid': False,
            'message': 'No referral code provided'
        })
    
    if request.user.is_authenticated:
        try:
            existing_referral = Referral.objects.get(referred=request.user)
            return JsonResponse({
                'success': False,
                'valid': False,
                'error': 'You have already been referred by someone'
            })
        except Referral.DoesNotExist:
            pass
    
    try:
        ref_code = ReferralCode.objects.select_related('user').get(code=code)
        
        if request.user.is_authenticated and ref_code.user == request.user:
            return JsonResponse({
                'success': False,
                'valid': False,
                'error': 'You cannot use your own referral code'
            })
        
        return JsonResponse({
            'success': True,
            'valid': True,
            'referrer': ref_code.user.first_name or ref_code.user.username,
            'code': ref_code.code
        })
    except ReferralCode.DoesNotExist:
        return JsonResponse({
            'success': False,
            'valid': False,
            'error': 'Invalid referral code'
        })


@login_required
@require_http_methods(["POST"])
def claim_daily_reward(request):
    try:
        user = request.user
        daily_claim, created = DailyClaim.objects.get_or_create(user=user)
        
        if not daily_claim.can_claim():
            return JsonResponse({
                'success': False,
                'error': 'You have already claimed your reward today. Come back tomorrow!'
            })
        
        reward_tokens = 20
        
        user.profile.wallet += reward_tokens
        user.profile.save()
        current_balance = user.profile.wallet
        Wallet.objects.create(
            user=user,
            type='recharge',
            amount=reward_tokens,
            balance=current_balance,
            message="Daily reward claimed"
        )

        
        daily_claim.last_claim = timezone.now()
        daily_claim.claim_count += 1
        daily_claim.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Congratulations! You earned {reward_tokens} tokens!',
            'tokens': reward_tokens,
            'new_balance': user.profile.wallet,
            'claim_count': daily_claim.claim_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while claiming your reward. Please try again.'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def check_claim_status(request):
    try:
        user = request.user
        daily_claim = DailyClaim.objects.filter(user=user).first()
        
        if not daily_claim:
            can_claim = True
            claim_count = 0
            last_claim = None
        else:
            can_claim = daily_claim.can_claim()
            claim_count = daily_claim.claim_count
            last_claim = daily_claim.last_claim.isoformat() if daily_claim.last_claim else None
        
        return JsonResponse({
            'success': True,
            'can_claim': can_claim,
            'claim_count': claim_count,
            'last_claim': last_claim,
            'current_balance': user.profile.wallet
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while checking claim status.'
        }, status=500)


def user_register(request):
    if request.session.get("auth_token"):
        messages.info(request, "You are already logged in.")
        return redirect("user_dashboard")
    
    if request.method == "POST":
        fullname = request.POST.get("fullname", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        website = Website.objects.filter(is_active=True).first()

        if not fullname:
            messages.error(request, "Full name is required.")
            return redirect("user_register")
        if not email:
            messages.error(request, "Email is required.")
            return redirect("user_register")
        if not password:
            messages.error(request, "Password is required.")
            return redirect("user_register")
        if not confirm_password:
            messages.error(request, "Please confirm your password.")
            return redirect("user_register")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("user_register")

        if User.objects.filter(Q(username=email) | Q(email=email)).exists():
            messages.error(request, "Email is already registered.")
            return redirect("user_register")

        recaptcha_response = request.POST.get("g-recaptcha-response", "")
        if not recaptcha_response:
            messages.error(request, "reCAPTCHA verification is required.")
            return redirect("user_register")

        try:
            verify = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": website.recaptcha_secret_key,
                    "response": recaptcha_response
                }
            )
            result = verify.json()
            if not result.get("success"):
                messages.error(request, "Invalid reCAPTCHA. Please try again.")
                return redirect("user_register")
        except requests.RequestException:
            messages.error(request, "Unable to verify reCAPTCHA. Try again later.")
            return redirect("user_register")

        try:
            with transaction.atomic():
                username = email.split("@")[0]

                if User.objects.filter(username=username).exists():
                    username = f"{username}_{User.objects.count()+1}"

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )

                parts = fullname.strip().split(" ", 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ""
                user.save()

                Profile.objects.get_or_create(user=user)

                token, _ = Token.objects.get_or_create(user=user)
                request.session["auth_token"] = token.key

                send_verification_email(request, user)

                messages.success(request, "Registration successful. Check your email to verify your account.")
                return redirect("user_verification_pending")
                
        except IntegrityError as e:
            messages.error(request, "Registration failed due to a system error.")
            Log.objects.create(title="Registration error", type="error", message=str(e))
            return redirect("user_register")
        except Exception as e:
            messages.error(request, "Unexpected error occurred.")
            Log.objects.create(title="Unexpected Registration Exception", type="error", message=str(e))
            return redirect("user_register")

    return render(request, "accounts/users/register.html")





@login_required
def resend_verification_view(request):
    if request.method == 'POST':
        send_verification_email(request, request.user)
        messages.success(request, "Email verification link has been sent successfully.")
        return redirect('user_verification_pending')
    return redirect('user_verification_pending')

@login_required
def user_verification_pending(request):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.email_verified:
        return redirect("user_dashboard")

    context = {
        "email": request.user.email
    }
    return render(request, "accounts/users/verify.html", context)



def user_verify_email(request, token):
    try:
        profile = Profile.objects.get(email_token=token)
    except Profile.DoesNotExist:
        messages.error(request, "Invalid or expired verification link.")
        return redirect("user_login")

    try:
        profile.email_verified = True
        profile.email_verified_at = timezone.now()
        profile.email_token = None
        profile.save(update_fields=["email_verified", "email_verified_at", "email_token"])
        send_verified_email(profile.user)
        messages.success(request, "Your email has been verified successfully.")
        return redirect("user_login")

    except Exception as e:
        Log.objects.create(title="Email Verification Error", type="error",message=str(e))
        messages.error(request, "Something went wrong while verifying your email.")
        return redirect("user_login")


def user_login(request):
    if request.session.get("auth_token"):
        messages.info(request, "You are already logged in.")
        return redirect("user_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        
        if not username or not password:
            messages.error(request, "Please provide both email/username and password.")
            return redirect("user_login")
        
        try:
            user_obj = User.objects.filter(
                Q(email__iexact=username) | Q(username__iexact=username)
            ).first()
            
            if not user_obj or not user_obj.is_active or user_obj.is_staff:
                messages.error(request, "Invalid email/username or password.")
                return redirect("user_login")

            user = authenticate(request, username=user_obj.username, password=password)
            
            if not user:
                messages.error(request, "Invalid email/username or password.")
                return redirect("user_login")

            token, _ = Token.objects.get_or_create(user=user)
            request.session["auth_token"] = token.key
            
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect("user_dashboard")

        except Exception as e:
            messages.error(request, "An error occurred during login.")
            Log.objects.create(
                title="Login Exception", 
                type="error", 
                message=f"Username: {username}, IP: {request.META.get('REMOTE_ADDR')}, Error: {str(e)}"
            )
            return redirect("user_login")

    return render(request, "accounts/users/login.html")


@login_required
@verified_required
def user_dashboard(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('ajax') == 'true'
    
    if is_ajax:
        page_number = request.GET.get('page', 1)
        orders = request.user.orders.prefetch_related('items__package__packagetype').order_by('-created_at')
        
        paginator = Paginator(orders, 10)
        page_obj = paginator.get_page(page_number)
        
        orders_data = []
        for order in page_obj:
            items_data = []
            for item in order.items.all():
                items_data.append({
                    'package': {
                        'packagetype': {
                            'name': item.package.packagetype.name
                        }
                    }
                })
            
            orders_data.append({
                'id': order.id,
                'created_at': order.created_at.isoformat(),
                'items': items_data,
                'currency': order.currency,
                'total': str(order.total)
            })
        
        return JsonResponse({
            'orders': orders_data,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        })
    
    user_stories = StoryBook.objects.filter(user=request.user, is_active=True).order_by('-id')[:4]
    orders_list = Order.objects.filter(user=request.user).prefetch_related("items").order_by('-id')
    paginator = Paginator(orders_list, 10) 
    page_number = request.GET.get('page', 1)
    orders_page = paginator.get_page(page_number)
    
    return render(request, "accounts/users/dashboard.html", {
        "stories": user_stories,
        "orders": orders_page    
    })


@login_required
def user_update_profile(request):
    if request.method == "POST":
        try:
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            user = request.user
            profile = user.profile
            user.first_name = request.POST.get("first_name", user.first_name)
            user.last_name = request.POST.get("last_name", user.last_name)
            user.email = request.POST.get("email", user.email)
            user.save()
            profile.line_1 = request.POST.get("line_1", profile.line_1)
            profile.line_2 = request.POST.get("line_2", profile.line_2)
            profile.city = request.POST.get("city", profile.city)
            profile.postal = request.POST.get("postal", profile.postal)
            profile.save()
            
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Profile updated successfully'})
            
            messages.success(request, "Profile updated successfully!")
            return redirect("user_dashboard")
        except Exception as e:
            Log.objects.create(title="Profile Update Failed", type="error", message=f"User {request.user.email}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            messages.error(request, "Failed to update profile.")
            return redirect("user_dashboard")
    
    return redirect("user_dashboard")


@login_required
def user_password_update(request):
    if request.method == "POST":
        try:
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            user = request.user
            current_password = request.POST.get("current_password")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if not check_password(current_password, user.password):
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Current password is incorrect.'}, status=400)
                messages.error(request, "Current password is incorrect.")
                return redirect("user_dashboard")

            if new_password != confirm_password:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'New password and confirm password do not match.'}, status=400)
                messages.error(request, "New password and confirm password do not match.")
                return redirect("user_dashboard")

            if not new_password:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'New password cannot be empty.'}, status=400)
                messages.error(request, "New password cannot be empty.")
                return redirect("user_dashboard")

            user.set_password(new_password)
            user.save()
            
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Password updated successfully'})
            
            messages.success(request, "Password updated successfully!")
            return redirect("user_dashboard")
        except Exception as e:
            Log.objects.create(title="Password Update Failed", type="error", message=f"User {request.user.email}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            messages.error(request, "Failed to update password.")
            return redirect("user_dashboard")
    
    return redirect("user_dashboard")


def user_forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, "Please enter your email address.")
            return redirect('user_forgot_password')
        
        try:
            user = User.objects.get(email=email)
            send_forgot_password_email(request, user)
            
        except User.DoesNotExist:
            pass
        
        messages.info(request, "If this email exists in our system, you will receive a password reset link.")
        return redirect('user_forgot_password')
    
    return render(request, 'accounts/passwords/forgot.html')


def user_set_password(request, token):
    try:
        profile = Profile.objects.get(email_token=token)
        user = profile.user
        
        if not profile.email_verified_at:
            messages.error(request, "Invalid password reset link.")
            return redirect('user_login')
        
        token_age = timezone.now() - profile.email_verified_at
        if token_age.total_seconds() > 86400:
            messages.error(request, "Password reset link has expired. Please request a new one.")
            return redirect('user_forgot_password')
        
        if request.method == 'POST':
            password = request.POST.get('password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            
            if not password or not confirm_password:
                messages.error(request, "Please enter both passwords.")
                return render(request, 'accounts/passwords/setnew.html', {'token': token})
            
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, 'accounts/passwords/setnew.html', {'token': token})
            
            if len(password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, 'accounts/passwords/setnew.html', {'token': token})
            
            try:
                with transaction.atomic():
                    user.set_password(password)
                    user.save()
                    
                    profile.email_token = None
                    profile.save(update_fields=["email_token"])
                    
                    send_password_reset_success_email(user)
                    
                    messages.success(request, "Your password has been reset successfully. Please login.")
                    return redirect('user_login')
                    
            except Exception as e:
                
                messages.error(request, "An error occurred while resetting password.")
                
                Log.objects.create(title="Password Reset Error", type="error",message=f"{user.email}: {str(e)}")
                
                return render(request, 'accounts/passwords/setnew.html', {'token': token})
        
        return render(request, 'accounts/passwords/setnew.html', {'token': token})
        
    except Profile.DoesNotExist:
        
        messages.error(request, "Invalid password reset link.")
        
        return redirect('user_login')
    
    
    
def user_logout(request):
    token_key = request.session.get("auth_token")
    if token_key:
        Token.objects.filter(key=token_key).delete()
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect("home")


@login_required
@verified_required
def library_list(request):
    base_stories = StoryBook.objects.filter(status="completed", user=request.user)

    stories = base_stories

    search_query = request.GET.get("search")
    if search_query:
        stories = stories.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

    filter_mapping = {
        "age": "agegroup__name__in",
        "story_type": "plot__name__in",
        "theme": "theme__name__in",
        "narration": "narrator__name__in",
        "style": "imagestyle__name__in",
    }

    filters = {field: request.GET.getlist(param) for param, field in filter_mapping.items() if request.GET.getlist(param)}
    if filters:
        stories = stories.filter(**filters)

    sort_by = request.GET.get("sort")
    if sort_by == "date_asc":
        stories = stories.order_by("created_at")
    else:
        stories = stories.order_by("-created_at")

    per_page_cards = 8
    paginator = Paginator(stories, per_page_cards)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    ages = ChildAgeRange.objects.annotate(
        story_count=Count("storybook", filter=Q(storybook__in=base_stories), distinct=True)
    ).order_by("-story_count")[:4]

    story_types = StoryPlot.objects.annotate(
        story_count=Count("storybook", filter=Q(storybook__in=base_stories), distinct=True)
    ).order_by("-story_count")[:4]

    themes = StoryTheme.objects.annotate(
        story_count=Count("storybook", filter=Q(storybook__in=base_stories), distinct=True)
    ).order_by("-story_count")[:4]

    narrations = NarratorVoice.objects.annotate(
        story_count=Count("storybook", filter=Q(storybook__in=base_stories), distinct=True)
    ).order_by("-story_count")[:4]

    styles = ImageStyle.objects.annotate(
        story_count=Count("storybook", filter=Q(storybook__in=base_stories), distinct=True)
    ).order_by("-story_count")[:4]

    context = {
        "per_page_cards": range(per_page_cards),
        "stories": page_obj,
        "page_obj": page_obj,
        "ages": ages,
        "story_types": story_types,
        "themes": themes,
        "narrations": narrations,
        "styles": styles,
        "selected_filters": {k: request.GET.getlist(k) for k in filter_mapping},
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("accounts/library/cards.html", {"stories": page_obj})
        pagination_html = render_to_string("accounts/library/pagination.html", {"page_obj": page_obj})
        return JsonResponse({
            "html": html,
            "pagination_html": pagination_html,
            "start_index": page_obj.start_index(),
            "end_index": page_obj.end_index(),
            "total_count": page_obj.paginator.count
        })

    return render(request, "accounts/library/library_list.html", context)




@login_required
@verified_required
def purchase_history(request):
    base_books = (
        ProductBook.objects
        .filter(
            id__in=ProductBookPurchase.objects.filter(user=request.user).values_list('book_id', flat=True),
            status="completed",
            pages__image__isnull=False
        )
        .exclude(pages__image="")
        .distinct()
    )

    stories = base_books

    search_query = request.GET.get("search")
    if search_query:
        stories = stories.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))

    filter_mapping = {
        "age": "agegroup__name__in",
        "story_type": "plot__name__in",
        "theme": "theme__name__in",
        "narration": "narrator__name__in",
        "style": "imagestyle__name__in",
    }

    filters = {field: request.GET.getlist(param) for param, field in filter_mapping.items() if request.GET.getlist(param)}
    if filters:
        stories = stories.filter(**filters)

    purchase_dates = dict(ProductBookPurchase.objects.filter(user=request.user).values_list('book_id', 'created_at'))
    stories_list = list(stories)

    sort_by = request.GET.get("sort")
    if sort_by == "date_asc":
        stories_list.sort(key=lambda x: purchase_dates.get(x.id))
    else:
        stories_list.sort(key=lambda x: purchase_dates.get(x.id), reverse=True)

    per_page_cards = 8
    paginator = Paginator(stories_list, per_page_cards)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    ages = ChildAgeRange.objects.annotate(
        story_count=Count("productbook", filter=Q(productbook__in=base_books), distinct=True)
    ).order_by("-story_count")[:4]

    story_types = StoryPlot.objects.annotate(
        story_count=Count("productbook", filter=Q(productbook__in=base_books), distinct=True)
    ).order_by("-story_count")[:4]

    themes = StoryTheme.objects.annotate(
        story_count=Count("productbook", filter=Q(productbook__in=base_books), distinct=True)
    ).order_by("-story_count")[:4]

    narrations = NarratorVoice.objects.annotate(
        story_count=Count("productbook", filter=Q(productbook__in=base_books), distinct=True)
    ).order_by("-story_count")[:4]

    styles = ImageStyle.objects.annotate(
        story_count=Count("productbook", filter=Q(productbook__in=base_books), distinct=True)
    ).order_by("-story_count")[:4]

    context = {
        "per_page_cards": range(per_page_cards),
        "stories": page_obj,
        "page_obj": page_obj,
        "ages": ages,
        "story_types": story_types,
        "themes": themes,
        "narrations": narrations,
        "styles": styles,
        "selected_filters": {k: request.GET.getlist(k) for k in filter_mapping},
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("accounts/purchases/cards.html", {"stories": page_obj})
        pagination_html = render_to_string("accounts/purchases/pagination.html", {"page_obj": page_obj})
        return JsonResponse({
            "html": html,
            "pagination_html": pagination_html,
            "start_index": page_obj.start_index(),
            "end_index": page_obj.end_index(),
            "total_count": page_obj.paginator.count
        })

    return render(request, "accounts/purchases/purchase_history.html", context)



def product_book_view_purchased(request, slug):
    story = ProductBook.objects.filter(slug=slug).order_by("-created_at").first()
    if not story:
        messages.error(request, "Story not found.")
        return redirect("product_book_list")

    is_purchased = False
    user = None
    
    token_key = request.session.get("auth_token")
    if token_key:
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
            if user.is_active and not user.is_staff:
                is_purchased = ProductBookPurchase.objects.filter(
                    user=user,
                    book=story
                ).exists()
        except Token.DoesNotExist:
            pass
    

    if not is_purchased:
        messages.error(request, "You need to purchase this book to view it.")
        return redirect("product_book_list")

    return render(request, "accounts/purchases/book_view.html", {"book": story})

@login_required
@verified_required
def library_view(request, slug):
    book = get_object_or_404(StoryBook, slug=slug)
    return render(request, 'accounts/library/library_view.html', {'book': book})


