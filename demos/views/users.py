from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.models import User
from stories.models import StoryBook
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
import json
import os
import shutil
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def get_users(request):
    users = User.objects.filter(is_staff=False, is_superuser=False).order_by("-id")
    context = {
        "users": users
    }
    return render(request, "demos/users/users.html", context)

def get_user_profile(request, user_id):
    try:
        user = User.objects.select_related('profile').get(
            id=user_id,
            is_staff=False, 
            is_superuser=False
        )
        
        stories = user.user_books.all().order_by('-created_at')
        
        context = {
            "user": user,
            "stories": stories,
        }
        return render(request, "demos/users/profile.html", context)
    except User.DoesNotExist:
        messages.error(request, "User not found or access denied.")
        return redirect('get_users')


def user_stories(request):
    stories = StoryBook.objects.all().order_by("-id")
    context = {
        "stories": stories
    }
    return render(request, "demos/users/stories/books.html", context)


def user_book_detail(request, slug):
    story = get_object_or_404(StoryBook, slug=slug)
    pages = story.pages.order_by("page")
    can_edit = request.user.is_authenticated and request.user == story.user
    
    context = {
        "story": story,
        "pages": pages,
        "can_edit": can_edit
    }
    return render(request, "demos/users/stories/book.html", context)


@require_http_methods(["GET", "POST"])
def edit_user_story(request, story_id):
    try:
        story = StoryBook.objects.get(id=story_id)
        
        if request.user != story.user and not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        if request.method == 'GET':
            return JsonResponse({
                'id': story.id,
                'title': story.title,
                'description': story.description,
                'is_active': getattr(story, 'is_active', True)
            })
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            
            story.title = data.get('title', story.title)
            story.description = data.get('description', story.description)
            if hasattr(story, 'is_active'):
                story.is_active = data.get('is_active', story.is_active)
            
            story.save()
            
            username = request.user.username if request.user.is_authenticated else "Anonymous"
            from logs.models import Log
            Log.objects.create(
                title="User Story Updated",
                type="info",
                message=f"Story: {story.title} | Updated by: {username}"
            )
            
            return JsonResponse({'success': True, 'message': 'Story updated successfully'})
    
    except StoryBook.DoesNotExist:
        return JsonResponse({'error': 'Story not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["DELETE"])
def delete_user_story(request, story_id):
    try:
        story = StoryBook.objects.get(id=story_id)
        
        if request.user != story.user and not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        pages = story.pages.all()
        
        story_media_dir = os.path.join(settings.MEDIA_ROOT, 'stories', 'books', str(story_id))
        deleted_media_dir = os.path.join(settings.MEDIA_ROOT, 'stories', 'books', f'deleted_{story_id}')
        
        if os.path.exists(story_media_dir):
            try:
                shutil.move(story_media_dir, deleted_media_dir)
            except Exception as e:
                print(f"Error renaming story directory: {e}")
        
        delete_title = story.title
        delete_id = story.id
        pages.delete()
        story.delete()
        
        user = request.user
        full_name = f"{user.first_name} {user.last_name}".strip() if user.is_authenticated else "Leo Team"

        from logs.models import Log
        Log.objects.create(
            title=f"User Story Deleted #{delete_id}",
            type="warning",
            message=f"Story:{delete_title} | Deleted by: {full_name}"
        )
        
        redirect_url = reverse('admin_user_books')
        return JsonResponse({'success': True, 'message': 'Story deleted successfully', 'redirect': redirect_url})
    
    except StoryBook.DoesNotExist:
        return JsonResponse({'error': 'Story not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_user(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        user = User.objects.get(id=user_id)
        user.is_active = data.get('is_active', False)
        user.save()
        
        user.profile.wallet = data.get('wallet', '')
        user.profile.email_verified = data.get('email_verified', False)
        user.profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'User updated successfully!'
        })
        
    except User.DoesNotExist:
        return JsonResponse({ 'success': False,'message': 'User not found'}, status=404)
        
    except Exception as e:
        return JsonResponse({ 'success': False,'message': str(e)}, status=500)