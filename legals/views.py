from django.shortcuts import render, get_object_or_404, redirect
from .models import LegalContent
from django.contrib import messages

def cookies_policy(request):
    legal_content = LegalContent.objects.filter(type='cookies', is_active=True).first()
    if not legal_content:
        messages.error(request, 'Cookies policy is currently unavailable.')
        return redirect(request.META.get('HTTP_REFERER', request.path))

    return render(request, 'legals/cookies_policy.html', {
        'legal': legal_content,
        'page_title': legal_content.get_type_display()
    })


def terms_conditions(request):
    legal_content = LegalContent.objects.filter(type='terms', is_active=True).first()
    if not legal_content:
        messages.error(request, 'Terms & Conditions are currently unavailable.')
        return redirect(request.META.get('HTTP_REFERER', request.path))

    return render(request, 'legals/terms_conditions.html', {
        'legal': legal_content,
        'page_title': legal_content.get_type_display()
    })


def privacy_policy(request):
    legal_content = LegalContent.objects.filter(type='privacy', is_active=True).first()
    if not legal_content:
        messages.error(request, 'Privacy Policy is currently unavailable.')
        return redirect(request.META.get('HTTP_REFERER', request.path))

    return render(request, 'legals/privacy_policy.html', {
        'legal': legal_content,
        'page_title': legal_content.get_type_display()
    })
