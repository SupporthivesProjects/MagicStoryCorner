from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    
    path('save-age-group/', views.save_age_group, name='save_age_group'),
    path('save-step-one/', views.story_save_step_one, name='story_save_step_one'),
    path('save-step-two/', views.story_save_step_two, name='story_save_step_two'),
    path('save-step-three/', views.story_save_step_three, name='story_save_step_three'),
    path('save-step-four/', views.story_save_step_four, name='story_save_step_four'),
    path('story-book-create/', views.story_book_create, name='story_book_create'),
    path('story-book-view/<slug:slug>/', views.story_book_view, name='story_book_view'),
    path('story/<slug:slug>/download/', views.storybook_download, name='storybook_download'),
]