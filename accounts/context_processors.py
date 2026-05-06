from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from payments .models import Currency

def loggedin_user(request):
    token_key = request.session.get("auth_token")
    if token_key:
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
            if user.is_active and not user.is_staff:
                return {"logged_in_user": user}
        except Token.DoesNotExist:
            pass
    return {"logged_in_user": None}

def global_currencies(request):
    currencies = Currency.objects.all()

    selected_currency = None

    # 1. Logged-in → profile (only if exists)
    if request.user.is_authenticated and hasattr(request.user, "profile"):
        if request.user.profile.currency:
            selected_currency = request.user.profile.currency

    # 2. Session
    if not selected_currency and request.session.get("currency"):
        selected_currency = Currency.objects.filter(
            code=request.session.get("currency")
        ).first()

    # 3. Default
    if not selected_currency:
        selected_currency = Currency.objects.filter(is_default=True).first()

    return {
        "currencies": currencies,
        "selected_currency": selected_currency
    }