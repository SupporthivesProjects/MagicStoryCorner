from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from legals.models import LegalContent, Website


def legal_list(request):
    legal_contents = LegalContent.objects.all()
    return render(request, 'demos/legals/legal_content.html', {'legal_contents': legal_contents})


@require_http_methods(["GET"])
def legal_get(request, pk):
    legal = get_object_or_404(LegalContent, pk=pk)
    return JsonResponse({
        'id': legal.id,
        'type': legal.type,
        'title': legal.title,
        'content': legal.content,
        'is_active': legal.is_active,
        'created_at': legal.created_at.isoformat(),
        'updated_at': legal.updated_at.isoformat()
    })

import json

@require_http_methods(["POST"])
def legal_create(request):
    try:
        data = json.loads(request.body)
        type_value = data.get('type')
        title = data.get('title')
        content = data.get('content')
        is_active = data.get('is_active', False)

        if not type_value or not title or not content:
            return JsonResponse({'success': False, 'error': 'All fields are required'}, status=400)

        legal = LegalContent.objects.create(
            type=type_value,
            title=title,
            content=content,
            is_active=is_active
        )

        return JsonResponse({'success': True, 'message': 'Legal content created successfully!', 'id': legal.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def legal_update(request, pk):
    try:
        legal = get_object_or_404(LegalContent, pk=pk)
        
        data = json.loads(request.body)
        type_value = data.get('type')
        title = data.get('title')
        content = data.get('content')
        is_active = data.get('is_active', False)

        if not type_value or not title or not content:
            return JsonResponse({'success': False, 'error': 'All fields are required'}, status=400)

        legal.type = type_value
        legal.title = title
        legal.content = content
        legal.is_active = is_active
        legal.save()

        return JsonResponse({'success': True, 'message': 'Legal content updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def legal_delete(request, pk):
    try:
        legal = get_object_or_404(LegalContent, pk=pk)
        legal.delete()
        return JsonResponse({'success': True, 'message': 'Legal content deleted successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def website_list(request):
    websites = Website.objects.all()
    return render(request, 'demos/legals/websites.html', {'websites': websites})


@require_http_methods(["GET"])
def website_get(request, pk):
    website = get_object_or_404(Website, pk=pk)
    return JsonResponse({
        'id': website.id,
        'company': website.company,
        'domain': website.domain,
        'website': website.website,
        'email': website.email,
        'mobile': website.mobile,
        'address': website.address,
        'is_active': website.is_active,
        'logo_url': website.logo_url,
        'header_url': website.header_url,
        'footer_url': website.footer_url,
        'signature_url': website.signature_url,
        'recaptcha_site_key': website.recaptcha_site_key,
        'recaptcha_secret_key': website.recaptcha_secret_key,
        'smtp_host': website.smtp_host,
        'smtp_port': website.smtp_port,
        'smtp_username': website.smtp_username,
        'smtp_password': website.smtp_password,
        'smtp_use_tls': website.smtp_use_tls,
        'api_key': website.api_key,
        'api_secret': website.api_secret,
        'payment_gateway': website.payment_gateway,
        'payment_key': website.payment_key,
        'payment_secret': website.payment_secret,
        'sms_provider': website.sms_provider,
        'sms_api_key': website.sms_api_key,
        'sms_api_secret': website.sms_api_secret,
        'sms_sender_id': website.sms_sender_id,
        'google_analytics_id': website.google_analytics_id,
        'facebook_pixel_id': website.facebook_pixel_id,
        'social_facebook': website.social_facebook,
        'social_twitter': website.social_twitter,
        'social_instagram': website.social_instagram,
        'social_linkedin': website.social_linkedin,
        'social_youtube': website.social_youtube,
        'maintenance_mode': website.maintenance_mode,
        'maintenance_message': website.maintenance_message,
        'created_at': website.created_at.isoformat(),
        'updated_at': website.updated_at.isoformat()
    })


@require_http_methods(["POST"])
def website_create(request):
    try:
        company = request.POST.get('company')
        domain = request.POST.get('domain')
        website = request.POST.get('website')

        if not company or not domain or not website:
            return JsonResponse({'success': False, 'error': 'Company, domain, and website URL are required'}, status=400)

        is_active = request.POST.get('is_active', 'false').lower() == 'true'
        smtp_use_tls = request.POST.get('smtp_use_tls', 'true').lower() == 'true'
        maintenance_mode = request.POST.get('maintenance_mode', 'false').lower() == 'true'

        website_obj = Website.objects.create(
            company=company,
            domain=domain,
            website=website,
            email=request.POST.get('email', ''),
            mobile=request.POST.get('mobile', ''),
            address=request.POST.get('address', ''),
            is_active=is_active,
            recaptcha_site_key=request.POST.get('recaptcha_site_key', ''),
            recaptcha_secret_key=request.POST.get('recaptcha_secret_key', ''),
            smtp_host=request.POST.get('smtp_host', ''),
            smtp_port=request.POST.get('smtp_port') or None,
            smtp_username=request.POST.get('smtp_username', ''),
            smtp_password=request.POST.get('smtp_password', ''),
            smtp_use_tls=smtp_use_tls,
            api_key=request.POST.get('api_key', ''),
            api_secret=request.POST.get('api_secret', ''),
            payment_gateway=request.POST.get('payment_gateway', ''),
            payment_key=request.POST.get('payment_key', ''),
            payment_secret=request.POST.get('payment_secret', ''),
            sms_provider=request.POST.get('sms_provider', ''),
            sms_api_key=request.POST.get('sms_api_key', ''),
            sms_api_secret=request.POST.get('sms_api_secret', ''),
            sms_sender_id=request.POST.get('sms_sender_id', ''),
            google_analytics_id=request.POST.get('google_analytics_id', ''),
            facebook_pixel_id=request.POST.get('facebook_pixel_id', ''),
            social_facebook=request.POST.get('social_facebook', ''),
            social_twitter=request.POST.get('social_twitter', ''),
            social_instagram=request.POST.get('social_instagram', ''),
            social_linkedin=request.POST.get('social_linkedin', ''),
            social_youtube=request.POST.get('social_youtube', ''),
            maintenance_mode=maintenance_mode,
            maintenance_message=request.POST.get('maintenance_message', '')
        )

        if 'logo' in request.FILES:
            website_obj.logo = request.FILES['logo']
        if 'header' in request.FILES:
            website_obj.header = request.FILES['header']
        if 'footer' in request.FILES:
            website_obj.footer = request.FILES['footer']
        if 'signature' in request.FILES:
            website_obj.signature = request.FILES['signature']

        website_obj.save()

        return JsonResponse({'success': True, 'message': 'Website created successfully!', 'id': website_obj.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def website_update(request, pk):
    try:
        website_obj = get_object_or_404(Website, pk=pk)

        company = request.POST.get('company')
        domain = request.POST.get('domain')
        website = request.POST.get('website')

        if not company or not domain or not website:
            return JsonResponse({'success': False, 'error': 'Company, domain, and website URL are required'}, status=400)

        website_obj.company = company
        website_obj.domain = domain
        website_obj.website = website
        website_obj.email = request.POST.get('email', '')
        website_obj.mobile = request.POST.get('mobile', '')
        website_obj.address = request.POST.get('address', '')
        website_obj.is_active = request.POST.get('is_active', 'false').lower() == 'true'
        website_obj.recaptcha_site_key = request.POST.get('recaptcha_site_key', '')
        website_obj.recaptcha_secret_key = request.POST.get('recaptcha_secret_key', '')
        website_obj.smtp_host = request.POST.get('smtp_host', '')
        website_obj.smtp_port = request.POST.get('smtp_port') or None
        website_obj.smtp_username = request.POST.get('smtp_username', '')
        website_obj.smtp_password = request.POST.get('smtp_password', '')
        website_obj.smtp_use_tls = request.POST.get('smtp_use_tls', 'true').lower() == 'true'
        website_obj.api_key = request.POST.get('api_key', '')
        website_obj.api_secret = request.POST.get('api_secret', '')
        website_obj.payment_gateway = request.POST.get('payment_gateway', '')
        website_obj.payment_key = request.POST.get('payment_key', '')
        website_obj.payment_secret = request.POST.get('payment_secret', '')
        website_obj.sms_provider = request.POST.get('sms_provider', '')
        website_obj.sms_api_key = request.POST.get('sms_api_key', '')
        website_obj.sms_api_secret = request.POST.get('sms_api_secret', '')
        website_obj.sms_sender_id = request.POST.get('sms_sender_id', '')
        website_obj.google_analytics_id = request.POST.get('google_analytics_id', '')
        website_obj.facebook_pixel_id = request.POST.get('facebook_pixel_id', '')
        website_obj.social_facebook = request.POST.get('social_facebook', '')
        website_obj.social_twitter = request.POST.get('social_twitter', '')
        website_obj.social_instagram = request.POST.get('social_instagram', '')
        website_obj.social_linkedin = request.POST.get('social_linkedin', '')
        website_obj.social_youtube = request.POST.get('social_youtube', '')
        website_obj.maintenance_mode = request.POST.get('maintenance_mode', 'false').lower() == 'true'
        website_obj.maintenance_message = request.POST.get('maintenance_message', '')

        if 'logo' in request.FILES:
            website_obj.logo = request.FILES['logo']
        if 'header' in request.FILES:
            website_obj.header = request.FILES['header']
        if 'footer' in request.FILES:
            website_obj.footer = request.FILES['footer']
        if 'signature' in request.FILES:
            website_obj.signature = request.FILES['signature']

        website_obj.save()

        return JsonResponse({'success': True, 'message': 'Website updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def website_delete(request, pk):
    try:
        website_obj = get_object_or_404(Website, pk=pk)
        website_obj.delete()
        return JsonResponse({'success': True, 'message': 'Website deleted successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)