from django.utils import timezone
from .models import Log

def logs(request):
    logs = Log.objects.all().order_by("-created_at", "-id")
    return {"logs": logs}


def today_logs(request):
    from django.utils import timezone
    
    today = timezone.localdate()  
    tomorrow = today + timezone.timedelta(days=1)

    logs = Log.objects.filter(
        created_at__gte=today,
        created_at__lt=tomorrow
    ).order_by('-created_at', '-id')

    return {
        "today_logs": logs,
        "today_logs_count": logs.count()
    }


