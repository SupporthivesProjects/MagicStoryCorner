from django.shortcuts import render
from products.models import ProductBook, ProductBookPurchase
from stories.models import StoryBook, ChildAgeRange, StorySetting, StoryPlot, StoryTheme, StoryTone, StoryLength, ImageStyle, LanguageOption, NarratorVoice
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
import json

User = get_user_model()

@login_required(login_url='admin_login')
def admin_dashboard(request):
    ten_minutes_ago = timezone.now() - timedelta(minutes=10)

    ProductBook.objects.filter(
        status='pending',
        created_at__lt=ten_minutes_ago
    ).update(status='failed')

    StoryBook.objects.filter(
        status='pending',
        created_at__lt=ten_minutes_ago
    ).update(status='failed')
    
    today = timezone.now().date()
    first_day_this_month = today.replace(day=1)
    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)
    this_month_start = timezone.make_aware(datetime.combine(first_day_this_month, datetime.min.time()))
    last_month_start = timezone.make_aware(datetime.combine(first_day_last_month, datetime.min.time()))
    
    product_stats = ProductBook.objects.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        pending=Count('id', filter=Q(status='pending')),
        failed=Count('id', filter=Q(status='failed')),
        this_month=Count('id', filter=Q(created_at__gte=this_month_start)),
        last_month=Count('id', filter=Q(created_at__gte=last_month_start, created_at__lt=this_month_start)),
        completed_this_month=Count('id', filter=Q(status='completed', created_at__gte=this_month_start)),
        completed_last_month=Count('id', filter=Q(status='completed', created_at__gte=last_month_start, created_at__lt=this_month_start)),
        failed_this_month=Count('id', filter=Q(status='failed', created_at__gte=this_month_start)),
        failed_last_month=Count('id', filter=Q(status='failed', created_at__gte=last_month_start, created_at__lt=this_month_start))
    )
    
    story_stats = StoryBook.objects.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        pending=Count('id', filter=Q(status='pending')),
        failed=Count('id', filter=Q(status='failed')),
        this_month=Count('id', filter=Q(created_at__gte=this_month_start)),
        last_month=Count('id', filter=Q(created_at__gte=last_month_start, created_at__lt=this_month_start)),
        completed_this_month=Count('id', filter=Q(status='completed', created_at__gte=this_month_start)),
        completed_last_month=Count('id', filter=Q(status='completed', created_at__gte=last_month_start, created_at__lt=this_month_start)),
        failed_this_month=Count('id', filter=Q(status='failed', created_at__gte=this_month_start)),
        failed_last_month=Count('id', filter=Q(status='failed', created_at__gte=last_month_start, created_at__lt=this_month_start))
    )
    
    total_users_count = User.objects.filter(
        is_active=True,
        is_staff=False,
        is_superuser=False
    ).count()
    
    def calculate_percentage_change(current, previous):
        if previous == 0:
            if current > 0:
                return f"+{current}"
            return "0"
        
        if previous < 10:
            diff = current - previous
            return f"+{diff}" if diff >= 0 else str(diff)
        
        change = ((current - previous) / previous) * 100
        return f"{'+' if change >= 0 else ''}{int(change)}%"
    
    product_book_change = calculate_percentage_change(product_stats['this_month'], product_stats['last_month'])
    product_completed_change = calculate_percentage_change(product_stats['completed_this_month'], product_stats['completed_last_month'])
    product_failed_change = calculate_percentage_change(product_stats['failed_this_month'], product_stats['failed_last_month'])
    
    story_book_change = calculate_percentage_change(story_stats['this_month'], story_stats['last_month'])
    story_completed_change = calculate_percentage_change(story_stats['completed_this_month'], story_stats['completed_last_month'])
    story_failed_change = calculate_percentage_change(story_stats['failed_this_month'], story_stats['failed_last_month'])

    days_to_monday = today.weekday()
    base_week_start = today - timedelta(days=days_to_monday)
    
    start_date = base_week_start - timedelta(weeks=6)
    end_date = base_week_start + timedelta(weeks=6, days=1)
    
    purchase_data = ProductBookPurchase.objects.filter(
        created_at__gte=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
        created_at__lt=timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
    ).extra(select={'date': 'DATE(created_at)'}).values('date').annotate(count=Count('id'))
    
    purchase_dict = {item['date']: item['count'] for item in purchase_data}
    
    product_data = ProductBook.objects.filter(
        created_at__gte=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
        created_at__lt=timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
    ).extra(select={'date': 'DATE(created_at)'}).values('date').annotate(count=Count('id'))
    
    product_dict = {item['date']: item['count'] for item in product_data}
    
    story_data = StoryBook.objects.filter(
        created_at__gte=timezone.make_aware(datetime.combine(start_date, datetime.min.time())),
        created_at__lt=timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
    ).extra(select={'date': 'DATE(created_at)'}).values('date').annotate(count=Count('id'))
    
    story_dict = {item['date']: item['count'] for item in story_data}
    
    weeks_data = []
    
    for week_offset in range(-6, 6):
        week_start = base_week_start + timedelta(weeks=week_offset)
        week_end = week_start + timedelta(days=6)
        
        daily_product_books = []
        daily_user_stories = []
        daily_purchases = []
        
        for day in range(7):
            current_day = week_start + timedelta(days=day)
            current_date = current_day.date() if hasattr(current_day, 'date') else current_day
            
            daily_product_books.append(product_dict.get(current_date, 0))
            daily_user_stories.append(story_dict.get(current_date, 0))
            daily_purchases.append(purchase_dict.get(current_date, 0))
        
        weeks_data.append({
            'offset': week_offset,
            'start': week_start.strftime('%b %d'),
            'end': week_end.strftime('%b %d, %Y'),
            'product_books': daily_product_books,
            'user_stories': daily_user_stories,
            'purchases': daily_purchases
        })
    
    weeks_data_json = json.dumps(weeks_data)
    
    current_day_of_week = today.weekday()
    
    story_config_data = {}
    
    config_groups = [
        ('agegroup', ChildAgeRange, 'Age Ranges'),
        ('setting', StorySetting, 'Settings'),
        ('plot', StoryPlot, 'Plots'),
        ('theme', StoryTheme, 'Themes'),
        ('tone', StoryTone, 'Tones'),
        ('length', StoryLength, 'Lengths'),
        ('imagestyle', ImageStyle, 'Image Styles'),
        ('language', LanguageOption, 'Languages'),
        ('narrator', NarratorVoice, 'Narrators')
    ]
    
    for key, model, display_name in config_groups:
        story_config_data[key] = {
            'labels': [],
            'productBooks': [],
            'userStories': []
        }
        
        for config_obj in model.objects.all():
            pb_count = ProductBook.objects.filter(**{f'{key}': config_obj}).count()
            sb_count = StoryBook.objects.filter(**{f'{key}': config_obj}).count()
            
            if pb_count > 0 or sb_count > 0:
                story_config_data[key]['labels'].append(config_obj.name)
                story_config_data[key]['productBooks'].append(pb_count)
                story_config_data[key]['userStories'].append(sb_count)
        
        if not story_config_data[key]['labels']:
            story_config_data[key]['labels'] = ['No Data']
            story_config_data[key]['productBooks'] = [0]
            story_config_data[key]['userStories'] = [0]
    
    story_config_json = json.dumps(story_config_data)
    
    context = {
        'product_book_count': product_stats['total'],
        'product_completed_count': product_stats['completed'],
        'product_pending_count': product_stats['pending'],
        'product_failed_count': product_stats['failed'],
        'product_book_change': product_book_change,
        'product_completed_change': product_completed_change,
        'product_failed_change': product_failed_change,
        'product_books_this_month': product_stats['this_month'],
        'product_completed_this_month': product_stats['completed_this_month'],
        'product_failed_this_month': product_stats['failed_this_month'],
        'storybook_count': story_stats['total'],
        'storybook_completed_count': story_stats['completed'],
        'storybook_pending_count': story_stats['pending'],
        'storybook_failed_count': story_stats['failed'],
        'story_book_change': story_book_change,
        'story_completed_change': story_completed_change,
        'story_failed_change': story_failed_change,
        'story_books_this_month': story_stats['this_month'],
        'story_completed_this_month': story_stats['completed_this_month'],
        'story_failed_this_month': story_stats['failed_this_month'],
        'total_users_count': total_users_count,
        'weeks_data_json': weeks_data_json,
        'story_config_json': story_config_json,
        'current_day_of_week': current_day_of_week,
    }
    
    return render(request, "demos/home/dashboard.html", context)