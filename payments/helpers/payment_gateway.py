import hashlib
import hmac
from decimal import Decimal
import traceback
from django.shortcuts import get_object_or_404, render
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import requests
from accounts.emails.helpers import send_referral_reward_email
from legals.models import Website
from accounts.models import Referral, ReferralCode, Wallet
from payments.models import Order, OrderItem, OrderStatus, Package, PaymentTransaction
from logs.models import Log


def convert_currency(amount, currency_obj):
    return Decimal(amount) * Decimal(currency_obj.exchange_rate)

class CitipayGateway:

    CURRENCY_MAP = { '$': 'USD','USD': 'USD'}

    def __init__(self):
        website = Website.objects.filter(is_active=True).first()
        base_url = website.website if website else settings.SITE_URL
        base_url = base_url.rstrip('/')

        self.merchant_name = getattr(settings, 'CITIPAY_MERCHANT_NAME', None)
        self.secret_key = getattr(settings, 'CITIPAY_SECRET_KEY', None)
        self.api_url = getattr(settings, 'CITIPAY_API_URL', None)
        self.payment_url = getattr(settings, 'CITIPAY_PAYMENT_URL', None)

        if not self.secret_key:
            Log.objects.create(title='Missing CITIPAY_SECRET_KEY', type='error', message='CITIPAY_SECRET_KEY not configured')
            raise ValueError("CITIPAY_SECRET_KEY is not configured in settings")
        if not self.merchant_name:
            Log.objects.create(title='Missing CITIPAY_MERCHANT_NAME', type='error', message='CITIPAY_MERCHANT_NAME not configured')
            raise ValueError("CITIPAY_MERCHANT_NAME is not configured in settings")
        if not self.api_url:
            Log.objects.create(title='Missing CITIPAY_API_URL', type='error', message='CITIPAY_API_URL not configured')
            raise ValueError("CITIPAY_API_URL is not configured in settings")

        # Fallback URLs from DB (overridden per-request when request is available)
        self.callback_url = f"{base_url}/payments/payment/callback/"
        self.success_url_base = f"{base_url}/payments/payment/success/"
        self.cancel_url_base = f"{base_url}/payments/payment/cancel/"

    def _get_currency_code(self, currency_symbol):
        return self.CURRENCY_MAP.get(currency_symbol, 'USD')

    def prepare_payment_request(self, order, user, request=None):
        customer_name = f"{user.first_name} {user.last_name}".strip()
        if not customer_name:
            customer_name = user.username

        merchant_ref = str(order.id)
        # currency = self._get_currency_code(order.currency)
        # amount = int(float(order.total) * 100)
        currency = order.currency
        amount = int(Decimal(order.total) * 100)

        concat = f"{self.secret_key}{merchant_ref}{currency}{amount}"
        signature = hashlib.sha1(concat.encode('utf-8')).hexdigest()

        profile = getattr(user, 'profile', None)

        line_1 = profile.line_1 if profile and profile.line_1 else 'Not Provided'
        line_2 = profile.line_2 if profile and profile.line_2 else ''
        city = profile.city if profile and profile.city else 'Not Provided'
        postal = profile.postal if profile and profile.postal else ''
        state = profile.state if profile and profile.state else ''
        country = profile.country if profile and profile.country else 'US'

        # On HTTPS (production), build URLs from the live request so they point
        # to the correct server. On HTTP (local dev), fall back to the DB URL
        # so CitiPay still receives a valid HTTPS URL.
        if request is not None and request.is_secure():
            from django.urls import reverse
            success_url = request.build_absolute_uri(reverse('payment_success')) + f'?order_id={order.id}'
            cancel_url = request.build_absolute_uri(reverse('payment_cancel')) + f'?order_id={order.id}'
            callback_url = request.build_absolute_uri(reverse('payment_callback'))
        else:
            success_url = f"{self.success_url_base}?order_id={order.id}"
            cancel_url = f"{self.cancel_url_base}?order_id={order.id}"
            callback_url = self.callback_url

        params = {
            'MerchantName': str(self.merchant_name),
            'MerchantPassword': str(self.secret_key),
            'MerchantRef': merchant_ref,
            'Firstname': str(user.first_name or user.username),
            'Surname': str(user.last_name or ''),
            'Email': str(user.email),
            'Currency': currency,
            'Amount': str(amount),
            'StreetLine1': str(line_1)[:100],
            'City': str(city)[:50],
            'SuccessURL': success_url,
            'FailURL': cancel_url,
            'CallbackURL': str(callback_url),
            'Signature': signature,
        }

        if line_2:
            params['StreetLine2'] = str(line_2)[:100]
        if postal:
            params['Postcode'] = str(postal)[:20]
        if state:
            params['State'] = str(state)[:50]
        if country:
            country_code = str(country)[:2].upper() if len(str(country)) == 2 else 'US'
            params['Country'] = country_code

        return params

    def get_payment_url(self):
        return self.payment_url

    def get_redirect_url(self, order, user, request=None):
        from urllib.parse import urlencode
        try:
            payment_data = self.prepare_payment_request(order, user, request=request)
            query_string = urlencode(payment_data)
            redirect_url = f"{self.payment_url}?{query_string}"
            return redirect_url
        except Exception as e:
            Log.objects.create(title=f'Redirect URL Generation Failed - Order #{order.id}', type='error', message=str(e))
            raise

    def render_payment_form(self, request, order, user):
        from django.http import HttpResponseRedirect
        try:
            redirect_url = self.get_redirect_url(order, user, request=request)
            return HttpResponseRedirect(redirect_url)
        except Exception as e:
            Log.objects.create(title=f'Payment Redirect Failed - Order #{order.id}', type='error', message=str(e))
            raise

    def _generate_signature(self, params):
        if not self.secret_key:
            raise ValueError("Secret key is not configured")

        sign_params = {k: v for k, v in params.items() if k not in ['Signature', 'Sign']}
        sorted_params = sorted(sign_params.items())
        sign_string = '&'.join(f"{k}={v}" for k, v in sorted_params)

        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def verify_callback(self, callback_data):
        response_code = callback_data.get('ResponseCode', '')
        response_desc = callback_data.get('ResponseDescription', '')
        merchant_ref = callback_data.get('MerchantRef', '')
        transaction_id = callback_data.get('TransactionID', '')

        if response_code != '0' and response_code != '':
            Log.objects.create(title=f'Payment Failed - Order #{merchant_ref}', type='warning', message=f'Code: {response_code}, {response_desc}')
            return False

        received_signature = callback_data.get('Signature') or callback_data.get('Sign')
        if not received_signature:
            if response_code == '0' or response_desc == 'Success':
                return True
            return False

        merchant_password = self.secret_key
        currency = callback_data.get('Currency', '')
        amount = callback_data.get('Amount', '')

        concat = f"{merchant_password}{merchant_ref}{currency}{amount}"
        calculated_signature = hashlib.sha1(concat.encode('utf-8')).hexdigest()

        is_valid = hmac.compare_digest(received_signature.lower(), calculated_signature.lower())

        if not is_valid:
            Log.objects.create(
                title=f'Signature Mismatch - Order #{merchant_ref}',
                type='warning',
                message=f'Received: {received_signature[:16]}..., Expected: {calculated_signature[:16]}...'
            )

        return is_valid

    def get_payment_status(self, transaction_id):
        try:
            params = {
                'MerchantName': str(self.merchant_name),
                'TimeStamp': str(int(timezone.now().timestamp())),
                'TransactionId': str(transaction_id),
            }

            sorted_params = sorted(params.items())
            sign_string = '&'.join(f"{k}={v}" for k, v in sorted_params)

            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                sign_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            params['Signature'] = signature

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
            }

            response = requests.post(
                f"{self.api_url}/query",
                data=params,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            return None
        except requests.Timeout:
            Log.objects.create(
                title=f'Payment Status Query Timeout - Transaction #{transaction_id}',
                type='error',
                message='Request timeout (30s)'
            )
            return None
        except Exception as e:
            Log.objects.create(
                title=f'Payment Status Query Failed - Transaction #{transaction_id}',
                type='error',
                message=str(e)
            )
            return None


class OrderService:
    @staticmethod
    def calculate_order_totals(cart, discount_percent=Decimal("0"), apply_gst=False):
        subtotal = sum(
            Decimal(item["price"]) * Decimal(item.get("quantity", 1))
            for item in cart.values()
        )

        discount_amount = (
            subtotal * (discount_percent / Decimal("100"))
            if discount_percent > 0 else Decimal("0")
        )

        subtotal_after_discount = subtotal - discount_amount

        gst_amount = Decimal("0")
        if apply_gst:
            gst_amount = subtotal_after_discount * Decimal("0.18")

        total_price = subtotal_after_discount + gst_amount

        total_tokens = sum(
            item["tokens"] * item.get("quantity", 1)
            for item in cart.values()
        )

        return {
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'gst_amount': gst_amount,
            'total_price': total_price,
            'total_tokens': total_tokens,
            'total_quantity': sum(item.get("quantity", 1) for item in cart.values()),
        }

    @staticmethod
    def create_pending_order(user, cart, totals, coupon_code=None, referral_code=None):
        with transaction.atomic():
            first_item = list(cart.values())[0] if cart else {}
            # currency = first_item.get('currency', '$')
            currency_obj = user.profile.currency
            currency = currency_obj.code

            order = Order.objects.create(
                user=user,
                quantity=totals['total_quantity'],
                currency=currency,
                tokens=totals['total_tokens'],
                # total=totals['total_price'],
                # discount=totals['discount_amount'],
                # gst=totals['gst_amount'],
                total = convert_currency(totals['total_price'], currency_obj),
                discount = convert_currency(totals['discount_amount'], currency_obj),
                gst = convert_currency(totals['gst_amount'], currency_obj),
                coupon=coupon_code,
                referral=referral_code,
                status=OrderStatus.PENDING,
            )

            for item in cart.values():
                package = get_object_or_404(Package, id=item["id"])
                quantity = item.get("quantity", 1)

                OrderItem.objects.create(
                    order=order,
                    package=package,
                    quantity=quantity,
                    # currency=package.currency,
                    currency = currency,
                    # price=Decimal(item["price"]),
                    price = convert_currency(item["price"], currency_obj),
                    tokens=item["tokens"] * quantity,
                    discount=Decimal("0"),
                )
            return order

    @staticmethod
    def complete_order(order, payment_data):
        try:
            with transaction.atomic():
                order_for_update = Order.objects.select_for_update().get(id=order.id)

                if order_for_update.status == OrderStatus.SUCCESS:
                    Log.objects.create(
                        title=f'Duplicate Order Completion #{order.id}',
                        type='warning',
                        message='Order already completed'
                    )
                    return True

                order_for_update.status = OrderStatus.SUCCESS
                order_for_update.save()

                PaymentTransaction.objects.create(
                    user=order_for_update.user,
                    order=order_for_update,
                    response=payment_data
                )

                profile = order_for_update.user.profile
                profile.wallet += order_for_update.tokens
                profile.save()

                Wallet.objects.create(
                    user=order_for_update.user,
                    type="recharge",
                    amount=order_for_update.tokens,
                    balance=profile.wallet,
                    message=f"Tokens added for Order #{order_for_update.id}"
                )

            if order_for_update.referral:
                try:
                    with transaction.atomic():
                        referral_code_obj = ReferralCode.objects.select_for_update().get(
                            code__iexact=order_for_update.referral
                        )
                        referrer = referral_code_obj.user

                        existing_referral = Referral.objects.select_for_update().filter(
                            referred=order_for_update.user
                        ).first()

                        if existing_referral:
                            Log.objects.create(
                                title=f'Referral Already Exists #{order.id}',
                                type='warning',
                                message=f'User {order_for_update.user.username} already referred'
                            )
                        else:
                            if referrer == order_for_update.user:
                                Log.objects.create(
                                    title=f'Self Referral Attempt #{order.id}',
                                    type='warning',
                                    message='User attempted self-referral'
                                )
                            else:
                                Referral.objects.create(
                                    referrer=referrer,
                                    referred=order_for_update.user,
                                    code=order_for_update.referral,
                                    purchased=True,
                                    rewarded=True,
                                    reward_at=timezone.now(),
                                    tokens=100
                                )

                                referrer_profile = referrer.profile
                                referrer_profile.wallet += 100
                                referrer_profile.save()

                                Wallet.objects.create(
                                    user=referrer,
                                    type='recharge',
                                    amount=100,
                                     balance=referrer_profile.wallet,
                                    message=f"Referral reward for Order #{order_for_update.id}"
                                )

                                referral_code_obj.referral_count += 1
                                referral_code_obj.tokens_earned += 100
                                referral_code_obj.save()

                                try:
                                    send_referral_reward_email(
                                        referrer,
                                        order_for_update.user,
                                        100
                                    )
                                except Exception as email_error:
                                    Log.objects.create(
                                        title=f'Referral Email Failed #{order.id}',
                                        type='warning',
                                        message=str(email_error)
                                    )

                except ReferralCode.DoesNotExist:
                    Log.objects.create(
                        title=f'Referral Code Not Found #{order.id}',
                        type='warning',
                        message=f'Code {order_for_update.referral} not found'
                    )
                except Exception as e:
                    Log.objects.create(
                        title=f'Referral Processing Error #{order.id}',
                        type='error',
                        message=f'{str(e)}\n{traceback.format_exc()}'
                    )

            return True

        except Exception as e:
            Log.objects.create(
                title=f'Order Completion Failed - Order #{order.id}',
                type='error',
                message=f'{str(e)}\n{traceback.format_exc()}'
            )
            raise


    @staticmethod
    def fail_order(order, payment_data, error_message="Payment failed"):
        try:
            with transaction.atomic():
                order.status = OrderStatus.FAILED
                order.save()

                PaymentTransaction.objects.create(
                    user=order.user,
                    order=order,
                    response={**payment_data, 'error_message': error_message}
                )

                Log.objects.create(
                    title=f'Order Failed - Order #{order.id}',
                    type='warning',
                    message=error_message
                )
        except Exception as e:
            Log.objects.create(
                title=f'Order Failure Handling Error - Order #{order.id}',
                type='error',
                message=str(e)
            )

    @staticmethod
    def cancel_order(order):
        order.status = OrderStatus.CANCELLED
        order.save()