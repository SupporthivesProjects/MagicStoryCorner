from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from playwright.async_api import async_playwright
import asyncio
import traceback
import sys
from accounts.models import Referral, ReferralCode, Wallet
from accounts.decorators import login_required, verified_required
from logs.models import Log
from payments.helpers.payment_gateway import CitipayGateway, OrderService
from .models import Coupon, Order, OrderItem, OrderStatus, Package, PackageType
from legals.models import Website
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
import base64
from django.core.mail import EmailMultiAlternatives
import traceback
from email.utils import parseaddr


def package_pricing(request):
    ref = request.GET.get("ref")
    if ref:
        request.session["ref_code"] = ref
        request.session.modified = True
    
    packages = Package.objects.select_related('packagetype').filter(is_active=True, order=0).exclude(price=1).order_by('created_at')
    custom_package = Package.objects.select_related('packagetype').filter(is_active=True, price=1)
    bronze_package = Package.objects.filter(is_active=True, order=1).first()
    popular_package = Package.objects.filter(is_active=True, order=2, is_popular=True).first()
    silver_package = Package.objects.filter(is_active=True, order=3).first()

    return render(request, 'payments/package_pricing.html', {
        'packages': packages,
        'bronze_package': bronze_package,
        'popular_package': popular_package,
        'silver_package': silver_package,
        'custom_package': custom_package
    })

@login_required
@verified_required
def order_summary(request):
    cart = request.session.get("cart", {})
    applied_coupon = request.session.get("applied_coupon", None)
    applied_referral = request.session.get("applied_referral", None)
    ref_code = request.session.get("ref_code", None)
    discount_percent = Decimal('0')
    discount_amount = Decimal('0')

    subtotal = sum(Decimal(str(item.get("price", 0))) * Decimal(item.get("quantity", 0)) for item in cart.values())
    total = subtotal

    if request.method == "POST":
        if "remove_code" in request.POST:
            request.session.pop("applied_coupon", None)
            request.session.pop("applied_referral", None)
            request.session.pop("ref_code", None) 
            applied_coupon = None
            applied_referral = None
            discount_percent = Decimal('0')
            discount_amount = Decimal('0')
            total = subtotal
            messages.info(request, "Promo code removed successfully.")
            return redirect("order_summary")

        promo_code = request.POST.get("promo_code", "").strip()
        if promo_code:
            try:
                coupon = Coupon.objects.get(code__iexact=promo_code, is_active=True)
             
                if coupon.startdate > timezone.now():
                    request.session.pop("applied_coupon", None)
                    request.session.pop("applied_referral", None)
                    applied_coupon = None
                    applied_referral = None
                    discount_percent = Decimal('0')
                    discount_amount = Decimal('0')
                    total = subtotal
                    messages.error(request, f"Coupon '{promo_code}' is not yet active.")
           
                elif coupon.enddate and coupon.enddate < timezone.now():
                    request.session.pop("applied_coupon", None)
                    request.session.pop("applied_referral", None)
                    applied_coupon = None
                    applied_referral = None
                    discount_percent = Decimal('0')
                    discount_amount = Decimal('0')
                    total = subtotal
                    messages.error(request, f"Coupon '{promo_code}' has expired.")
                else:
                    discount_percent = coupon.discount
                    discount_amount = subtotal * (discount_percent / Decimal('100'))
                    total = subtotal - discount_amount
                    request.session["applied_coupon"] = coupon.code
                    request.session.pop("applied_referral", None)
                    applied_coupon = coupon.code
                    applied_referral = None
                    messages.success(request, f"Coupon '{coupon.code}' applied! You saved {discount_percent}% (${discount_amount:.2f})")
                    
            except Coupon.DoesNotExist:
                try:
                    with transaction.atomic():
                        referral_code = ReferralCode.objects.select_for_update().get(code__iexact=promo_code)
                        
                        if referral_code.user == request.user:
                            messages.error(request, "You cannot use your own referral code.")
                        elif Referral.objects.filter(referred=request.user).exists():
                            messages.error(request, "You have already used a referral code.")
                        else:
                            request.session["applied_referral"] = referral_code.code
                            request.session.pop("applied_coupon", None)
                            applied_referral = referral_code.code
                            applied_coupon = None
                            discount_percent = Decimal('0')
                            discount_amount = Decimal('0')
                            total = subtotal
                            messages.success(request, f"Referral code '{referral_code.code}' applied! The referrer will receive 100 tokens after your purchase.")
                        
                except ReferralCode.DoesNotExist:
                    request.session.pop("applied_coupon", None)
                    request.session.pop("applied_referral", None)
                    applied_coupon = None
                    applied_referral = None
                    discount_percent = Decimal('0')
                    discount_amount = Decimal('0')
                    total = subtotal
                    messages.error(request, f"Invalid promo code '{promo_code}'. Please check and try again.")

    elif applied_coupon:
        try:
            coupon = Coupon.objects.get(code__iexact=applied_coupon, is_active=True)
            
            if coupon.startdate <= timezone.now() and (not coupon.enddate or coupon.enddate >= timezone.now()):
                discount_percent = coupon.discount
                discount_amount = subtotal * (discount_percent / Decimal('100'))
                total = subtotal - discount_amount
            else:
                request.session.pop("applied_coupon", None)
                applied_coupon = None
                messages.warning(request, f"Your coupon is no longer valid and has been removed.")
        except Coupon.DoesNotExist:
            request.session.pop("applied_coupon", None)
            messages.warning(request, f"Your coupon is no longer available and has been removed.")
            applied_coupon = None
            
    elif applied_referral:
        try:
            referral_code = ReferralCode.objects.get(code__iexact=applied_referral)
            if Referral.objects.filter(referred=request.user).exists():
                request.session.pop("applied_referral", None)
                applied_referral = None
                messages.warning(request, "You have already used a referral code.")
        except ReferralCode.DoesNotExist:
            request.session.pop("applied_referral", None)
            messages.warning(request, f"Your referral code is no longer available and has been removed.")
            applied_referral = None
    
    elif ref_code and not applied_referral and not Referral.objects.filter(referred=request.user).exists():
        try:
            referral_code = ReferralCode.objects.get(code__iexact=ref_code)
            if referral_code.user != request.user:
                request.session["applied_referral"] = referral_code.code
                applied_referral = referral_code.code
        except ReferralCode.DoesNotExist:
            request.session.pop("ref_code", None)

    context = {
        "cart": cart,
        "subtotal": subtotal,
        "savings": discount_amount,
        "discount_percent": discount_percent,
        "total": total,
        "applied_coupon": applied_coupon,
        "applied_referral": applied_referral,
        "applied_code": applied_coupon or applied_referral,
    }

    return render(request, "payments/order_summary.html", context)

@login_required
def add_package_to_cart(request, package_id):
    if request.method == "POST":
        try:
            package = get_object_or_404(Package, id=package_id)
            cart = request.session.get("cart", {})

            if str(package_id) in cart:
                cart[str(package_id)]["quantity"] += 1
            else:
                cart[str(package_id)] = {
                    "id": package.id,
                    "name": package.packagetype.name,
                    "quantity": 1,
                    "price": float(package.price),
                    "tokens": package.tokens
                }

            request.session["cart"] = cart
            request.session.modified = True

            subtotal = sum(item["price"] * item["quantity"] for item in cart.values())
            
            applied_coupon = request.session.get("applied_coupon")
            discount_percent = 0
            savings = 0
            
            if applied_coupon:
                try:
                    coupon = Coupon.objects.get(code__iexact=applied_coupon, is_active=True)
                    if coupon.startdate <= timezone.now() and (not coupon.enddate or coupon.enddate >= timezone.now()):
                        discount_percent = float(coupon.discount)
                        savings = subtotal * (discount_percent / 100)
                except Coupon.DoesNotExist:
                    request.session.pop("applied_coupon", None)
                    discount_percent = 0
                    savings = 0
            
            total = subtotal - savings

            cart_items = [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "tokens": item["tokens"]
                } for item in cart.values()
            ]

            return JsonResponse({
                "success": True,
                "cart_items": cart_items,
                "subtotal": subtotal,
                "savings": savings,
                "discount_percent": discount_percent,
                "total": total
            })

        except Exception as e:
            user_info = f"UserID:{request.user.id}, Username:{request.user.username}" if request.user.is_authenticated else "Anonymous User"
            Log.objects.create(title="Add Package to Cart Error",type="error",message=f"{user_info} | PackageID:{package_id} | Error:{str(e)}")
            return JsonResponse({"success": False, "error": "Something went wrong."}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request."}, status=400)


@login_required
def add_custom_package_to_cart(request):
    if request.method == "POST":
        try:
            package_id = request.POST.get("package_id")
            amount = float(request.POST.get("amount"))
            tokens = int(request.POST.get("tokens"))

            if amount <= 0 or tokens <= 0:
                return JsonResponse({"success": False, "error": "Invalid amount or tokens."}, status=400)

            package = get_object_or_404(Package, id=package_id)
            cart = request.session.get("cart", {})

            if str(package_id) in cart:
                cart[str(package_id)]["price"] += amount
                cart[str(package_id)]["tokens"] += tokens
                cart[str(package_id)]["quantity"] += 1
            else:
                cart[str(package_id)] = {
                    "id": package.id,
                    "name": package.packagetype.name,
                    "quantity": 1,
                    "price": amount,
                    "tokens": tokens
                }

            request.session["cart"] = cart
            request.session.modified = True

            subtotal = sum(item["price"] for item in cart.values())
            
            applied_coupon = request.session.get("applied_coupon")
            discount_percent = 0
            savings = 0
            
            if applied_coupon:
                try:
                    coupon = Coupon.objects.get(code__iexact=applied_coupon, is_active=True)
                    if coupon.startdate <= timezone.now() and (not coupon.enddate or coupon.enddate >= timezone.now()):
                        discount_percent = float(coupon.discount)
                        savings = subtotal * (discount_percent / 100)
                except Coupon.DoesNotExist:
                    request.session.pop("applied_coupon", None)
                    discount_percent = 0
                    savings = 0
            
            total = subtotal - savings

            cart_items = [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "tokens": item["tokens"]
                } for item in cart.values()
            ]

            return JsonResponse({
                "success": True,
                "cart_items": cart_items,
                "subtotal": subtotal,
                "savings": savings,
                "discount_percent": discount_percent,
                "total": total
            })

        except Exception as e:
            user_info = f"UserID:{request.user.id}, Username:{request.user.username}" if request.user.is_authenticated else "Anonymous User"
            Log.objects.create(title="Add Custom Package to Cart Error",type="error",message=f"{user_info} | PackageID:{package_id} | Error:{str(e)}")
            return JsonResponse({"success": False, "error": "Something went wrong."}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request."}, status=400)


@login_required
def remove_from_cart(request, package_id):
    cart = request.session.get("cart", {})
    removed_item_name = None

    if str(package_id) in cart:
        removed_item = cart.pop(str(package_id))
        removed_item_name = removed_item["name"]
        request.session["cart"] = cart
        request.session.modified = True
    else:
        return JsonResponse({"success": False, "error": "Item not found in cart."}, status=400)

    subtotal = sum(item["price"] * item["quantity"] for item in cart.values())
    
    applied_coupon = request.session.get("applied_coupon")
    discount_percent = 0
    savings = 0
    
    if applied_coupon and cart:
        try:
            coupon = Coupon.objects.get(code__iexact=applied_coupon, is_active=True)
            if coupon.startdate <= timezone.now() and (not coupon.enddate or coupon.enddate >= timezone.now()):
                discount_percent = float(coupon.discount)
                savings = subtotal * (discount_percent / 100)
        except Coupon.DoesNotExist:
            request.session.pop("applied_coupon", None)
    
    if not cart:
        request.session.pop("applied_coupon", None)
        request.session.pop("applied_referral", None)
    
    total = subtotal - savings

    cart_items = [
        {
            "id": item["id"],
            "name": item["name"],
            "quantity": item["quantity"],
            "price": item["price"],
            "tokens": item["tokens"]
        } for item in cart.values()
    ]

    return JsonResponse({
        "success": True,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "savings": savings,
        "discount_percent": discount_percent,
        "total": total,
        "removed_item": removed_item_name
    })



@login_required
@verified_required
def billing_information(request):
    user = request.user
    cart = request.session.get("cart", {})
    context = {
        "user": user,
        "cart": cart,
    }
    return render(request, "payments/billing_information.html", context)

@login_required
@verified_required
def payment(request):
    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("order_summary")

    profile = getattr(request.user, "profile", None)

    if request.method == "POST":
        if profile:
            profile.line_1 = request.POST.get("line_1", profile.line_1)
            profile.line_2 = request.POST.get("line_2", profile.line_2)
            profile.city = request.POST.get("city", profile.city)
            profile.postal = request.POST.get("postal", profile.postal)
            profile.save()

        request.user.first_name = request.POST.get("first_name", request.user.first_name)
        request.user.last_name = request.POST.get("last_name", request.user.last_name)
        request.user.email = request.POST.get("email", request.user.email)
        request.user.save()

        applied_coupon_code = request.session.get("applied_coupon")
        applied_referral_code = request.session.get("applied_referral")
        discount_percent = Decimal("0")

        if applied_coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=applied_coupon_code, is_active=True)
                if coupon.startdate <= timezone.now() and (not coupon.enddate or coupon.enddate >= timezone.now()):
                    discount_percent = coupon.discount
                else:
                    request.session.pop("applied_coupon", None)
                    applied_coupon_code = None
                    messages.warning(request, "Your coupon expired. Proceeding without discount.")
            except Coupon.DoesNotExist:
                request.session.pop("applied_coupon", None)
                applied_coupon_code = None
                messages.warning(request, "Your coupon is no longer valid. Proceeding without discount.")

        if applied_referral_code:
            try:
                with transaction.atomic():
                    referral_code_obj = ReferralCode.objects.select_for_update().get(code__iexact=applied_referral_code)
                    
                    if referral_code_obj.user == request.user:
                        request.session.pop("applied_referral", None)
                        applied_referral_code = None
                        messages.warning(request, "Cannot use your own referral code. Proceeding without it.")
                    elif Referral.objects.filter(referred=request.user).exists():
                        request.session.pop("applied_referral", None)
                        applied_referral_code = None
                        messages.warning(request, "You've already used a referral code. Proceeding without it.")
            except ReferralCode.DoesNotExist:
                request.session.pop("applied_referral", None)
                applied_referral_code = None
                messages.warning(request, "Referral code no longer valid. Proceeding without it.")

        try:
            totals = OrderService.calculate_order_totals(cart, discount_percent, apply_gst=False)
            
            order = OrderService.create_pending_order(
                request.user, 
                cart, 
                totals, 
                applied_coupon_code,
                applied_referral_code
            )
            
            gateway = CitipayGateway()
            
            request.session['pending_order_id'] = order.id
            request.session.modified = True
            
            return gateway.render_payment_form(request, order, request.user)

        except Exception as e:
            Log.objects.create(
                title="Payment Error",
                type="error",
                message=str(e)
            )
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect('order_summary')

    return redirect('billing_information')


@csrf_exempt
def payment_callback(request):
    callback_data = request.POST.dict() if request.method == 'POST' else request.GET.dict()
    
    try:
        gateway = CitipayGateway()
        merchant_ref = callback_data.get('MerchantRef', '')
        response_code = callback_data.get('ResponseCode', '')
        response_desc = callback_data.get('ResponseDescription', '')
        transaction_id = callback_data.get('TransactionID', '')

        if not merchant_ref:
            Log.objects.create(
                title='Callback Missing Ref',
                type='error',
                message=f'Data: {callback_data}'
            )
            return HttpResponse('ERROR: Missing MerchantRef', status=400)

        try:
            order = Order.objects.get(id=merchant_ref)
        except Order.DoesNotExist:
            Log.objects.create(
                title='Callback Order Missing',
                type='error',
                message=f'Order {merchant_ref} not found | Data: {callback_data}'
            )
            return HttpResponse('ERROR: Order not found', status=404)

        if order.status == OrderStatus.SUCCESS:
            Log.objects.create(
                title=f'Duplicate Callback #{order.id}',
                type="info",
                message='Order already completed'
            )
            return HttpResponse('OK: Order already processed', status=200)

        if response_code == '0' or response_desc.lower() == 'success':
            try:
                OrderService.complete_order(order, callback_data)
                send_order_invoice_email(order)
                return HttpResponse('OK: Payment processed', status=200)
            except Exception as e:
                Log.objects.create(
                    title=f'Order Completion Error #{order.id}',
                    type='error',
                    message=str(e)
                )
                return HttpResponse('ERROR: Processing failed', status=500)
        else:
            error_msg = response_desc or 'Payment failed'
            OrderService.fail_order(order, callback_data, error_msg)
            Log.objects.create(
                title=f'Callback Failed #{order.id}',
                type='warning',
                message=f'Code: {response_code} | Error: {error_msg} | Txn: {transaction_id}'
            )
            return HttpResponse('OK: Payment failed recorded', status=200)

    except Exception as e:
        Log.objects.create(
            title='Callback Exception',
            type='error',
            message=f'{type(e).__name__}: {str(e)} | Data: {callback_data}'
        )
        return HttpResponse(f'Error: {str(e)}', status=500)



@csrf_exempt
def payment_success(request):
    order_id = request.GET.get('order_id') or request.GET.get('MerchantRef')
    
    if order_id:
        try:
            decoded = base64.urlsafe_b64decode(order_id.encode())
            signer = TimestampSigner()
            order_id = signer.unsign(decoded.decode(), max_age=3600)
        except (BadSignature, SignatureExpired, Exception):
            pass
    
    if not order_id:
        messages.error(request, "Order not found.")
        return redirect("home")

    try:
        order = Order.objects.get(id=order_id)

        # If CitiPay redirected here with a success response and the order is
        # still PENDING (callback hasn't fired yet), complete it now directly.
        if order.status == OrderStatus.PENDING:
            response_code = request.GET.get('ResponseCode', '')
            response_desc = request.GET.get('ResponseDescription', '')
            if response_code == '0' or response_desc.lower() == 'success':
                try:
                    OrderService.complete_order(order, request.GET.dict())
                    send_order_invoice_email(order)
                    order.refresh_from_db()
                except Exception as e:
                    Log.objects.create(title=f'Success-view completion error #{order.id}', type='error', message=str(e))

        user = order.user
        token, _ = Token.objects.get_or_create(user=user)
        request.session["auth_token"] = token.key
        
        if order.status == OrderStatus.SUCCESS:
            processed_key = f'order_processed_{order.id}'
            
            if not request.session.get(processed_key, False):
                request.session.pop('cart', None)
                request.session.pop('pending_order_id', None)
                request.session.pop('applied_coupon', None)
                request.session.pop('applied_referral', None)
                request.session.pop('pending_referral_code', None)
                request.session.pop('ref_code', None)
                request.session[processed_key] = True
                request.session['show_payment_modal'] = True
                request.session.modified = True
                messages.success(
                    request,
                    f"Payment successful! {order.tokens} tokens added to your wallet."
                )
                
                signer = TimestampSigner()
                signed = signer.sign(str(order.id))
                encrypted_order_id = base64.urlsafe_b64encode(signed.encode()).decode()
                return redirect(f"{reverse('payment_success')}?order_id={encrypted_order_id}")
            
            show_modal_flag = request.session.pop('show_payment_modal', False)

            return render(request, 'payments/payment_success.html', {
                'order': order,
                'total_tokens': order.tokens,
                'total_price': float(order.total),
                'auth_token': token.key,
                'show_modal_flag': show_modal_flag
            })

        elif order.status == OrderStatus.PENDING:
            messages.warning(request, "Payment is still being processed. Please wait.")
            return render(request, 'payments/payment_failed.html', {'order': order})

        else:
            messages.error(request, "Payment was not successful.")
            signer = TimestampSigner()
            signed = signer.sign(str(order.id))
            encrypted_order_id = base64.urlsafe_b64encode(signed.encode()).decode()
            return redirect(f"{reverse('payment_failed')}?order_id={encrypted_order_id}")

    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect("home")


@csrf_exempt
def payment_cancel(request):
    order_id = request.GET.get('MerchantRef') or request.GET.get('order_id')
    
    if order_id and '?' in order_id:
        order_id = order_id.split('?')[0]
    
    if order_id:
        try:
            decoded = base64.urlsafe_b64decode(order_id.encode())
            signer = TimestampSigner()
            order_id = signer.unsign(decoded.decode(), max_age=3600)
        except (BadSignature, SignatureExpired, Exception):
            pass
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            user = order.user
            token, _ = Token.objects.get_or_create(user=user)
            request.session["auth_token"] = token.key
            
            processed_key = f'order_cancelled_{order.id}'
            
            if not request.session.get(processed_key, False):
                if order.status == OrderStatus.PENDING:
                    OrderService.cancel_order(order)
                request.session[processed_key] = True
                request.session.pop('pending_order_id', None)
                request.session.pop('applied_coupon', None)
                request.session.pop('applied_referral', None)
                request.session.pop('pending_referral_code', None)
                request.session.modified = True
                messages.info(request, "Payment was cancelled.")
                
                return redirect('order_summary')
            else:
                return redirect('order_summary')
                
        except Order.DoesNotExist as e:
            Log.objects.create(title="Cancel Order Missing", type="error", message=str(e))
        except ValueError as e:
            Log.objects.create(
                title="Cancel Order Invalid ID",
                type="error",
                message=f"Invalid order_id: {order_id} | Error: {str(e)}"
            )
    
    request.session.pop('pending_order_id', None)
    request.session.pop('cart', None)
    request.session.pop('applied_coupon', None)
    request.session.pop('applied_referral', None)
    request.session.pop('pending_referral_code', None)
    request.session.modified = True
    messages.info(request, "Payment was cancelled.")
    return redirect('order_summary')


@csrf_exempt
def payment_failed(request):
    order_id = request.GET.get('MerchantRef') or request.GET.get('order_id')
    
    if order_id and '?' in order_id:
        order_id = order_id.split('?')[0]
    
    if order_id:
        try:
            decoded = base64.urlsafe_b64decode(order_id.encode())
            signer = TimestampSigner()
            order_id = signer.unsign(decoded.decode(), max_age=3600)
        except (BadSignature, SignatureExpired, Exception):
            pass
    
    error_message = request.session.pop('payment_error', 'Payment failed')
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            user = order.user
            token, _ = Token.objects.get_or_create(user=user)
            request.session["auth_token"] = token.key
            
            processed_key = f'order_failed_{order.id}'
            
            if not request.session.get(processed_key, False):
                request.session[processed_key] = True
                request.session.modified = True
                
                if order.status == OrderStatus.PENDING:
                    Log.objects.create(
                        title="Payment Failed - Pending",
                        type="warning",
                        message=f"Order {order.id} still pending | {error_message}"
                    )
                    messages.warning(
                        request,
                        "Payment is still processing. Please check back later."
                    )
                else:
                    Log.objects.create(
                        title="Payment Failed",
                        type="error",
                        message=f"Order {order.id} | {error_message}"
                    )
                    messages.error(request, f"Payment failed: {error_message}")
            
            return render(request, 'payments/payment_failed.html', {'order': order})
            
        except Order.DoesNotExist:
            Log.objects.create(
                title="Failed Order Missing", type="error",message=f"Order {order_id} not found"
            )
        except ValueError as e:
            Log.objects.create(
                title="Failed Order Invalid ID",
                type="error",
                message=f"Invalid order_id: {order_id} | Error: {str(e)}"
            )
    
    messages.error(request, "Payment failed. Please try again.")
    return render(request, "payments/payment_failed.html")


def send_order_invoice_email(order):
    try:
        if not order.items.exists():
            Log.objects.create(
                title='Invoice Email - No Items',
                type='warning',
                message=f'Order {order.id} has no items'
            )
            return False
        
        website = Website.objects.filter(is_active=True).first()
        
        items = order.items.all()
        for item in items:
            item.subtotal = item.price * item.quantity

        invoice_context = {
            'website': website if website else None,
            'order': order,
            'items': items,
        }
       
        html_content = render_to_string('payments/invoices/invoice.html', invoice_context)
       
        pdf_bytes = generate_pdf_from_html(html_content)

        email_context = {
            'user': order.user,
            'order': order,
            'website': website,
            'items': items,
        }
        
        email_body = render_to_string('payments/emails/invoice_email.html', email_context)
        
        raw_admin_email = (
            website.email
            if website and getattr(website, "email", None)
            else settings.DEFAULT_FROM_EMAIL
        )

        subject = f"Your Invoice for Order #{order.id}"

        to_email = []

        if order.user.email:
            to_email.append(order.user.email)

        admin_email = parseaddr(raw_admin_email)[1]
        if admin_email:
            to_email.append(admin_email)

        from_email = raw_admin_email
        
        email = EmailMultiAlternatives(subject, "", from_email, to_email)
        email.attach_alternative(email_body, "text/html")
        email.attach(f"Invoice_{order.id}.pdf", pdf_bytes, 'application/pdf')
        
        email.send()
       
        return True
        
    except Exception as e:
        Log.objects.create(
            title='Invoice Email Send Error',
            type='error',
            message=f'Error sending invoice email for order_id: {order.id}. Error: {str(e)}\n{traceback.format_exc()}'
        )
        return False



@login_required
@verified_required
def download_order_invoice(request, order_id):
    """
    Generate and download invoice PDF on-the-fly without storing
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        if not order.items.exists():
            return JsonResponse({'error': 'No items found in this order. Cannot generate invoice.'}, status=400)
        
        website = Website.objects.filter(is_active=True).first()
        
        items = order.items.all()
        for item in items:
            item.subtotal = item.price * item.quantity

        context = {
            'website': website if website else None,
            'order': order,
            'items': items,
        }
        
        html_content = render_to_string('payments/invoices/invoice.html', context)
        
        pdf_bytes = generate_pdf_from_html(html_content)
        
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_{order.id}.pdf"'
        return response
        
    except Order.DoesNotExist:
        Log.objects.create(title='Invoice Download Failed', type='error', message=f'Order not found for order_id: {order_id}, user: {request.user.username}')
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        Log.objects.create(title='Invoice Generation Error', type='error', message=f'Error generating invoice for order_id: {order_id}, user: {request.user.username}. Error: {str(e)}\n{traceback.format_exc()}')
        return JsonResponse({'error': f'Error generating invoice: {str(e)}'}, status=500)


def generate_pdf_from_html(html_content):
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
    
    try:
        pdf_bytes = asyncio.run(generate_pdf(html_content))
        return pdf_bytes
    except Exception as e:
        Log.objects.create(
            title='PDF Generation Failed',
            type='error',
            message=f'{str(e)}\n{traceback.format_exc()}'
        )
        raise Exception(f"PDF generation failed: {str(e)}")