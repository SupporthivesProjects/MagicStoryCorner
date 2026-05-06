import asyncio
import base64
import io
import os
from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

from django.core.files import File
from django.db.models import Max
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from products.models import ProductBook, ProductBookPurchase
from products.builder import ProductBookBuilder
from stories.helper.views import get_story_options
from logs.models import Log
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from products.models import Configuration
from logs.models import Log
from django.core.files.storage import default_storage
from django.conf import settings
import os
import shutil
from django.views.decorators.csrf import csrf_exempt

def productbook_list(request):
    stories = ProductBook.objects.filter(status="completed").order_by("-created_at")
    context = {
        "stories": stories
    }
    return render(request, "demos/products/list_books.html", context)

def productbook_get(request, slug):
    book = get_object_or_404(ProductBook, slug=slug)
    pages = book.pages.order_by("page")
    return render(request, "demos/products/view_book.html", {"book": book, "pages": pages})


@require_http_methods(["POST"])
def retry_cover(request, book_id):
    try:
        data = json.loads(request.body)
        method = data.get('method', 'python')
        
        if method == 'ai':
            from products.cover_ai import GeminiCoverGenerator
            regenerator = GeminiCoverGenerator()
            result = regenerator.retry_cover(book_id)
        else:
            from products.cover_pil import PILCoverGenerator
            regenerator = PILCoverGenerator()
            result = regenerator.retry_cover(book_id)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required(login_url='admin_login')
def productbook_create(request):
    context = get_story_options()
    if request.method == "POST":
        story_data = request.POST
        
        input_data = {
            "childgroup_id": story_data.get("childgroup_id"),
            "character_name": story_data.get("character_name"),
            "character_desc": story_data.get("character_desc"),
            "setting_id": story_data.get("setting_id"),
            "setting_desc": story_data.get("setting_desc"),
            "plot_id": story_data.get("plot_id"),
            "plot_desc": story_data.get("plot_desc"),
            "theme_id": story_data.get("theme_id"),
            "theme_desc": story_data.get("theme_desc"),
            "tone_id": story_data.get("tone_id"),
            "storylength_id": story_data.get("storylength_id"),
            "imagestyle_id": story_data.get("imagestyle_id"),
            "language_id": story_data.get("language_id"),
        }

        narrator_value = story_data.get("narrator_id")
        if narrator_value: 
            input_data["narrator_id"] = narrator_value

        builder = ProductBookBuilder(request.user, input_data)

        try:
            book = builder.save_book()
            if book and book.status == "completed":
                messages.success(request, "Product Book generated successfully!")
                return redirect("admin_books_detail", slug=book.slug)
            else:
                messages.error(request, "Failed to generate the Product Book.")
                return redirect("admin_books_create")

        except Exception as e:
            error_message = f"Failed to generate Product Book: {str(e)}"
            messages.error(request, error_message)
            try:
                Log.objects.create(title="Product Book Generation Error", type="error", message=error_message)
            except Exception:
                pass
            return redirect("admin_books_create")

    return render(request, "demos/products/create_book.html", context)

def productbook_edit(request, book_id):
    book = get_object_or_404(ProductBook, id=book_id)
    
    if request.method == 'GET':
        try:
            data = {
                'success': True,
                'id': book.id,
                'title': book.title,
                'description': book.description if hasattr(book, 'description') else '',
                'price': float(book.price) if book.price else 0.00,
                'tokens': book.tokens if hasattr(book, 'tokens') else 0,
                'is_active': book.is_active if hasattr(book, 'is_active') else True
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error fetching book data: {str(e)}'
            }, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            if not data.get('title'):
                return JsonResponse({
                    'success': False,
                    'message': 'Title is required'
                }, status=400)
            
            book.title = data.get('title', book.title).strip()
            book.description = data.get('description', book.description).strip() if data.get('description') else ''
            
            try:
                book.price = float(data.get('price', book.price))
                if book.price < 0:
                    return JsonResponse({
                        'success': False,
                        'message': 'Price cannot be negative'
                    }, status=400)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid price format'
                }, status=400)
            
            try:
                book.tokens = int(data.get('tokens', book.tokens))
                if book.tokens < 0:
                    return JsonResponse({
                        'success': False,
                        'message': 'Tokens cannot be negative'
                    }, status=400)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid tokens format'
                }, status=400)
            
            book.is_active = bool(data.get('is_active', book.is_active))
            
            book.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Book updated successfully',
                'book': {
                    'id': book.id,
                    'title': book.title,
                    'description': book.description,
                    'price': float(book.price),
                    'tokens': book.tokens,
                    'is_active': book.is_active
                }
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating book: {str(e)}'
            }, status=500)



@login_required(login_url='admin_login')
def user_purchased_books(request):
    
    purchases = ProductBookPurchase.objects.select_related(
        'user', 
        'book'
    ).order_by('-created_at')
    
    return render(request, 'demos/products/purchased_books.html', {  'purchases': purchases })


DEFAULT_CONFIG = {
    'admin': {
        'chars_per_page': 400,
        'max_pages': 25,
        'img_retries': 3,
        'tts_retries': 3,
        'workers': 10,
        'consistency_checks': 4,
        'story_retries': 3,
        'min_story_len': 80,
    },
    'user': {
        'chars_per_page': 400,
        'max_pages': 25,
        'img_retries': 1,
        'tts_retries': 1,
        'workers': 10,
        'consistency_checks': 4,
        'story_retries': 1,
        'min_story_len': 80,
    }
}


@login_required(login_url='admin_login')
def configurations(request):
    admin_config = Configuration.objects.filter(type='admin').first()
    user_config = Configuration.objects.filter(type='user').first()
    
    if not admin_config:
        admin_config = Configuration.objects.create(type='admin', **DEFAULT_CONFIG['admin'])
    
    if not user_config:
        user_config = Configuration.objects.create(type='user', **DEFAULT_CONFIG['user'])
    
    context = {
        'admin_config': admin_config,
        'user_config': user_config,
    }
    return render(request, "demos/products/configurations.html", context)


@login_required(login_url='admin_login')
@require_http_methods(["POST"])
def save_configuration(request):
    try:
        data = json.loads(request.body)
        config_type = data.get('type', 'admin')
        config = Configuration.objects.filter(type=config_type).first()
        
        if not config:
            config = Configuration.objects.create(type=config_type, **DEFAULT_CONFIG[config_type])
        
        for field, value in data.items():
            if field != 'type' and hasattr(config, field):
                setattr(config, field, int(value))
        
        config.updated_by = request.user.first_name
        config.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Configuration saved successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='admin_login')
@require_http_methods(["POST"])
def reset_configuration(request):
    try:
        data = json.loads(request.body)
        config_type = data.get('type', 'admin')
        config = Configuration.objects.filter(type=config_type).first()
        defaults = DEFAULT_CONFIG[config_type]
        
        if config:
            for field, value in defaults.items():
                setattr(config, field, value)
            config.updated_by = request.user.first_name
            config.save()
        else:
            config = Configuration.objects.create(
                type=config_type,
                updated_by=request.user.first_name,
                **defaults
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Configuration reset to defaults'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["DELETE"])
def delete_product_book(request, book_id):
    try:
        book = ProductBook.objects.get(id=book_id)
        pages = book.pages.all()
        
        book_media_dir = os.path.join(settings.MEDIA_ROOT, 'products', 'books', str(book_id))
        deleted_media_dir = os.path.join(settings.MEDIA_ROOT, 'products', 'books', f'deleted_{book_id}')
        
        if os.path.exists(book_media_dir):
            try:
                shutil.move(book_media_dir, deleted_media_dir)
            except Exception as e:
                print(f"Error renaming book directory: {e}")
        delete_title = book.title
        delete_id = book.id

        pages.delete()
        book.delete()

        user = request.user
        full_name = f"{user.first_name} {user.last_name}".strip() if user.is_authenticated else "Leo Team"

        Log.objects.create(
            title=f"Product Book Deleted #{delete_id}",
            type="warning",
            message=f"Book:{delete_title} - Deleted by: {full_name}"
        )
        redirect_url = reverse('admin_books_list')
        return JsonResponse({'success': True, 'message': 'Book deleted successfully', 'redirect': redirect_url})
    
    except ProductBook.DoesNotExist:
        return JsonResponse({'error': 'Book not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)