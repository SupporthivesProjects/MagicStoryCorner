from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('app-install/',views.app_install, name="app_install"),
    path('about/', views.about, name="about"),
    path('howitworks/', views.howItWorks, name="howItWorks"),
    path('contactus/', views.contactUs, name="contactUs"),


    path('errors/404/', views.error_404, name="error_404"),
    path('errors/500/', views.error_500, name="error_500"),
    path('errors/403/', views.error_403, name="error_403"),
    path('errors/400/', views.error_400, name="error_400"),

]