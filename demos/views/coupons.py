from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from payments.models import Coupon
from django.db import IntegrityError


def get_coupons(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    context = {
        "coupons": coupons
    }
    return render(request, "demos/coupons/coupon_list.html", context)


def coupon_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code').upper()
        discount = request.POST.get('discount')
        startdate = request.POST.get('startdate')
        enddate = request.POST.get('enddate') if request.POST.get('enddate') else None
        is_active = request.POST.get('is_active') == 'on'  

        try:
            coupon = Coupon.objects.create(
                name=name,
                code=code,
                discount=discount,
                startdate=startdate,
                enddate=enddate,
                is_active=is_active
            )
            messages.success(request, f'Coupon "{coupon.name}" created successfully.')
            return redirect('admin_coupon_list')
        except IntegrityError:
            messages.error(request, f'Coupon code "{code}" already exists. Please choose a different code.')
            context = {
                'action': 'Create',
                'name': name,
                'code': code,
                'discount': discount,
                'startdate': startdate,
                'enddate': enddate,
                'is_active': is_active,
            }
            return render(request, "demos/coupons/coupon_form.html", context)
    
    return render(request, "demos/coupons/coupon_form.html", {'action': 'Create'})


def coupon_edit(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        coupon.name = request.POST.get('name')
        coupon.code = request.POST.get('code').upper()
        coupon.discount = request.POST.get('discount')
        coupon.startdate = request.POST.get('startdate')
        coupon.enddate = request.POST.get('enddate') if request.POST.get('enddate') else None
        coupon.is_active = request.POST.get('is_active') == 'on'  # Checkbox value

        try:
            coupon.save()
            messages.success(request, f'Coupon "{coupon.name}" updated successfully.')
            return redirect('admin_coupon_list')
        except IntegrityError:
            messages.error(request, f'Coupon code "{coupon.code}" already exists. Please choose a different code.')
            context = {
                'coupon': coupon,
                'action': 'Edit'
            }
            return render(request, "demos/coupons/coupon_form.html", context)
    
    context = {
        'coupon': coupon,
        'action': 'Edit'
    }
    return render(request, "demos/coupons/coupon_form.html", context)


def coupon_toggle(request, coupon_id):
    if request.method == 'POST':
        coupon = get_object_or_404(Coupon, id=coupon_id)
        coupon.is_active = not coupon.is_active
        coupon.save()
        status = "activated" if coupon.is_active else "deactivated"
        messages.success(request, f'Coupon "{coupon.code}" {status} successfully.')
    return redirect('admin_coupon_list')