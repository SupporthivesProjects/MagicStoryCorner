from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import connection, IntegrityError, transaction
import json

from stories.models import (
    AIModel,MODEL_TYPE_CHOICES,  ChildAgeRange, StorySetting, StoryPlot, 
    StoryTheme, StoryTone, StoryLength, ImageStyle, 
    LanguageOption, NarratorVoice, StoryEnd
)


@login_required(login_url='admin_login')
def ai_models(request):
    models = AIModel.objects.all().order_by('-created_at')
    
    context = {
        'models': models,
        'types': MODEL_TYPE_CHOICES
    }
    return render(request, 'demos/storyOptions/aimodels.html', context)

@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def model_get(request, model_id):
    try:
        model = AIModel.objects.get(id=model_id)
        return JsonResponse({
            'id': model.id,
            'name': model.name,
            'emoji': model.emoji,
            'alias': model.alias,
            'type': model.type,
            'family': model.family,
            'temperature': model.temperature,
            'apikey': model.apikey,
            'endpoint': model.endpoint,
            'parameters': model.parameters,
            'types': MODEL_TYPE_CHOICES,
        })
    except AIModel.DoesNotExist:
        return JsonResponse({'error': 'Model not found'}, status=404)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def model_create(request):
    try:
        with transaction.atomic():
            name = request.POST.get('name')
            emoji = request.POST.get('emoji', '')
            alias = request.POST.get('alias', '')
            type_ = request.POST.get('type', '')
            family = request.POST.get('family', '')
            temperature = request.POST.get('temperature') or 0.7
            apikey = request.POST.get('apikey', '')
            endpoint = request.POST.get('endpoint', '')
            parameters = request.POST.get('parameters', '')

            if not name:
                return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)

            if parameters:
                try:
                    parameters = json.loads(parameters)
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'error': 'Invalid JSON in parameters'}, status=400)
            else:
                parameters = {}

            model = AIModel.objects.create(
                name=name,
                emoji=emoji,
                alias=alias,
                type=type_,
                family=family,
                temperature=float(temperature),
                apikey=apikey,
                endpoint=endpoint,
                parameters=parameters
            )
            return JsonResponse({'success': True, 'id': model.id, 'message': 'Model created successfully!'})
    except IntegrityError as e:
        return JsonResponse({'success': False, 'error': 'Database error: Duplicate entry'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    

@login_required(login_url='admin_login')
@require_http_methods(['POST', 'PUT'])
def model_update(request, model_id):
    try:
        with transaction.atomic():
            model = AIModel.objects.get(id=model_id)
            
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = {
                    'name': request.POST.get('name'),
                    'emoji': request.POST.get('emoji'),
                    'alias': request.POST.get('alias'),
                    'type': request.POST.get('type'),
                    'family': request.POST.get('family'),
                    'temperature': request.POST.get('temperature'),
                    'apikey': request.POST.get('apikey'),
                    'endpoint': request.POST.get('endpoint'),
                    'parameters': request.POST.get('parameters'),
                    'is_active': request.POST.get('is_active', 'false').lower() == 'true',
                }
            
            if not data.get('name'):
                return JsonResponse({'error': 'Name is required', 'success': False}, status=400)
            
            model.name = data.get('name', model.name)
            model.emoji = data.get('emoji', model.emoji)
            model.alias = data.get('alias', model.alias)
            model.type = data.get('type', model.type)
            model.family = data.get('family', model.family)
            model.is_active = data.get('is_active', model.is_active)
            
            try:
                model.temperature = float(data.get('temperature', model.temperature))
            except (ValueError, TypeError):
                model.temperature = model.temperature
            
            model.apikey = data.get('apikey', model.apikey)
            model.endpoint = data.get('endpoint', model.endpoint)
            
            parameters = data.get('parameters', model.parameters)
            if isinstance(parameters, str) and parameters.strip():
                try:
                    parameters = json.loads(parameters)
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Invalid JSON in parameters', 'success': False}, status=400)
            else:
                parameters = {}
            model.parameters = parameters
            
            model.save()
            
            return JsonResponse({'id': model.id, 'success': True, 'message': 'Model updated successfully!'})
    except AIModel.DoesNotExist:
        return JsonResponse({'error': 'Model not found', 'success': False}, status=404)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry', 'success': False}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['DELETE', 'POST'])
def model_delete(request, model_id):
    try:
        with transaction.atomic():
            model = AIModel.objects.get(id=model_id)
            model_name = model.name
            model.delete()
            return JsonResponse({'success': True, 'message': f'Model "{model_name}" deleted successfully!'})
    except AIModel.DoesNotExist:
        return JsonResponse({'error': 'Model not found', 'success': False}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)



@login_required(login_url='admin_login')
def age_ranges(request):
    age_ranges = ChildAgeRange.objects.all().order_by('-created_at')
    context = {'age_ranges': age_ranges}
    return render(request, 'demos/storyOptions/ageranges.html', context)


@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def age_range_get(request, age_range_id):
    try:
        age_range = ChildAgeRange.objects.get(id=age_range_id)
        return JsonResponse({
            'id': age_range.id,
            'name': age_range.name,
            'emoji': age_range.emoji,
            'content': age_range.content,
            'cost': age_range.cost,
            'icon': age_range.icon.url if age_range.icon else None,
            'is_active': age_range.is_active
        })
    except ChildAgeRange.DoesNotExist:
        return JsonResponse({'error': 'Age range not found', 'success': False}, status=404)


@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def age_range_create(request):
    try:
        with transaction.atomic():
            name = request.POST.get('name', '').strip()
            if not name:
                return JsonResponse({'error': 'Name is required', 'success': False}, status=400)
            
            emoji = request.POST.get('emoji', '').strip()
            content = request.POST.get('content', '').strip()
            is_active = request.POST.get('is_active', 'false').lower() == 'true'
            
            try:
                cost = int(request.POST.get('cost', 0))
                if cost < 0:
                    cost = 0
            except (ValueError, TypeError):
                cost = 0
            
            age_range = ChildAgeRange.objects.create(
                name=name,
                emoji=emoji,
                content=content,
                cost=cost,
                is_active=is_active
            )
            
            return JsonResponse({
                'id': age_range.id,
                'success': True,
                'message': 'Age range created successfully!'
            })
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)


@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def age_range_update(request, age_range_id):
    try:
        with transaction.atomic():
            age_range = ChildAgeRange.objects.get(id=age_range_id)
            
            name = request.POST.get('name', '').strip()
            if not name:
                return JsonResponse({'error': 'Name is required', 'success': False}, status=400)
            
            age_range.name = name
            age_range.emoji = request.POST.get('emoji', '').strip() or age_range.emoji
            age_range.content = request.POST.get('content', '').strip() or age_range.content
            age_range.is_active = request.POST.get('is_active', 'false').lower() == 'true'
            
            try:
                cost = request.POST.get('cost', age_range.cost)
                cost = int(cost) if cost else age_range.cost
                age_range.cost = max(0, cost)
            except (ValueError, TypeError):
                pass
            
            age_range.save()
            
            return JsonResponse({
                'id': age_range.id,
                'success': True,
                'message': 'Age range updated successfully!'
            })
    except ChildAgeRange.DoesNotExist:
        return JsonResponse({'error': 'Age range not found', 'success': False}, status=404)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)


@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def age_range_delete(request, age_range_id):
    try:
        with transaction.atomic():
            age_range = ChildAgeRange.objects.get(id=age_range_id)
            age_range.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Age range deleted successfully!'
            })
    except ChildAgeRange.DoesNotExist:
        return JsonResponse({'error': 'Age range not found', 'success': False}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)


@login_required(login_url='admin_login')
def settings(request):
    settings = StorySetting.objects.all().order_by('-created_at')
    context = {'settings': settings}
    return render(request, 'demos/storyOptions/settings.html', context)

@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def setting_get(request, setting_id):
    try:
        setting = StorySetting.objects.get(id=setting_id)
        return JsonResponse({
            'id': setting.id,
            'name': setting.name,
            'emoji': setting.emoji,
            'content': setting.content,
            'cost': setting.cost,
            'is_active': setting.is_active,
            'success': True
        })
    except StorySetting.DoesNotExist:
        return JsonResponse({'error': 'Setting not found', 'success': False}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def setting_create(request):
    try:
        with transaction.atomic():
            name = request.POST.get('name', '').strip()
            if not name:
                return JsonResponse({'error': 'Name is required', 'success': False}, status=400)
            
            emoji = request.POST.get('emoji', '')
            content = request.POST.get('content', '')
            cost = request.POST.get('cost', '0')
            is_active = request.POST.get('is_active', 'false').lower() == 'true'
            
            try:
                cost = int(cost)
                if cost < 0:
                    cost = 0
            except (ValueError, TypeError):
                cost = 0
            
            setting = StorySetting.objects.create(
                name=name,
                emoji=emoji,
                content=content,
                cost=cost,
                is_active=is_active,
            )
            
            return JsonResponse({
                'id': setting.id,
                'success': True,
                'message': 'Setting created successfully!'
            })
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['POST']) 
def setting_update(request, setting_id):
    try:
        with transaction.atomic():
            setting = StorySetting.objects.get(id=setting_id)
            
            name = request.POST.get('name', '').strip()
            if not name:
                return JsonResponse({'error': 'Name is required', 'success': False}, status=400)
            
            setting.name = name
            setting.emoji = request.POST.get('emoji', setting.emoji)
            setting.content = request.POST.get('content', setting.content)
            setting.is_active = request.POST.get('is_active', 'false').lower() == 'true'
            
            cost = request.POST.get('cost', setting.cost)
            try:
                cost = int(cost)
                if cost < 0:
                    cost = 0
                setting.cost = cost
            except (ValueError, TypeError):
                pass 
            
            setting.save()
            
            return JsonResponse({
                'id': setting.id,
                'success': True,
                'message': 'Setting updated successfully!'
            })
    except StorySetting.DoesNotExist:
        return JsonResponse({'error': 'Setting not found', 'success': False}, status=404)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['DELETE', 'POST'])
def setting_delete(request, setting_id):
    try:
        with transaction.atomic():
            setting = StorySetting.objects.get(id=setting_id)
            setting_name = setting.name
            setting.delete()
            return JsonResponse({
                'success': True,
                'message': f'Setting "{setting_name}" deleted successfully!'
            })
    except StorySetting.DoesNotExist:
        return JsonResponse({'error': 'Setting not found', 'success': False}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)


@login_required(login_url='admin_login')
def plots(request):
    plots = StoryPlot.objects.all().order_by('-created_at')
    context = {'plots': plots}
    return render(request, 'demos/storyOptions/plots.html', context)

@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def plot_get(request, plot_id):
    try:
        plot = StoryPlot.objects.get(id=plot_id)
        return JsonResponse({
            'id': plot.id,
            'name': plot.name,
            'emoji': plot.emoji,
            'content': plot.content,
            'cost': plot.cost,
            'is_active' : plot.is_active,
            'success': True
        })
    except StoryPlot.DoesNotExist:
        return JsonResponse({'error': 'Plot not found', 'success': False}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def plot_create(request):
    try:
        with transaction.atomic():
            name = request.POST.get('name', '').strip()
            if not name:
                return JsonResponse({'error': 'Name is required', 'success': False}, status=400)
            
            emoji = request.POST.get('emoji', '')
            content = request.POST.get('content', '')
            cost = request.POST.get('cost', '0')
            is_active = request.POST.get('is_active', 'false').lower() == 'true'
            
            try:
                cost = int(cost)
                if cost < 0:
                    cost = 0
            except (ValueError, TypeError):
                cost = 0
            
            plot = StoryPlot.objects.create(
                name=name,
                emoji=emoji,
                content=content,
                cost=cost,
                is_active=is_active
            )
            
            return JsonResponse({
                'id': plot.id,
                'success': True,
                'message': 'Plot created successfully!'
            })
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['POST']) 
def plot_update(request, plot_id):
    try:
        with transaction.atomic():
            plot = StoryPlot.objects.get(id=plot_id)
            
            name = request.POST.get('name', '').strip()
            if not name:
                return JsonResponse({'error': 'Name is required', 'success': False}, status=400)
            
            plot.name = name
            plot.emoji = request.POST.get('emoji', plot.emoji)
            plot.content = request.POST.get('content', plot.content)
            plot.is_active = request.POST.get('is_active', 'false').lower() == 'true'
            cost = request.POST.get('cost', plot.cost)
            try:
                cost = int(cost)
                if cost < 0:
                    cost = 0
                plot.cost = cost
            except (ValueError, TypeError):
                pass 
            
            
            plot.save()
            
            return JsonResponse({
                'id': plot.id,
                'success': True,
                'message': 'Plot updated successfully!'
            })
    except StoryPlot.DoesNotExist:
        return JsonResponse({'error': 'Plot not found', 'success': False}, status=404)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['DELETE', 'POST'])
def plot_delete(request, plot_id):
    try:
        with transaction.atomic():
            plot = StoryPlot.objects.get(id=plot_id)
            plot_name = plot.name
            plot.delete()
            return JsonResponse({
                'success': True,
                'message': f'Plot "{plot_name}" deleted successfully!'
            })
    except StoryPlot.DoesNotExist:
        return JsonResponse({'error': 'Plot not found', 'success': False}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)


@login_required(login_url='admin_login')
def themes(request):
    themes = StoryTheme.objects.all().order_by('-created_at')
    context = {'themes': themes}
    return render(request, 'demos/storyOptions/themes.html', context)

@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def theme_get(request, theme_id):
    try:
        theme = StoryTheme.objects.get(id=theme_id)
        return JsonResponse({
            'id': theme.id,
            'name': theme.name,
            'emoji': theme.emoji,
            'content': theme.content,
            'is_active': theme.is_active,
            'cost': theme.cost
        })
    except StoryTheme.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def theme_create(request):
    try:
        with transaction.atomic():
            cost = request.POST.get('cost')
            theme = StoryTheme.objects.create(
                name=request.POST.get('name'),
                emoji=request.POST.get('emoji'),
                content=request.POST.get('content'),
                cost=int(cost) if cost else 0,
                is_active = request.POST.get('is_active', 'false').lower() == 'true'
            )
            return JsonResponse({'id': theme.id, 'success': True})
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def theme_update(request, theme_id):
    try:
        with transaction.atomic():
            theme = StoryTheme.objects.get(id=theme_id)
            theme.name = request.POST.get('name', theme.name)
            theme.emoji = request.POST.get('emoji', theme.emoji)
            theme.content = request.POST.get('content', theme.content)
            theme.is_active = request.POST.get('is_active', 'false').lower() == 'true'

            cost = request.POST.get('cost')
            if cost is not None:
                theme.cost = int(cost)
            theme.save()
            return JsonResponse({'id': theme.id, 'success': True})
    except StoryTheme.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['DELETE', 'POST'])
def theme_delete(request, theme_id):
    try:
        with transaction.atomic():
            theme = StoryTheme.objects.get(id=theme_id)
            theme.delete()
            return JsonResponse({'success': True})
    except StoryTheme.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    
@login_required(login_url='admin_login')
def tones(request):
    tones = StoryTone.objects.all().order_by('-created_at')
    context = {'tones': tones}
    return render(request, 'demos/storyOptions/tones.html', context)

@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def tone_get(request, tone_id):
    try:
        tone = StoryTone.objects.get(id=tone_id)
        return JsonResponse({
            'id': tone.id,
            'name': tone.name,
            'emoji': tone.emoji,
            'content': tone.content,
            'cost': tone.cost,
            'is_active' : tone.is_active
        })
    except StoryTone.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def tone_create(request):
    try:
        with transaction.atomic():
            cost = request.POST.get('cost')
            tone = StoryTone.objects.create(
                name=request.POST.get('name'),
                emoji=request.POST.get('emoji'),
                content=request.POST.get('content'),
                cost=int(cost) if cost else 0,
                is_active = request.POST.get('is_active', 'false').lower() == 'true'
            )
            return JsonResponse({'id': tone.id, 'success': True})
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def tone_update(request, tone_id):
    try:
        with transaction.atomic():
            tone = StoryTone.objects.get(id=tone_id)
            tone.name = request.POST.get('name', tone.name)
            tone.emoji = request.POST.get('emoji', tone.emoji)
            tone.content = request.POST.get('content', tone.content)
            tone.is_active = request.POST.get('is_active', 'false').lower() == 'true'
            cost = request.POST.get('cost')
            if cost is not None:
                tone.cost = int(cost)
            tone.save()
            return JsonResponse({'id': tone.id, 'success': True})
    except StoryTone.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['DELETE', 'POST'])
def tone_delete(request, tone_id):
    try:
        with transaction.atomic():
            tone = StoryTone.objects.get(id=tone_id)
            tone.delete()
            return JsonResponse({'success': True})
    except StoryTone.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


@login_required(login_url='admin_login')
def lengths(request):
    lengths = StoryLength.objects.all().order_by('-created_at')
    context = {'lengths': lengths}
    return render(request, 'demos/storyOptions/lengths.html', context)

@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def length_get(request, length_id):
    try:
        length = StoryLength.objects.get(id=length_id)
        return JsonResponse({
            'id': length.id,
            'name': length.name,
            'emoji': length.emoji,
            'min': length.min,
            'max': length.max,
            'cost': length.cost,
            'is_active': length.is_active
        })
    except StoryLength.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def length_create(request):
    try:
        name = request.POST.get('name', '').strip()
        emoji = request.POST.get('emoji', '').strip()
        min_val = int(request.POST.get('min', 1))
        max_val = int(request.POST.get('max', 10))
        cost = int(request.POST.get('cost', 0))
        is_active = request.POST.get('is_active', 'false').lower() == 'true'
        
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)
        
        if min_val >= max_val:
            return JsonResponse({'error': 'Min must be less than max'}, status=400)
        
        length = StoryLength.objects.create(
            name=name,
            emoji=emoji,
            min=min_val,
            max=max_val,
            cost=cost,
            is_active=is_active
        )
        
        return JsonResponse({
            'id': length.id,
            'success': True,
            'message': f'{name} created successfully'
        })
            
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'details': 'Check server logs for more info'
        }, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def length_update(request, length_id):
    try:
        with transaction.atomic():
            length = StoryLength.objects.get(id=length_id)
            length.name = request.POST.get('name', length.name)
            length.emoji = request.POST.get('emoji', length.emoji)
            length.min = int(request.POST.get('min', length.min))
            length.max = int(request.POST.get('max', length.max))
            length.cost = int(request.POST.get('cost', length.cost))
            length.is_active = request.POST.get('is_active', 'false').lower() == 'true'
            length.save()
            return JsonResponse({'id': length.id, 'success': True})
    except StoryLength.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['DELETE', 'POST'])
def length_delete(request, length_id):
    try:
        with transaction.atomic():
            length = StoryLength.objects.get(id=length_id)
            length.delete()
            return JsonResponse({'success': True})
    except StoryLength.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


@login_required(login_url='admin_login')
def imagestyles(request):
    styles = ImageStyle.objects.all().order_by('-created_at')
    context = {'styles': styles}
    return render(request, 'demos/storyOptions/imagestyles.html', context)

@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def imagestyle_get(request, style_id):
    try:
        style = ImageStyle.objects.get(id=style_id)
        return JsonResponse({
            'id': style.id,
            'name': style.name,
            'cost': style.cost,
            'content': style.content,
            'image': style.image.url if style.image else None,
            'is_active': style.is_active
        })
    except ImageStyle.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def imagestyle_create(request):
    try:
        with transaction.atomic():
            style = ImageStyle(
                name=request.POST.get('name'),
                cost=int(request.POST.get('cost', 0)),
                content=request.POST.get('content', ''),
                is_active = request.POST.get('is_active', 'false').lower() == 'true'
            )

            if 'image' in request.FILES:
                style.image = request.FILES['image']

            style.save()

            return JsonResponse({
                'id': style.id,
                'success': True,
                'image_url': style.image.url if style.image else ''
            })
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def imagestyle_update(request, style_id):
    try:
        with transaction.atomic():
            style = ImageStyle.objects.get(id=style_id)
            style.name = request.POST.get('name', style.name)
            style.cost = int(request.POST.get('cost', style.cost))
            style.content = request.POST.get('content', style.content)
            style.is_active = request.POST.get('is_active', 'false').lower() == 'true'
            if request.FILES.get('image'):
                style.image = request.FILES.get('image')
            style.save()
            return JsonResponse({'id': style.id, 'success': True})
    except ImageStyle.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database error: Duplicate entry'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required(login_url='admin_login')
@require_http_methods(['DELETE', 'POST'])
def imagestyle_delete(request, style_id):
    try:
        with transaction.atomic():
            style = ImageStyle.objects.get(id=style_id)
            style.delete()
            return JsonResponse({'success': True})
    except ImageStyle.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


@login_required(login_url='admin_login')
def languages(request):
    languages = LanguageOption.objects.all().order_by('-created_at')
    context = {'languages': languages}
    return render(request, 'demos/storyOptions/languages.html', context)


@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def language_get(request, language_id):
    try:
        language = LanguageOption.objects.get(id=language_id)
        return JsonResponse({
            'id': language.id,
            'name': language.name,
            'emoji': language.emoji,
            'content': language.content,
            'cost': language.cost,
            'is_active': language.is_active
        })
    except LanguageOption.DoesNotExist:
        return JsonResponse({'error': 'Not found', 'success': False}, status=404)


@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def language_create(request):
    try:
        with transaction.atomic():
            name = request.POST.get('name', '').strip()
            content = request.POST.get('content', '').strip()
            
            if not name or not content:
                return JsonResponse({'error': 'Name and Content are required', 'success': False}, status=400)
            
            if LanguageOption.objects.filter(code=name).exists():
                return JsonResponse({'error': 'A language with this name already exists', 'success': False}, status=400)
            
            is_active = request.POST.get('is_active', 'false').lower() == 'true'
            
            try:
                cost = int(request.POST.get('cost', 0))
                if cost < 0:
                    cost = 0
            except (ValueError, TypeError):
                cost = 0
            
            language = LanguageOption.objects.create(
                name=name,
                code=name,
                emoji=request.POST.get('emoji', ''),
                content=content,
                cost=cost,
                is_active=is_active
            )
        
            return JsonResponse({
                'id': language.id,
                'success': True,
                'message': 'Language created successfully!'
            }, status=200)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database integrity error', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=500)


@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def language_update(request, language_id):
    try:
        with transaction.atomic():
            language = LanguageOption.objects.get(id=language_id)
            
            name = request.POST.get('name', '').strip()
            content = request.POST.get('content', '').strip()
            
            if not name or not content:
                return JsonResponse({'error': 'Name and Content are required', 'success': False}, status=400)
            
            if LanguageOption.objects.filter(code=name).exclude(id=language_id).exists():
                return JsonResponse({'error': 'A language with this name already exists', 'success': False}, status=400)
            
            language.name = name
            language.code = name
            language.emoji = request.POST.get('emoji', '').strip()
            language.content = content
            language.is_active = request.POST.get('is_active', 'false').lower() == 'true'
            
            try:
                cost = request.POST.get('cost', language.cost)
                cost = int(cost) if cost else language.cost
                language.cost = max(0, cost)
            except (ValueError, TypeError):
                pass
            
            language.save()
            
            return JsonResponse({
                'id': language.id,
                'success': True,
                'message': 'Language updated successfully!'
            }, status=200)
    except LanguageOption.DoesNotExist:
        return JsonResponse({'error': 'Language not found', 'success': False}, status=404)
    except IntegrityError as e:
        return JsonResponse({'error': 'Database integrity error', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=500)
    

@login_required(login_url='admin_login')
@require_http_methods(['DELETE', 'POST'])
def language_delete(request, language_id):
    try:
        with transaction.atomic():
            language = LanguageOption.objects.get(id=language_id)
            language.delete()
            return JsonResponse({'success': True})
    except LanguageOption.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


@login_required(login_url='admin_login')
def narrators(request):
    voices = NarratorVoice.objects.all().order_by('-created_at')
    models = AIModel.objects.all()
    context = {'voices': voices, 'models': models}
    return render(request, 'demos/storyOptions/narrators.html', context)


@login_required(login_url='admin_login')
@require_http_methods(['GET'])
def narrator_get(request, voice_id):
    try:
        voice = NarratorVoice.objects.get(id=voice_id)
        return JsonResponse({
            'id': voice.id,
            'name': voice.name,
            'emoji': voice.emoji,
            'vid': voice.vid,
            'voice': voice.voice,
            'cost': voice.cost,
            'model': voice.model.id if voice.model else None,
            'is_active': voice.is_active,
            'success': True
        })
    except NarratorVoice.DoesNotExist:
        return JsonResponse({'error': 'Not found', 'success': False}, status=404)


@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def narrator_create(request):
    try:
        with transaction.atomic():
            name = request.POST.get('name', '').strip()
            model_id = request.POST.get('model')

            if not name:
                return JsonResponse({'error': 'Name is required', 'success': False}, status=400)

            if not model_id:
                return JsonResponse({'error': 'Model is required', 'success': False}, status=400)

            try:
                cost = int(request.POST.get('cost', 0))
                cost = max(0, cost)
            except:
                cost = 0

            is_active = request.POST.get('is_active', 'false').lower() == 'true'

            model = AIModel.objects.get(id=model_id)

            voice = NarratorVoice.objects.create(
                name=name,
                emoji=request.POST.get('emoji', '').strip(),
                vid=request.POST.get('vid', '').strip(),
                voice=request.POST.get('voice', '').strip(),
                cost=cost,
                model=model,
                is_active=is_active
            )

            return JsonResponse({
                'id': voice.id,
                'success': True,
                'message': 'Voice created successfully!'
            })

    except AIModel.DoesNotExist:
        return JsonResponse({'error': 'Selected model not found', 'success': False}, status=404)
    except IntegrityError:
        return JsonResponse({'error': 'Database error: Duplicate entry', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)


@login_required(login_url='admin_login')
@require_http_methods(['POST'])
def narrator_update(request, voice_id):
    try:
        with transaction.atomic():
            voice = NarratorVoice.objects.get(id=voice_id)

            name = request.POST.get('name', '').strip()
            model_id = request.POST.get('model')

            if not name:
                return JsonResponse({'error': 'Name is required', 'success': False}, status=400)

            if not model_id:
                return JsonResponse({'error': 'Model is required', 'success': False}, status=400)

            model = AIModel.objects.get(id=model_id)

            voice.name = name
            voice.emoji = request.POST.get('emoji', '').strip() or voice.emoji
            voice.vid = request.POST.get('vid', '').strip() or voice.vid
            voice.voice = request.POST.get('voice', '').strip() or voice.voice
            voice.is_active = request.POST.get('is_active', 'false').lower() == 'true'
            voice.model = model

            try:
                cost = request.POST.get('cost', voice.cost)
                cost = int(cost) if cost else voice.cost
                voice.cost = max(0, cost)
            except (ValueError, TypeError):
                pass

            voice.save()

            return JsonResponse({
                'id': voice.id,
                'success': True,
                'message': 'Voice updated successfully!'
            })

    except NarratorVoice.DoesNotExist:
        return JsonResponse({'error': 'Voice not found', 'success': False}, status=404)
    except AIModel.DoesNotExist:
        return JsonResponse({'error': 'Model not found', 'success': False}, status=404)
    except IntegrityError:
        return JsonResponse({'error': 'Database error: Duplicate entry', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=400)


@login_required(login_url='admin_login')
@require_http_methods(['DELETE', 'POST'])
def narrator_delete(request, voice_id):
    try:
        with transaction.atomic():
            voice = NarratorVoice.objects.get(id=voice_id)
            voice.delete()
            return JsonResponse({'success': True})
    except NarratorVoice.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)