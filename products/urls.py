from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [

    path('books/', views.product_book_list, name='product_book_list'),
    path('books/<slug:slug>/', views.product_books_details, name='product_books_details'),
    path('book/purchase-book/',views.product_book_purchase , name="purchase_story"),
    path('books/<slug:slug>/download/', views.productbook_download, name='productbook_download'),
]