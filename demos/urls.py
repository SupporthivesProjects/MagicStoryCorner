from django.urls import path
from . import views

urlpatterns = [

    # admin
    path('', views.admin_login, name='admin_login'),
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('profile/<int:admin_id>/', views.get_admin_profile, name='get_admin_profile'),
    path('my-profile/<int:admin_id>/', views.get_my_profile, name='get_my_profile'),
    path('profile/<int:admin_id>/update-info/', views.update_admin_info, name='update_admin_info'),
    path('profile/<int:admin_id>/update-password/', views.update_admin_password, name='update_admin_password'),
    path('create-admin/', views.create_admin, name='create_admin'),
    path('admin-list/', views.admins, name='admin_list'),

    # logs
    path('logs/', views.get_logs, name='admin_logs'),
    path('logs/delete/', views.delete_logs, name='delete_logs'),

    # configurations
    path('configurations/', views.configurations, name='configurations'),
    path('configurations/save/', views.save_configuration, name='save_configuration'),
    path('configurations/reset/', views.reset_configuration, name='reset_configuration'),

    # books
    path('books/purchased-books/', views.user_purchased_books, name='user_purchased_books'),
    path('books/', views.productbook_list, name='admin_books_list'),
    path('books/create/', views.productbook_create, name='admin_books_create'),
    path('books/<slug:slug>/', views.productbook_get, name='admin_books_detail'),
    path('books/edit/<int:book_id>/', views.productbook_edit, name='edit_product_book'),
    path('books/delete/<int:book_id>/', views.delete_product_book, name='delete_product_book'),
    path('book/<int:book_id>/retry-cover/', views.retry_cover, name='retry_cover'),

    # users
    path('user-list/', views.get_users, name='admin_user_list'),
    path('user-profile/<int:user_id>/', views.get_user_profile, name='get_user_profile'),
    path('update-user/', views.update_user, name='update_user'),
    path('user-stories/', views.user_stories, name='admin_user_books'),
    path('user-story/<str:slug>/', views.user_book_detail, name='user_book_detail'),
    path('user/story/delete/<int:story_id>/', views.delete_user_story, name='delete_user_story'),

    #user wallets
    path('wallets/transactions/', views.user_wallets, name='user_wallets'),
    path('wallet/transactions/get/<int:wallet_id>/', views.wallet_get, name='wallet_get'),
    path('wallet/transactions/create/', views.wallet_create, name='wallet_create'),
    path('wallet/transactions/update/<int:wallet_id>/', views.wallet_update, name='wallet_update'),
    path('wallet/transactions/delete/<int:wallet_id>/', views.wallet_delete, name='wallet_delete'),

    # daily claims
    path('get-users/', views.get_all_users, name='get_all_users'),

    path('daily-claims/', views.daily_claim_list, name='daily_claim_list'),
    path('daily-claims/<int:pk>/', views.daily_claim_get, name='daily_claim_get'),
    path('daily-claims/create/', views.daily_claim_create, name='daily_claim_create'),
    path('daily-claims/<int:pk>/update/', views.daily_claim_update, name='daily_claim_update'),
    path('daily-claims/<int:pk>/delete/', views.daily_claim_delete, name='daily_claim_delete'),

    # referrals
    path('referrals/', views.referral_list, name='referral_list'),
    path('referrals/<int:pk>/', views.referral_get, name='referral_get'),
    path('referrals/create/', views.referral_create, name='referral_create'),
    path('referrals/<int:pk>/update/', views.referral_update, name='referral_update'),
    path('referrals/<int:pk>/delete/', views.referral_delete, name='referral_delete'),

    # referral codes
    path('referral-codes/', views.referral_code_list, name='referral_code_list'),
    path('referral-codes/<int:pk>/', views.referral_code_get, name='referral_code_get'),
    path('referral-codes/create/', views.referral_code_create, name='referral_code_create'),
    path('referral-codes/<int:pk>/update/', views.referral_code_update, name='referral_code_update'),
    path('referral-codes/<int:pk>/delete/', views.referral_code_delete, name='referral_code_delete'),

    # legal
    path('legal/', views.legal_list, name='legal_list'),
    path('legal/get/<int:pk>/', views.legal_get, name='legal_get'),
    path('legal/create/', views.legal_create, name='legal_create'),
    path('legal/update/<int:pk>/', views.legal_update, name='legal_update'),
    path('legal/delete/<int:pk>/', views.legal_delete, name='legal_delete'),

    path('website/', views.website_list, name='website_list'),
    path('website/get/<int:pk>/', views.website_get, name='website_get'),
    path('website/create/', views.website_create, name='website_create'),
    path('website/update/<int:pk>/', views.website_update, name='website_update'),
    path('website/delete/<int:pk>/', views.website_delete, name='website_delete'),

    # orders and coupons
    path('order-list/', views.get_orders, name='admin_order_list'),
    path('transaction-list/', views.get_transactions, name='admin_transaction_list'),
    path('coupons/', views.get_coupons, name='admin_coupon_list'),
    path('coupons/create/', views.coupon_create, name='admin_coupon_create'),
    path('coupons/edit/<int:coupon_id>/', views.coupon_edit, name='admin_coupon_edit'),
    path('coupons/toggle/<int:coupon_id>/', views.coupon_toggle, name='admin_coupon_toggle'),

    # packages
    path('admin/package-types/', views.packagetype_list, name='packagetype_list'),
    path('admin/package-types/get/<int:pk>/', views.packagetype_get, name='packagetype_get'),
    path('admin/package-types/create/', views.packagetype_create, name='packagetype_create'),
    path('admin/package-types/update/<int:pk>/', views.packagetype_update, name='packagetype_update'),

    path('admin/packages/', views.package_list, name='package_list'),
    path('admin/packages/get/<int:pk>/', views.package_get, name='package_get'),
    path('admin/packages/create/', views.package_create, name='package_create'),
    path('admin/packages/update/<int:pk>/', views.package_update, name='package_update'),

    # contacts
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/<int:id>/update/', views.contact_update, name='contact_update'),
    path('contact/<int:id>/reply/', views.contact_reply, name='contact_reply'),
    path('contacts/<int:id>/delete/', views.contact_delete, name='contact_delete'),

    # options - ai models
    path('options/models/', views.ai_models, name='ai_models'),
    path('options/models/<int:model_id>/get/', views.model_get, name='model_get'),
    path('options/models/create/', views.model_create, name='model_create'),
    path('options/models/<int:model_id>/update/', views.model_update, name='model_update'),
    path('options/models/<int:model_id>/delete/', views.model_delete, name='model_delete'),

    # options - age ranges
    path('options/age-ranges/', views.age_ranges, name='age_ranges'),
    path('options/age-ranges/<int:age_range_id>/get/', views.age_range_get, name='age_range_get'),
    path('options/age-ranges/create/', views.age_range_create, name='age_range_create'),
    path('options/age-ranges/<int:age_range_id>/update/', views.age_range_update, name='age_range_update'),
    path('options/age-ranges/<int:age_range_id>/delete/', views.age_range_delete, name='age_range_delete'),

    # options - settings
    path('options/settings/', views.settings, name='settings'),
    path('options/settings/<int:setting_id>/get/', views.setting_get, name='setting_get'),
    path('options/settings/create/', views.setting_create, name='setting_create'),
    path('options/settings/<int:setting_id>/update/', views.setting_update, name='setting_update'),
    path('options/settings/<int:setting_id>/delete/', views.setting_delete, name='setting_delete'),

    # options - plots
    path('options/plots/', views.plots, name='plots'),
    path('options/plots/<int:plot_id>/get/', views.plot_get, name='plot_get'),
    path('options/plots/create/', views.plot_create, name='plot_create'),
    path('options/plots/<int:plot_id>/update/', views.plot_update, name='plot_update'),
    path('options/plots/<int:plot_id>/delete/', views.plot_delete, name='plot_delete'),

    # options - themes
    path('options/themes/', views.themes, name='themes'),
    path('options/themes/<int:theme_id>/get/', views.theme_get, name='theme_get'),
    path('options/themes/create/', views.theme_create, name='theme_create'),
    path('options/themes/<int:theme_id>/update/', views.theme_update, name='theme_update'),
    path('options/themes/<int:theme_id>/delete/', views.theme_delete, name='theme_delete'),

    # options - tones
    path('options/tones/', views.tones, name='tones'),
    path('options/tones/<int:tone_id>/get/', views.tone_get, name='tone_get'),
    path('options/tones/create/', views.tone_create, name='tone_create'),
    path('options/tones/<int:tone_id>/update/', views.tone_update, name='tone_update'),
    path('options/tones/<int:tone_id>/delete/', views.tone_delete, name='tone_delete'),

    # options - lengths
    path('options/lengths/', views.lengths, name='lengths'),
    path('options/lengths/<int:length_id>/get/', views.length_get, name='length_get'),
    path('options/lengths/create/', views.length_create, name='length_create'),
    path('options/lengths/<int:length_id>/update/', views.length_update, name='length_update'),
    path('options/lengths/<int:length_id>/delete/', views.length_delete, name='length_delete'),

    # options - image styles
    path('options/styles/', views.imagestyles, name='imagestyles'),
    path('options/styles/<int:style_id>/get/', views.imagestyle_get, name='imagestyle_get'),
    path('options/styles/create/', views.imagestyle_create, name='imagestyle_create'),
    path('options/styles/<int:style_id>/update/', views.imagestyle_update, name='imagestyle_update'),
    path('options/styles/<int:style_id>/delete/', views.imagestyle_delete, name='imagestyle_delete'),

    # options - languages
    path('options/languages/', views.languages, name='languages'),
    path('options/languages/<int:language_id>/get/', views.language_get, name='language_get'),
    path('options/languages/create/', views.language_create, name='language_create'),
    path('options/languages/<int:language_id>/update/', views.language_update, name='language_update'),
    path('options/languages/<int:language_id>/delete/', views.language_delete, name='language_delete'),

    # options - narrators
    path('options/voices/', views.narrators, name='narrators'),
    path('options/voices/<int:voice_id>/get/', views.narrator_get, name='narrator_get'),
    path('options/voices/create/', views.narrator_create, name='narrator_create'),
    path('options/voices/<int:voice_id>/update/', views.narrator_update, name='narrator_update'),
    path('options/voices/<int:voice_id>/delete/', views.narrator_delete, name='narrator_delete'),
]
