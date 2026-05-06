from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from accounts.models import  DailyClaim, Referral, ReferralCode, Wallet
from django.db import transaction
from django.utils.timezone import localtime


def admin_login(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        login_input = request.POST.get('username', '').strip() 
        password = request.POST.get('password', '').strip()

        user_obj = None

        if '@' in login_input:
            user_obj = User.objects.filter(email__iexact=login_input).first()
        else:
            user_obj = User.objects.filter(username__iexact=login_input).first()

        if user_obj:
            user = authenticate(
                request,
                username=user_obj.username,
                password=password
            )
        else:
            user = None

        if user is not None:
            if user.is_staff:
                login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Login successful!',
                    'redirect_url': reverse('admin_dashboard')
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You do not have admin access.'
                })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username/email or password.'
            })

    return render(request, "demos/auth/login.html")

@login_required(login_url='admin_login')
def admins(request):
    users = User.objects.filter(is_staff=True).order_by("-id")
    context = {
        "users": users
    }
    return render(request, "demos/auth/admins.html", context)



@login_required(login_url='admin_login')
def get_admin_profile(request, admin_id):
    try:
        user = User.objects.select_related('profile').get(id=admin_id)
        
        stories = user.user_books.all().order_by('-created_at')
        stories_count = stories.count()
        total_users = User.objects.filter(is_staff=False, is_superuser=False).count()
        
        paginator = Paginator(stories, 6)
        page = request.GET.get('page')
        stories_page = paginator.get_page(page)
        
        context = {
            "user": user,
            "stories": stories_page,
            "stories_count": stories_count,
            "total_stories": stories_count,
            "total_users": total_users,
            "total_categories": 0,
            "is_paginated": paginator.num_pages > 1,
            "page_obj": stories_page,
            "is_editable": False,
            "can_update_password": request.user.is_superuser and request.user.is_staff
        }
        return render(request, "demos/auth/profile.html", context)
    
    except User.DoesNotExist:
        messages.error(request, "Admin not found or access denied.")
        return redirect('get_admins')


@login_required(login_url='admin_login')
@require_http_methods(["POST"])
def create_admin(request):
    if not (request.user.is_superuser and request.user.is_staff):
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to create admins.'
        }, status=403)

    try:
        data = json.loads(request.body)

        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        mobile = data.get('mobile', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'admin')

        if not all([first_name, last_name, username, email, password]):
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields.'
            })

        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': 'This username is already taken.'
            })

        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'This email is already in use.'
            })

        if len(password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 8 characters long.'
            })

        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)

        if not (has_letter and has_number and has_special):
            return JsonResponse({
                'success': False,
                'message': 'Password must contain letters, numbers, and special characters.'
            })

        is_superuser = True if role == 'super_admin' else False

        new_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=is_superuser
        )

        try:
            from django.apps import apps
            UserProfile = apps.get_model('app_name', 'UserProfile')
            UserProfile.objects.create(user=new_user, mobile=mobile)
        except LookupError:
            pass

        return JsonResponse({
            'success': True,
            'message': f'{role.replace("_", " ").title()} {first_name} {last_name} created successfully.'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data.'
        }, status=400)

    except Exception:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while creating admin.'
        }, status=500)

    
    
@login_required(login_url='admin_login')
def get_my_profile(request, admin_id):
    try:
        user = User.objects.select_related('profile').get(id=admin_id)
        
        if request.user.id != admin_id:
            messages.error(request, "You can only access your own profile.")
            return redirect('admin_dashboard')
        
        stories = user.user_books.all().order_by('-created_at')
        stories_count = stories.count()
        total_users = User.objects.filter(is_staff=False, is_superuser=False).count()
        
        paginator = Paginator(stories, 6)
        page = request.GET.get('page')
        stories_page = paginator.get_page(page)
        
        context = {
            "user": user,
            "stories": stories_page,
            "stories_count": stories_count,
            "total_stories": stories_count,
            "total_users": total_users,
            "total_categories": 0,
            "is_paginated": paginator.num_pages > 1,
            "page_obj": stories_page,
            "is_editable": True,
            "can_update_password": True
        }
        return render(request, "demos/auth/profile.html", context)
    
    except User.DoesNotExist:
        messages.error(request, "Admin not found or access denied.")
        return redirect('admin_dashboard')


@login_required(login_url='admin_login')
@require_http_methods(["POST"])
def update_admin_info(request, admin_id):
    try:
        target_user = User.objects.select_related('profile').get(
            id=admin_id,
            is_staff=True,
            is_superuser=True
        )
        
        current_user = request.user
        is_own_profile = current_user.id == admin_id
        
        if not is_own_profile:
            return JsonResponse({
                'success': False,
                'message': 'You can only edit your own profile.'
            }, status=403)
        
        data = json.loads(request.body)
        
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        mobile = data.get('mobile', '').strip()
        
        if not first_name or not last_name or not email:
            return JsonResponse({
                'success': False,
                'message': 'Please fill in all required fields.'
            })
        
        if User.objects.filter(email=email).exclude(id=admin_id).exists():
            return JsonResponse({
                'success': False,
                'message': 'This email is already in use.'
            })
        
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.email = email
        target_user.save()
        
        if mobile:
            target_user.profile.mobile = mobile
            target_user.profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully.'
        })
    
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Admin not found.'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating profile.'
        }, status=500)


@login_required(login_url='admin_login')
@require_http_methods(["POST"])
def update_admin_password(request, admin_id):
    try:
        target_user = User.objects.get(
            id=admin_id,
            is_staff=True,
            is_superuser=True
        )
        
        current_user = request.user
        is_own_profile = current_user.id == admin_id
        is_superuser = current_user.is_superuser and current_user.is_staff
        
        if not is_own_profile and not is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to update this password.'
            }, status=403)
        
        data = json.loads(request.body)
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            return JsonResponse({
                'success': False,
                'message': 'Password fields cannot be empty.'
            })
        
        if new_password != confirm_password:
            return JsonResponse({
                'success': False,
                'message': 'Passwords do not match.'
            })
        
        if len(new_password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 8 characters long.'
            })
        
        has_letter = any(c.isalpha() for c in new_password)
        has_number = any(c.isdigit() for c in new_password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in new_password)
        
        if not (has_letter and has_number and has_special):
            return JsonResponse({
                'success': False,
                'message': 'Password must contain letters, numbers, and special characters.'
            })
        
        target_user.set_password(new_password)
        target_user.save()
        
        action = 'Your password has been updated.' if is_own_profile else f'{target_user.get_full_name()}\'s password has been updated.'
        
        return JsonResponse({
            'success': True,
            'message': action
        })
    
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Admin not found.'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating password.'
        }, status=500)


@login_required(login_url='admin_login')
def admin_logout(request):
    logout(request)
    return redirect('admin_login')

@require_http_methods(["GET"])
def get_all_users(request):
    try:
        users = (
            User.objects
            .filter(is_staff=False, is_superuser=False, is_active=True)
            .select_related('profile')
            .order_by('username')
        )

        data = []
        for user in users:
            data.append({
                'id': user.id,
                'username': user.username,
                'wallet': user.profile.wallet or 0,
            })

        return JsonResponse({
            'success': True,
            'users': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def daily_claim_list(request):
    claims = DailyClaim.objects.select_related('user').all()
    return render(request, 'demos/auth/daily_claims.html', {'claims': claims})


@require_http_methods(["GET"])
def daily_claim_get(request, pk):
    claim = get_object_or_404(DailyClaim, pk=pk)
    return JsonResponse({
        'id': claim.id,
        'user_id': claim.user.id,
        'username': claim.user.username,
        'last_claim': claim.last_claim.isoformat() if claim.last_claim else None,
        'claim_count': claim.claim_count,
        'can_claim': claim.can_claim(),
        'created_at': claim.created_at.isoformat(),
        'updated_at': claim.updated_at.isoformat()
    })


@require_http_methods(["POST"])
def daily_claim_create(request):
    try:
        user_id = request.POST.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User is required'}, status=400)
        
        if DailyClaim.objects.filter(user_id=user_id).exists():
            return JsonResponse({'success': False, 'error': 'Daily claim already exists for this user'}, status=400)
        
        claim = DailyClaim.objects.create(
            user_id=user_id,
            last_claim=timezone.now() if request.POST.get('last_claim') else None,
            claim_count=request.POST.get('claim_count', 0)
        )
        
        return JsonResponse({'success': True, 'message': 'Daily claim created successfully!', 'id': claim.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def daily_claim_update(request, pk):
    try:
        claim = get_object_or_404(DailyClaim, pk=pk)
        
        claim.claim_count = request.POST.get('claim_count', claim.claim_count)
        
        if request.POST.get('last_claim'):
            claim.last_claim = timezone.now()
        
        claim.save()
        
        return JsonResponse({'success': True, 'message': 'Daily claim updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def daily_claim_delete(request, pk):
    try:
        claim = get_object_or_404(DailyClaim, pk=pk)
        claim.delete()
        return JsonResponse({'success': True, 'message': 'Daily claim deleted successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def referral_list(request):
    referrals = Referral.objects.select_related('referrer', 'referred').all()
    return render(request, 'demos/auth/referrals.html', {'referrals': referrals})


@require_http_methods(["GET"])
def referral_get(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    return JsonResponse({
        'id': referral.id,
        'referrer_id': referral.referrer.id,
        'referrer_username': referral.referrer.username,
        'referred_id': referral.referred.id,
        'referred_username': referral.referred.username,
        'code': referral.code,
        'purchased': referral.purchased,
        'rewarded': referral.rewarded,
        'reward_at': referral.reward_at.isoformat() if referral.reward_at else None,
        'tokens': referral.tokens,
        'created_at': referral.created_at.isoformat(),
        'updated_at': referral.updated_at.isoformat()
    })


@require_http_methods(["POST"])
def referral_create(request):
    try:
        referrer_id = request.POST.get('referrer_id')
        referred_id = request.POST.get('referred_id')
        code = request.POST.get('code').strip().upper()
        
        if not referrer_id or not referred_id or not code:
            return JsonResponse({'success': False, 'error': 'Referrer, referred user, and code are required'}, status=400)
        
        if referrer_id == referred_id:
            return JsonResponse({'success': False, 'error': 'Referrer and referred user cannot be the same'}, status=400)
        
        referrer = get_object_or_404(User, pk=referrer_id)
        referred = get_object_or_404(User, pk=referred_id)
        
        if Referral.objects.filter(referred=referred).exists():
            return JsonResponse({'success': False, 'error': 'Referred user already has a referral'}, status=400)
        
        referral = Referral.objects.create(
            referrer=referrer,
            referred=referred,
            code=code,
            purchased=request.POST.get('purchased', 'false').lower() == 'true',
            rewarded=request.POST.get('rewarded', 'false').lower() == 'true',
            tokens=request.POST.get('tokens', 0)
        )
        
        return JsonResponse({'success': True, 'message': 'Referral created successfully!', 'id': referral.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def referral_update(request, pk):
    try:
        referral = get_object_or_404(Referral, pk=pk)
        
        referral.code = request.POST.get('code', referral.code).strip().upper()
        referral.purchased = request.POST.get('purchased', 'false').lower() == 'true'
        referral.rewarded = request.POST.get('rewarded', 'false').lower() == 'true'
        referral.tokens = request.POST.get('tokens', referral.tokens)
        
        if request.POST.get('reward_at') and not referral.reward_at:
            referral.reward_at = timezone.now()
        
        referral.save()
        
        return JsonResponse({'success': True, 'message': 'Referral updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
def referral_update(request, pk):
    try:
        referral = get_object_or_404(Referral, pk=pk)
        
        referral.code = request.POST.get('code', referral.code).strip().upper()
        referral.purchased = request.POST.get('purchased', 'false').lower() == 'true'
        referral.rewarded = request.POST.get('rewarded', 'false').lower() == 'true'
        referral.tokens = request.POST.get('tokens', referral.tokens)
        
        if request.POST.get('reward_at') and not referral.reward_at:
            referral.reward_at = timezone.now()
        
        referral.save()
        
        return JsonResponse({'success': True, 'message': 'Referral updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def referral_delete(request, pk):
    try:
        referral = get_object_or_404(Referral, pk=pk)
        referral.delete()
        return JsonResponse({'success': True, 'message': 'Referral deleted successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def referral_code_list(request):
    codes = ReferralCode.objects.select_related('user').all()
    return render(request, 'demos/auth/referral_codes.html', {'codes': codes})


@require_http_methods(["GET"])
def referral_code_get(request, pk):
    ref_code = get_object_or_404(ReferralCode, pk=pk)
    return JsonResponse({
        'id': ref_code.id,
        'user_id': ref_code.user.id,
        'username': ref_code.user.username,
        'code': ref_code.code,
        'referral_count': ref_code.referral_count,
        'tokens_earned': ref_code.tokens_earned,
        'referral_link': ref_code.get_link(),
        'created_at': ref_code.created_at.isoformat(),
        'updated_at': ref_code.updated_at.isoformat()
    })


@require_http_methods(["POST"])
def referral_code_create(request):
    try:
        user_id = request.POST.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User is required'}, status=400)
        
        if ReferralCode.objects.filter(user_id=user_id).exists():
            return JsonResponse({'success': False, 'error': 'Referral code already exists for this user'}, status=400)
        
        code = request.POST.get('code') or ReferralCode.generate()
        
        if ReferralCode.objects.filter(code=code).exists():
            return JsonResponse({'success': False, 'error': 'This code is already taken'}, status=400)
        
        ref_code = ReferralCode.objects.create(
            user_id=user_id,
            code=code,
            referral_count=request.POST.get('referral_count', 0),
            tokens_earned=request.POST.get('tokens_earned', 0)
        )
        
        return JsonResponse({'success': True, 'message': 'Referral code created successfully!', 'id': ref_code.id, 'code': ref_code.code})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def referral_code_update(request, pk):
    try:
        ref_code = get_object_or_404(ReferralCode, pk=pk)
        
        code = request.POST.get('code')
        if code and code != ref_code.code:
            if ReferralCode.objects.filter(code=code).exclude(pk=pk).exists():
                return JsonResponse({'success': False, 'error': 'This code is already taken'}, status=400)
            ref_code.code = code
        
        ref_code.referral_count = request.POST.get('referral_count', ref_code.referral_count)
        ref_code.tokens_earned = request.POST.get('tokens_earned', ref_code.tokens_earned)
        
        ref_code.save()
        
        return JsonResponse({'success': True, 'message': 'Referral code updated successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def referral_code_delete(request, pk):
    try:
        ref_code = get_object_or_404(ReferralCode, pk=pk)
        ref_code.delete()
        return JsonResponse({'success': True, 'message': 'Referral code deleted successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@login_required
def user_wallets(request):
    wallets = Wallet.objects.select_related('user', 'user__profile').all().order_by('-created_at')
    return render(request, 'demos/auth/userwallets.html', {'wallets': wallets})

@login_required
def wallet_get(request, wallet_id):
    try:
        wallet = Wallet.objects.select_related('user', 'user__profile').get(id=wallet_id)
        return JsonResponse({
            'id': wallet.id,
            'user_id': wallet.user.id,
            'type': wallet.type,
            'amount': wallet.amount,
            'balance': wallet.balance,
            'message': wallet.message or '',
            "created_at": localtime(wallet.created_at).strftime("%d %b %Y, %I:%M %p")
        })
    except Wallet.DoesNotExist:
        return JsonResponse({'error': 'Wallet transaction not found'}, status=404)

@login_required
def wallet_create(request):
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            wallet_type = request.POST.get('type')
            amount = int(request.POST.get('amount'))
            message = request.POST.get('message', '').strip()

            if not user_id or not wallet_type or amount <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

            user = User.objects.get(id=user_id)
            
            with transaction.atomic():
                profile = user.profile
                
                if wallet_type == 'recharge':
                    profile.wallet += amount
                else:
                    if profile.wallet < amount:
                        return JsonResponse({'success': False, 'error': 'Insufficient balance'}, status=400)
                    profile.wallet -= amount
                
                profile.save()
                current_balance = profile.wallet
                
                wallet_entry = Wallet.objects.create(
                    user=user,
                    type=wallet_type,
                    amount=amount,
                    balance=current_balance,
                    message=message if message else None
                )

            return JsonResponse({'success': True, 'message': 'Transaction created successfully'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def wallet_update(request, wallet_id):
    if request.method == 'POST':
        try:
            wallet = Wallet.objects.select_related('user', 'user__profile').get(id=wallet_id)
            new_amount = int(request.POST.get('amount'))
            new_message = request.POST.get('message', '').strip()

            if new_amount <= 0:
                return JsonResponse({'success': False, 'error': 'Amount must be greater than 0'}, status=400)

            with transaction.atomic():
                profile = wallet.user.profile
                
                if wallet.type == 'recharge':
                    profile.wallet = profile.wallet - wallet.amount + new_amount
                else:
                    profile.wallet = profile.wallet + wallet.amount - new_amount
                    if profile.wallet < 0:
                        return JsonResponse({'success': False, 'error': 'Insufficient balance for this deduction'}, status=400)
                
                profile.save()
                current_balance = profile.wallet
                
                wallet.amount = new_amount
                wallet.balance = current_balance
                wallet.message = new_message if new_message else None
                wallet.save()

            return JsonResponse({'success': True, 'message': 'Transaction updated successfully'})
        except Wallet.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Wallet transaction not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def wallet_delete(request, wallet_id):
    if request.method == 'POST':
        try:
            wallet = Wallet.objects.get(id=wallet_id)
            wallet.delete()
            return JsonResponse({'success': True, 'message': 'Transaction deleted successfully'})
        except Wallet.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Wallet transaction not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)