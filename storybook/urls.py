"""
URL configuration for storybook project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
import os
from django.conf.urls.static import static
from django.http import JsonResponse
from storybook.utils.progress import ProgressTracker

def progress_status(request):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    progress = ProgressTracker.get(request.user)
    if progress:
        return JsonResponse(progress)
    return JsonResponse({'error': 'No active progress'}, status=404)

urlpatterns = [
    path('manager/', admin.site.urls),
    path('', include('pages.urls')),       
    path('users/', include('accounts.urls')),
    path('stories/', include('stories.urls')),
    path('payments/', include('payments.urls')),
    path('products/', include('products.urls')),
    path('legals/', include('legals.urls')),
    path('logs/', include('logs.urls')),
    path('admin/', include('demos.urls')),
    path('progress-status/', progress_status, name='progress_status'),

    
]

handler404 = 'pages.views.error_404'
handler400 = 'pages.views.error_400'
handler500 = 'pages.views.error_500'
handler403 = 'pages.views.error_403'




if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

