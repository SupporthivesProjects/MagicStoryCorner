import asyncio
import base64
import json
import os
import re
import subprocess
import tempfile
import time
from io import BytesIO
from pathlib import Path
from datetime import datetime

import openai
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

from accounts.context_processors import loggedin_user
from accounts.decorators import login_required, tokens_required, verified_required
from accounts.models import Wallet
from stories.builder import StoryBookBuilder
from stories.helper.views import get_story_options
from stories.models import *
from products.models import *
from products.builder import ProductBookBuilder
from logs.models import Log
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.urls import reverse
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404
import html


logger = logging.getLogger(__name__)


BASE_TOKENS = 100

def merge_story_data(request, new_data):
    story_data = request.session.get("story_data", {})
    story_data.update(new_data)
    request.session["story_data"] = story_data
    request.session.modified = True
    return story_data


@csrf_exempt
def save_age_group(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            merge_story_data(request, {
                'childgroup_id': data.get('agegroup'),
                'age_cost': data.get('age_cost', 0)
            })
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def story_save_step_one(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            merge_story_data(request, {
                'character_name': data.get('char_name'),
                'character_desc': data.get('char_look'),
                'char_cost': data.get('char_cost', 0)
            })
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def story_save_step_two(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            merge_story_data(request, {
                'setting_id': data.get('setting_id'),
                'setting_desc': data.get('setting_text'),
                'plot_id': data.get('plot_id'),
                'plot_desc': data.get('plot_text'),
                'theme_id': data.get('theme_id'),
                'theme_desc': data.get('theme_text'),
                'setting_cost': data.get('setting_cost', 0),
                'plot_cost': data.get('plot_cost', 0),
                'theme_cost': data.get('theme_cost', 0)
            })
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def story_save_step_three(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            merge_story_data(request, {
                'tone_id': data.get('tone_id'),
                'storylength_id': data.get('length_id'),
                'imagestyle_id': data.get('style_id'),
                'style_cost': data.get('style_cost', 0),
                'tone_cost': data.get('tone_cost', 0),
                'length_cost': data.get('length_cost', 0)
            })
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def story_save_step_four(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            story_data = merge_story_data(request, {
                'narrator_id': data.get('narrator_id') or None, 
                'language_id': data.get('language_id'),
                'narrator_cost': data.get('narrator_cost', 0),
                'language_cost': data.get('language_cost', 0)
            })

            return JsonResponse({'success': True, 'story_data': story_data})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@tokens_required(100)
@verified_required
def story_book_create(request):
    context = get_story_options()
    story_data = request.session.get("story_data", {})

    total_tokens = BASE_TOKENS
    for key in [
        'age_cost', 'char_cost', 'setting_cost', 'plot_cost', 'theme_cost',
        'style_cost', 'tone_cost', 'length_cost', 'narrator_cost', 'language_cost'
    ]:
        total_tokens += int(story_data.get(key, 0))

    context['storybook'] = story_data
    context['total_tokens'] = total_tokens

    if request.method == "POST":
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
            "narrator_id": story_data.get("narrator_id"),
            "total_tokens": total_tokens
        }

        user_wallet = request.user.profile.wallet

        if user_wallet < total_tokens:
            messages.error(request, "You don't have enough tokens to create this story.")
            return redirect("story_book_create")

        upfront_tokens = 100
        profile = request.user.profile
        profile.wallet -= upfront_tokens
        profile.save()

        current_balance = profile.wallet
        Wallet.objects.create(
            user=request.user,
            type="deduct",
            amount=upfront_tokens,
            message="StoryBook creation (initial)",
            balance=current_balance
        )

        builder = StoryBookBuilder(request.user, input_data)

        try:
            book = builder.save_book()

            if book and book.status == "completed":
                remaining_tokens = total_tokens - upfront_tokens

                if remaining_tokens > 0:
                    profile.refresh_from_db()
                    profile.wallet -= remaining_tokens
                    profile.save()

                    current_balance = profile.wallet
                    Wallet.objects.create(
                        user=request.user,
                        type="deduct",
                        amount=remaining_tokens,
                        balance=current_balance,
                        message="StoryBook creation (final)"
                    )

                book.tokens = total_tokens
                book.save()

                messages.success(request, "StoryBook generated successfully!")
                request.session.pop("story_data", None)
                request.session.modified = True
                return redirect("story_book_view", slug=book.slug)

            else:
                messages.error(
                    request,
                    "Failed to generate the StoryBook. You were only charged 100 tokens."
                )
                return redirect("story_book_create")

        except Exception as e:
            error_message = f"Failed to generate StoryBook: {str(e)}"
            messages.error(request, error_message)

            try:
                Log.objects.create(
                    title="StoryBook Generation Error",
                    type="error",
                    message=error_message
                )
            except Exception:
                pass

            return redirect("story_book_create")

    return render(request, "stories/create.html", context)




@login_required
@verified_required
def story_book_view(request, slug):
    try:
        book = get_object_or_404(StoryBook, slug=slug)
        
        if book.user != request.user:
            messages.error(request, "You don't have permission to view this storybook.")
            return redirect('story_book_create')
        
        return render(request, 'stories/view.html', {'book': book})
    
    except Http404:
        messages.error(request, "Story book not found.")
        return redirect('story_book_create')
    
    except Exception as e:
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect('story_book_create')
    

def storybook_download(request, slug):
    book = get_object_or_404(StoryBook, slug=slug)

    if not book.pages.exists():
        Log.objects.create(
            title="PDF Generation Failed",
            type="warning",
            message=f"No pages found in book '{book.title}' (ID: {book.id}). Cannot generate PDF."
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No pages found in this book. Cannot generate PDF.'}, status=400)
        messages.warning(request, "No pages found in this book. Cannot generate PDF.")
        return redirect("library_view", slug=book.slug)

    if not book.pdf or not book.pdf.name:
        try:
            storybook_generate_and_save_pdf(request, book)
            logged_in_user = loggedin_user(request).get("logged_in_user")
            if logged_in_user:
                try:
                    logged_in_user.profile.wallet -= 40
                    logged_in_user.profile.save()
                    current_balance = logged_in_user.profile.wallet
                    Wallet.objects.create(
                        user=logged_in_user,
                        type="deduct",
                        amount=40,
                        balance=current_balance,
                        message=f"Download PDF: {book.title}"
                    )
                except Exception as wallet_error:
                    Log.objects.create(
                        title="Wallet Transaction Failed",
                        type="error",
                        message=f"Wallet creation failed: {str(wallet_error)}"
                    )
        except Exception as e:
            Log.objects.create(
                title="PDF Generation Failed",
                type="error",
                message=f"PDF generation failed for '{book.title}': {str(e)}"
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=500)
            messages.error(request, f"PDF generation failed: {e}")
            return redirect("library_view", slug=book.slug)
    
    try:
        pdf_bytes = storybook_generate_pdf_bytes(request, book)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{book.title}.pdf"'
        response['Content-Length'] = len(pdf_bytes)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
        
    except Exception as e:
        Log.objects.create(
            title="PDF Generation Failed",
            type="error",
            message=f"Error generating PDF for book '{book.title}': {str(e)}"
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        messages.error(request, f"Error generating PDF: {e}")
        return redirect("library_view", slug=book.slug)


def storybook_generate_pdf_bytes(request, book):
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
    
    html_content = """
        <html><head><style>
        @page{size:A4;margin:0;}
        body{font-family:'Georgia','Times New Roman',serif;margin:0;padding:0;color:#2c2c2c;}

        .page{position:relative;width:210mm;height:297mm;overflow:hidden;page-break-after:always;margin:0;padding:0;box-sizing:border-box;} 
        .page:last-child{page-break-after:auto;}

        .cover-page{
            position:relative;
            width:210mm;
            height:297mm;
            margin:0;
            padding:0;
            overflow:hidden;
        }

        .cover-image-container{
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
        }

        .cover-image{
            width:100%;
            height:100%;
            object-fit:fill;
            display:block;
            margin:0;
            padding:0;
        }

        .cover-title-overlay{
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
        }

        .cover-title{
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
        }

        .page-image{
            width:100%;
            height:auto;
            object-fit:contain;
            display:block;
            background-color:#f5f5f5;
            margin:0;
            padding:0;
            box-sizing:border-box;
        }

        .page-text{
            padding:20px 30px;
            overflow:hidden;
            font-size:18px;
            line-height:1.5;
            letter-spacing:0.5px;
            margin:0;
            box-sizing:border-box;
        }

        .page-number{position:absolute;bottom:10px;left:20px;font-size:18px;color:#666;}
        </style></head><body>
        """
    
    cover_image = None

    if hasattr(book, "char_img") and book.char_img:
        cover_image = book.char_img
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


def storybook_generate_and_save_pdf(request, book):
    pdf_bytes = storybook_generate_pdf_bytes(request, book)
    pdf_file = BytesIO(pdf_bytes)
    book.pdf.save(f"{book.title}.pdf", File(pdf_file), save=True)