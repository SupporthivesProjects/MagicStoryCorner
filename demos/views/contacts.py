from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from logs.models import Log
from pages.models import Contact
from legals.models import Website


@login_required
def contact_list(request):
    contacts = Contact.objects.all().order_by('-created_at')
    
    context = {
        'contacts': contacts
    }
    return render(request, 'demos/contacts/contactus.html', context)


@login_required
@require_http_methods(["POST"])
def contact_update(request, id):
    try:
        contact = get_object_or_404(Contact, id=id)
        
        status = request.POST.get('status')
        
        valid_statuses = ['pending', 'reviewed', 'resolved']
        if status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': 'Invalid status value'
            })
        
        contact.status = status
        contact.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Contact status updated successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def contact_reply(request, id):
    try:
        contact = get_object_or_404(Contact, id=id)
        reply_message = request.POST.get('reply_message', '').strip()
        
        if not reply_message:
            return JsonResponse({
                'success': False,
                'error': 'Reply message is required'
            })
        
        website = Website.objects.filter(is_active=True).first()
        
        context = {
            'website': website,
            'name': contact.name,
            'user_message': contact.message,
            'reply_message': reply_message
        }
        
        html_message = render_to_string('pages/emails/contact_reply.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Reply to Your Contact Request - LittleStoryBox',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[contact.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        contact.status = 'resolved'
        contact.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Reply sent successfully!'
        })
        
    except Contact.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Contact not found'
        })
    except Exception as e:
        Log.objects.create(
            title="Contact Reply Error",
            type="error",
            message=f"Contact ID: {id}, Error: {str(e)}"
        )
        return JsonResponse({
            'success': False,
            'error': 'Failed to send reply'
        })


@login_required
@require_http_methods(["POST"])
def contact_delete(request, id):
    try:
        contact = get_object_or_404(Contact, id=id)
        contact_name = contact.name
        contact.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Contact from {contact_name} deleted successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })