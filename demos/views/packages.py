from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from payments.models import PackageType, Package
import json


@login_required
def packagetype_list(request):
    package_types = PackageType.objects.all().order_by('-id')
    return render(request, 'demos/packages/packagetypes.html', {
        'package_types': package_types
    })


@login_required
@require_http_methods(["GET"])
def packagetype_get(request, pk):
    try:
        package_type = get_object_or_404(PackageType, pk=pk)
        return JsonResponse({
            'id': package_type.id,
            'name': package_type.name,
            'description': package_type.description,
            'is_active': package_type.is_active,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def packagetype_create(request):
    try:
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'true'

        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)

        if PackageType.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': 'Package type with this name already exists'}, status=400)

        package_type = PackageType.objects.create(
            name=name,
            description=description,
            is_active=is_active
        )

        return JsonResponse({
            'success': True,
            'message': 'Package type created successfully',
            'id': package_type.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def packagetype_update(request, pk):
    try:
        package_type = get_object_or_404(PackageType, pk=pk)
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'true'

        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)

        if PackageType.objects.filter(name=name).exclude(pk=pk).exists():
            return JsonResponse({'success': False, 'error': 'Package type with this name already exists'}, status=400)

        package_type.name = name
        package_type.description = description
        package_type.is_active = is_active
        package_type.save()

        return JsonResponse({
            'success': True,
            'message': 'Package type updated successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



@login_required
def package_list(request):

    packages = Package.objects.select_related('packagetype').all().order_by('-id')
    package_types = PackageType.objects.filter(is_active=True)
    return render(request, 'demos/packages/packages.html', {
        'packages': packages,
        'package_types': package_types
    })


@login_required
@require_http_methods(["GET"])
def package_get(request, pk):
    try:
        package = get_object_or_404(Package, pk=pk)
        return JsonResponse({
            'id': package.id,
            'packagetype_id': package.packagetype.id,
            'name': package.name,
            'tokens': package.tokens,
            'description': package.description,
            'currency': package.currency,
            'price': str(package.price),
            'order': package.order,
            'is_popular': package.is_popular,
            'is_active': package.is_active,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def package_create(request):
    try:
        packagetype_id = request.POST.get('packagetype_id')
        name = request.POST.get('name', '').strip()
        tokens = request.POST.get('tokens')
        description = request.POST.get('description', '').strip()
        currency = request.POST.get('currency', '$').strip()
        price = request.POST.get('price')
        order = request.POST.get('order', 0)
        is_popular = request.POST.get('is_popular') == 'true'
        is_active = request.POST.get('is_active') == 'true'
        image = request.FILES.get('image')

        if not packagetype_id:
            return JsonResponse({'success': False, 'error': 'Package type is required'}, status=400)

        if not tokens or int(tokens) < 1:
            return JsonResponse({'success': False, 'error': 'Tokens must be at least 1'}, status=400)

        if not price or float(price) < 0:
            return JsonResponse({'success': False, 'error': 'Price cannot be negative'}, status=400)

        package_type = get_object_or_404(PackageType, pk=packagetype_id)

        package = Package.objects.create(
            packagetype=package_type,
            name=name if name else None,
            tokens=int(tokens),
            description=description if description else None,
            currency=currency,
            price=float(price),
            order=int(order),
            is_popular=is_popular,
            is_active=is_active
        )

        if image:
            package.image = image
            package.save()

        return JsonResponse({
            'success': True,
            'message': 'Package created successfully',
            'id': package.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def package_update(request, pk):
    try:
        package = get_object_or_404(Package, pk=pk)
        packagetype_id = request.POST.get('packagetype_id')
        name = request.POST.get('name', '').strip()
        tokens = request.POST.get('tokens')
        description = request.POST.get('description', '').strip()
        currency = request.POST.get('currency', '$').strip()
        price = request.POST.get('price')
        order = request.POST.get('order', 0)
        is_popular = request.POST.get('is_popular') == 'true'
        is_active = request.POST.get('is_active') == 'true'
        image = request.FILES.get('image')

        if not packagetype_id:
            return JsonResponse({'success': False, 'error': 'Package type is required'}, status=400)

        if not tokens or int(tokens) < 1:
            return JsonResponse({'success': False, 'error': 'Tokens must be at least 1'}, status=400)

        if not price or float(price) < 0:
            return JsonResponse({'success': False, 'error': 'Price cannot be negative'}, status=400)

        package_type = get_object_or_404(PackageType, pk=packagetype_id)

        package.packagetype = package_type
        package.name = name if name else None
        package.tokens = int(tokens)
        package.description = description if description else None
        package.currency = currency
        package.price = float(price)
        package.order = int(order)
        package.is_popular = is_popular
        package.is_active = is_active

        if image:
            package.image = image

        package.save()

        return JsonResponse({
            'success': True,
            'message': 'Package updated successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)