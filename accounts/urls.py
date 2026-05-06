from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from .views import set_currency

urlpatterns = [

    path('register/', views.user_register, name='user_register'),
    path('email-verification-pending/', views.user_verification_pending, name='user_verification_pending'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification'),
    
    path("verify-email/<str:token>/", views.user_verify_email, name="user_verify_email"),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashbaord/', views.user_dashboard, name='user_dashboard'),
    path('update-profile/', views.user_update_profile, name='user_update_profile'),
    path('update-password/', views.user_password_update, name='user_password_update'),

    path('forgot-password/', views.user_forgot_password, name='user_forgot_password'),
    path('reset-password/<str:token>/', views.user_set_password, name='user_set_password'),
    path('set-currency/', set_currency, name='set_currency'),



    path('library/', views.library_list, name='library_list'),
    path('purchase-history/', views.purchase_history , name='purchase_history'), 
    path('books/view/<slug:slug>/', views.product_book_view_purchased, name='product_book_view_purchased'),          
    path('library/<slug:slug>/', views.library_view, name='library_view'),

    path('claim-daily-reward/', views.claim_daily_reward, name='claim_daily_reward'),
    path('check-claim-status/', views.check_claim_status, name='check_claim_status'),

    path('referral/code/', views.get_referral_code, name='get_referral_code'),
    path('referral/stats/', views.get_referral_stats, name='get_referral_stats'),
    path('referral/validate/', views.validate_referral_code, name='validate_referral_code'),
  
]