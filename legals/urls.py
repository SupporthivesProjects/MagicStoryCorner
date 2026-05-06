from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('cookies-policy/', views.cookies_policy, name='cookies_policy'),
    path('terms-conditions/', views.terms_conditions, name='terms_conditions'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
]