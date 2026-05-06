from django.shortcuts import render
from payments.models import Order, PaymentTransaction


def get_orders(request):
    orders = Order.objects.all()
    context = {
        "orders": orders
    }
    return render(request, "demos/orders/orders.html", context)


def get_transactions(request):
    transactions = PaymentTransaction.objects.select_related('user', 'order').all()
    context = {
        "transactions": transactions
    }
    return render(request, "demos/orders/transactions.html", context)