import asyncio
import base64
import os
import re
import subprocess
import tempfile
import time
from io import BytesIO
from pathlib import Path
from datetime import datetime

from rest_framework.authtoken.models import Token
import requests
from PIL import Image
# from weasyprint import HTML, CSS
from playwright.async_api import async_playwright
from django.conf import settings
from django.core.cache import cache
from django.core.files import File
from django.db.models import Max
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify
from django.contrib import messages

from accounts.emails.helpers import send_story_purchase_email
from accounts.models import Wallet
from stories.helper.views import get_story_options
from stories.models import *
from products.models import *
from products.builder import ProductBookBuilder
from logs.models import Log
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import ProductBook, ProductBookPurchase
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
import json
from accounts.decorators import login_required, tokens_required, verified_required
# import google.generativeai as genai
import google.genai as genai
from django.db.models import Prefetch


@login_required
@require_http_methods(["POST"])
@csrf_protect
def product_book_purchase(request):
   
    try:
        data = json.loads(request.body)
        story_id = data.get('story_id')
        if not story_id:
            return JsonResponse({'success': False, 'message': 'Invalid story ID'}, status=400)
        
        try:
            book = ProductBook.objects.get(id=story_id)
        except ProductBook.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Book not found'}, status=404)
        
        user = request.user
        
        if ProductBookPurchase.objects.filter(user=user, book=book).exists():
            return JsonResponse({'success': False, 'message': 'You have already purchased this book'}, status=400)
        
        if user.profile.wallet < book.tokens:
            return JsonResponse({'success': False, 'message': 'Insufficient token balance'}, status=400)
        
        with transaction.atomic():
            user.profile.wallet -= book.tokens
            user.profile.save()
            current_balance = user.profile.wallet
            
            Wallet.objects.create(
                user=request.user,
                type="deduct",
                amount=book.tokens,
                balance=current_balance,
                message=f"Purchase: {book.title}"
            )
            
            ProductBookPurchase.objects.create(user=user, book=book)
        
        send_story_purchase_email(user, book)
        
        return JsonResponse({'success': True, 'message': 'Purchase successful', 'new_balance': user.profile.wallet})
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'}, status=500)
    
from django.core.cache import cache

def product_book_list(request):
    base_books = (
        ProductBook.objects
        .filter(is_active=True, status="completed", image__isnull=False)
        .exclude(image="")
        .select_related('agegroup', 'plot', 'theme', 'narrator', 'imagestyle')
        .prefetch_related('pages')
        .distinct()
    )

    stories = base_books

    search_query = request.GET.get("search")
    if search_query:
        stories = stories.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

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
    if sort_by == "price_asc":
        stories = stories.order_by("tokens", "id")
    elif sort_by == "price_desc":
        stories = stories.order_by("-tokens", "id")
    else:
        stories = stories.order_by("-created_at", "id")

    per_page_cards = 8

    paginator = Paginator(stories, per_page_cards)
    page_number = request.GET.get("page")

    try:
        page_obj = paginator.page(page_number)
    except:
        page_obj = paginator.page(1)

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if not is_ajax:
        cache_key = "book_list_filters"
        filter_data = cache.get(cache_key)

        if not filter_data:
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
            filter_data = {
                "ages": list(ages),
                "story_types": list(story_types),
                "themes": list(themes),
                "narrations": list(narrations),
                "styles": list(styles),
            }
            cache.set(cache_key, filter_data, 60 * 10)

        ages = filter_data["ages"]
        story_types = filter_data["story_types"]
        themes = filter_data["themes"]
        narrations = filter_data["narrations"]
        styles = filter_data["styles"]
    else:
        ages = []
        story_types = []
        themes = []
        narrations = []
        styles = []

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    query_string = query_params.urlencode()

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
        "query_string": query_string,
    }

    if is_ajax:
        html = render_to_string("products/cards.html", {"stories": page_obj})
        pagination_html = render_to_string("products/pagination.html", {
            "page_obj": page_obj,
            "query_string": query_string
        })
        return JsonResponse({
            "html": html,
            "pagination_html": pagination_html,
            "start_index": page_obj.start_index(),
            "end_index": page_obj.end_index(),
            "total_count": page_obj.paginator.count
        })

    return render(request, "products/books.html", context)


def product_books_details(request, slug):
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
    
    if not user and request.user.is_authenticated:
        user = request.user
        is_purchased = ProductBookPurchase.objects.filter( user=user, book=story).exists()

    return render(request, "products/book.html", {"story": story, "is_purchased": is_purchased })



def productbook_download(request, slug):
    book = get_object_or_404(ProductBook, slug=slug)

    if not book.pages.exists():
        Log.objects.create(title="PDF Generation Failed", type="warning",
                           message=f"No pages found in book '{book.title}' (ID: {book.id}). Cannot generate PDF.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No pages found in this book. Cannot generate PDF.'}, status=400)
        messages.warning(request, "No pages found in this book. Cannot generate PDF.")
        return redirect("admin_books_detail", slug=book.slug)

    try:
        pdf_bytes = generate_pdf_bytes(request, book)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{book.title}.pdf"'
        response['Content-Length'] = len(pdf_bytes)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    except Exception as e:
        Log.objects.create(title="PDF Generation Failed", type="error",
                           message=f"Error generating PDF for book '{book.title}': {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': f'Error generating PDF: {str(e)}'}, status=500)
        messages.error(request, f"Error generating PDF: {e}")
        return redirect("admin_books_detail", slug=book.slug)


def generate_pdf_bytes(request, book):
    pages = book.pages.all().order_by("page")
    
    def img_to_base64(image_field):
        img = Image.open(image_field.path)
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=100)
        encoded = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{encoded}"
    
    def calculate_text_lines(text):
        if not text:
            return 0
        return len(text) // 80 + text.count('\n')
    
    html_content = f"""
        <html><head><style>
        @page{{size:A4;margin:0;}}
        body{{font-family:'Georgia','Times New Roman',serif;margin:0;padding:0;color:#2c2c2c;}}

        .page{{position:relative;width:210mm;height:297mm;overflow:hidden;page-break-after:always;margin:0;padding:0;box-sizing:border-box;}} 
        .page:last-child{{page-break-after:auto;}}

        .cover-page{{
            position:relative;
            width:210mm;
            height:297mm;
            margin:0;
            padding:0;
            overflow:hidden;
        }}

        .cover-image-container{{
            position:absolute;
            top:0;
            left:0;
            width:100%;
            height:100%;
            margin:0;
            padding:0;
            line-height:0;
            overflow:hidden;
            background-color:#ffffff;
        }}

        .cover-image{{
            width:100%;
            height:100%;
            object-fit:fill;
            display:block;
            margin:0;
            padding:0;
        }}

        .cover-title-overlay{{
            position:absolute;
            bottom:0;
            left:0;
            width:100%;
            min-height:100px;
            display:flex;
            align-items:center;
            justify-content:center;
            background:linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.8) 60%, rgba(0,0,0,0) 100%);
            z-index:10;
            padding:30px 20px;
            box-sizing:border-box;
        }}

        .cover-title{{
            text-align:center;
            font-size:28px;
            font-weight:bold;
            letter-spacing:0.5px;
            color:#ffffff;
            margin:0;
            padding:15px 20px;
            text-shadow:2px 2px 8px rgba(0,0,0,0.9);
            line-height:1.4;
            max-width:90%;
        }}

        .page-image{{
            width:100%;
            height:auto;
            object-fit:contain;
            display:block;
            background-color:#f5f5f5;
            margin:0;
            padding:0;
            box-sizing:border-box;
        }}

        .page-text{{
            padding:20px 30px;
            overflow:hidden;
            font-size:18px;
            line-height:1.5;
            letter-spacing:0.5px;
            margin:0;
            box-sizing:border-box;
        }}

        .page-number{{position:absolute;bottom:10px;left:20px;font-size:18px;color:#666;}}
        </style></head><body>
        """
    
    cover_image = None

    if hasattr(book, "image") and book.image:
        cover_image = book.image
    elif hasattr(book, "image") and book.image:
        cover_image = book.image
    elif pages and pages[0].image:
        cover_image = pages[0].image

    html_content += '<div class="page cover-page">'
    html_content += '<div class="cover-image-container">'
    if cover_image:
        html_content += f'<img class="cover-image" src="{img_to_base64(cover_image)}">'
    html_content += '</div>'
    html_content += '<div class="cover-title-overlay">'
    html_content += f'<div class="cover-title">{book.title}</div>'
    html_content += '</div>'
    html_content += '</div>'
    
    for page in pages:
        text_lines = calculate_text_lines(page.text or "")
        needs_more_space = text_lines > 8
        
        image_class = "page-image-reduced" if needs_more_space else "page-image-normal"
        text_class = "page-text-expanded" if needs_more_space else "page-text-normal"
        
        html_content += '<div class="page">'
        if page.image:
            html_content += f'<img class="page-image {image_class}" src="{img_to_base64(page.image)}">'
        html_content += f'<div class="page-text {text_class}">'
        html_content += f'<p>{page.text or ""}</p>'
        html_content += '</div>'
        html_content += f'<div class="page-number">{page.page}</div>'
        html_content += '</div>'
    
    html_content += "</body></html>"
    
    async def generate_pdf(html):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html)
            pdf_bytes = await page.pdf(
                format="A4", 
                print_background=True, 
                display_header_footer=False,
                prefer_css_page_size=True
            )
            await browser.close()
            return pdf_bytes
    
    pdf_bytes = asyncio.run(generate_pdf(html_content))
    return pdf_bytes


def generate_and_save_pdf(request, book):
    pdf_bytes = generate_pdf_bytes(request, book)
    pdf_file = BytesIO(pdf_bytes)
    book.pdf.save(f"{book.title}.pdf", File(pdf_file), save=True)
