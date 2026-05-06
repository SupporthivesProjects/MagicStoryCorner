from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('package-pricing/', views.package_pricing, name='package_pricing'),
    path('add-to-cart/<int:package_id>/', views.add_package_to_cart, name='add_package_to_cart'),
    path('add-to-cart/', views.add_custom_package_to_cart, name='add_custom_package_to_cart'),    
    path('remove-from-cart/<int:package_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order-summary/', views.order_summary, name='order_summary'),
    path('billing-information/', views.billing_information, name='billing_information'),

    path('payment/pay/', views.payment, name='payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    
    path('orders/<int:order_id>/download-invoice/', views.download_order_invoice, name='download_order_invoice'),
   
]