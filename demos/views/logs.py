from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from logs.models import Log
import json

@login_required(login_url='admin_login')
def get_logs(request):
    logs = Log.objects.all().order_by('-created_at')
    context = {
        'logs': logs
    }
    return render(request, "demos/logs/logs.html", context)


@login_required(login_url='admin_login')
@require_POST
def delete_logs(request):
    try:
        log_ids_json = request.POST.get('log_ids')
        log_ids = json.loads(log_ids_json)
        
        if not log_ids:
            return JsonResponse({
                'success': False,
                'message': 'No logs selected'
            })
        
        deleted_count = Log.objects.filter(id__in=log_ids).delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} log(s) deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting logs: {str(e)}'
        })