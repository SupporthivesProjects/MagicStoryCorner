from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from logs.models import Log
from legals.models import Website 
from .models import Contact
import requests
from payments.models import Package, Currency


def index(request):
    bronze_package = Package.objects.filter(order=1).first()
    popular_package = Package.objects.filter(order=2, is_popular=True).first()
    silver_package = Package.objects.filter(order=3).first()


    return render(request, 'pages/index.html', {
        'bronze_package': bronze_package,
        'popular_package': popular_package,
        'silver_package': silver_package,
    })

def app_install(request):
    context = {
        'base_url': request.build_absolute_uri('/'),
    }
    return render(request, 'pages/app_install.html', context)

def about(request):
    return render(request, 'pages/about.html')

def howItWorks(request):
    return render(request, 'pages/how_it_works.html')

def contactUs(request):
    website = Website.objects.filter(is_active=True).first()

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        message = request.POST.get("message", "").strip()
        recaptcha_response = request.POST.get("g-recaptcha-response")

        if not all([name, email, message]):
            return JsonResponse({
                "success": False,
                "message": "Please fill in all required fields."
            })

        if not recaptcha_response:
            return JsonResponse({
                "success": False,
                "message": "Please complete the reCAPTCHA verification."
            })

        try:
            data = {
                "secret": website.recaptcha_secret_key,
                "response": recaptcha_response
            }

            r = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data=data,
                timeout=5
            )
            result = r.json()

            if result.get("success"):
                Contact.objects.create(
                    name=name,
                    email=email,
                    mobile=mobile,
                    message=message,
                    status="pending"
                )

                try:
                    context = {
                        'website': website,
                        'name': name,
                        'email': email,
                        'mobile': mobile,
                        'message': message
                    }
                    
                    html_message = render_to_string('pages/emails/contact_confirmation.html', context)
                    plain_message = strip_tags(html_message)
                    
                    send_mail(
                        subject='Contact Request Received - LittleStoryBox',
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=False,
                    )
                    
                    if website and website.email:
                        admin_html_message = render_to_string('pages/emails/contact_admin_notification.html', context)
                        admin_plain_message = strip_tags(admin_html_message)
                        
                        send_mail(
                            subject=f'New Contact Request from {name}',
                            message=admin_plain_message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[website.email],
                            html_message=admin_html_message,
                            fail_silently=True,
                        )
                    
                except Exception as e:
                    Log.objects.create(
                        title="Contact Email Error",
                        type="warning",
                        message=f"Contact saved but email failed - Name: {name}, Email: {email}, Error: {str(e)}"
                    )
                
                return JsonResponse({
                    "success": True,
                    "message": "Thank you! Your message has been sent."
                })
            else:
                return JsonResponse({
                    "success": False,
                    "message": "reCAPTCHA verification failed."
                })

        except requests.RequestException as e:
            Log.objects.create(
                title="Contact Form Error",
                type="error",
                message=f"reCAPTCHA API error: {str(e)}"
            )
            return JsonResponse({
                "success": False,
                "message": "An error occurred while processing your request."
            })
        except Exception as e:
            Log.objects.create(
                title="Contact Form Error",
                type="error",
                message=f"Unexpected error: {str(e)}"
            )
            return JsonResponse({
                "success": False,
                "message": "An error occurred while processing your request."
            })

    return render(request, "pages/contact_us.html", {"website": website})

def error_404(request, exception=None):
    return render(request, 'pages/404.html', status=404)

def error_500(request, exception=None):
    return render(request, 'pages/500.html', status=500)

def error_403(request, exception=None):
    return render(request, 'pages/403.html', status=403)

def error_400(request, exception=None):
    return render(request, 'pages/400.html', status=400)