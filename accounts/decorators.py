from django.shortcuts import redirect
from django.contrib import messages
from rest_framework.authtoken.models import Token
from logs.models import Log
from functools import wraps

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token_key = request.session.get("auth_token")
        if not token_key:
            messages.error(request, "Login required.")
            return redirect("user_login")
        try:
            token = Token.objects.get(key=token_key)
            request.user = token.user
        except Token.DoesNotExist:
            messages.error(request, "Invalid login session. Please log in again.")
            Log.objects.create(title="Invalid Login Session", type="error", message=f"Token {token_key} does not exist or expired.")
            request.session.flush()
            return redirect("user_login")
        return view_func(request, *args, **kwargs)
    return wrapper


def verified_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user:
            messages.error(request, "Login required.")
            return redirect("user_login")
        
        if not request.user.profile.email_verified:
            messages.error(request, "Please verify your email address.")
            return redirect("user_verification_pending")
        
        return view_func(request, *args, **kwargs)
    return wrapper




def tokens_required(min_balance):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            profile = getattr(request.user, 'profile', None)
            wallet_balance = getattr(profile, 'wallet', 0) if profile else 0

            if wallet_balance < min_balance:
                messages.error(request, f"Insufficient tokens: {wallet_balance}/{min_balance}")
                return redirect('package_pricing')

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
