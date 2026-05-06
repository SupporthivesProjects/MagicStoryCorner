from demos.views.auth import (
    admin_login,
    admins,
    admin_logout,
    get_admin_profile,
    get_my_profile,
    update_admin_password,
    update_admin_info,
    create_admin,
    get_all_users,

    user_wallets,
    wallet_get,
    wallet_create,
    wallet_update,
    wallet_delete,

    daily_claim_create,
    daily_claim_delete,
    daily_claim_get,
    daily_claim_list,
    daily_claim_update,

    referral_code_create,
    referral_code_delete,
    referral_code_get,
    referral_code_list,
    referral_code_update,

    referral_create,
    referral_delete,
    referral_get,
    referral_list,
    referral_update,
)

from demos.views.dashboard import admin_dashboard

from demos.views.books import (
    retry_cover,
    delete_product_book,
    productbook_list,
    productbook_get,
    productbook_create,
    productbook_edit,
    user_purchased_books,
    configurations,
    save_configuration,
    reset_configuration,
)

from demos.views.coupons import (
    get_coupons,
    coupon_create,
    coupon_edit,
    coupon_toggle,
)

from demos.views.orders import get_orders, get_transactions

from demos.views.users import (
    get_users,
    get_user_profile,
    user_stories,
    update_user,
    user_book_detail,
    delete_user_story,
)

from demos.views.logs import get_logs, delete_logs

from demos.views.contacts import (
    contact_list,
    contact_update,
    contact_reply,
    contact_delete,
)

from demos.views.packages import (
    package_create,
    package_get,
    package_list,
    package_update,
    packagetype_create,
    packagetype_get,
    packagetype_list,
    packagetype_update,
)

from demos.views.legals import (
    legal_get,
    legal_create,
    legal_list,
    legal_update,
    legal_delete,
    website_get,
    website_list,
    website_create,
    website_update,
    website_delete,
)

from .options import (
    ai_models,
    model_get,
    model_create,
    model_update,
    model_delete,

    age_ranges,
    age_range_get,
    age_range_create,
    age_range_update,
    age_range_delete,

    settings,
    setting_get,
    setting_create,
    setting_update,
    setting_delete,

    plots,
    plot_get,
    plot_create,
    plot_update,
    plot_delete,

    themes,
    theme_get,
    theme_create,
    theme_update,
    theme_delete,

    tones,
    tone_get,
    tone_create,
    tone_update,
    tone_delete,

    lengths,
    length_get,
    length_create,
    length_update,
    length_delete,

    imagestyles,
    imagestyle_get,
    imagestyle_create,
    imagestyle_update,
    imagestyle_delete,

    languages,
    language_get,
    language_create,
    language_update,
    language_delete,

    narrators,
    narrator_get,
    narrator_create,
    narrator_update,
    narrator_delete,
)

__all__ = [
    # Admin
    'admin_login',
    'admins',
    'admin_logout',
    'get_admin_profile',
    'get_my_profile',
    'admin_dashboard',
    'update_admin_password',
    'update_admin_info',
    'create_admin',
    'get_all_users',

     # Wallets
    'user_wallets',
    'wallet_get',
    'wallet_create',
    'wallet_update',
    'wallet_delete',

    # Daily Claims
    'daily_claim_create',
    'daily_claim_delete',
    'daily_claim_get',
    'daily_claim_list',
    'daily_claim_update',

    # Referrals
    'referral_code_create',
    'referral_code_delete',
    'referral_code_get',
    'referral_code_list',
    'referral_code_update',
    'referral_create',
    'referral_delete',
    'referral_get',
    'referral_list',
    'referral_update',

    # Books
    'productbook_list',
    'productbook_get',
    'productbook_create',
    'productbook_edit',
    'delete_product_book',
    'user_purchased_books',
    'retry_cover',

    # Coupons
    'get_coupons',
    'coupon_create',
    'coupon_edit',
    'coupon_toggle',

    # Orders
    'get_orders',
    'get_transactions',

    # Packages
    'package_create',
    'package_get',
    'package_list',
    'package_update',
    'packagetype_create',
    'packagetype_get',
    'packagetype_list',
    'packagetype_update',

    # Users
    'get_users',
    'get_user_profile',
    'update_user',
    'user_stories',
    'user_book_detail',
    'delete_user_story',

    # Logs
    'get_logs',
    'delete_logs',

    # Legal / Website
    'legal_get',
    'legal_create',
    'legal_list',
    'legal_update',
    'legal_delete',
    'website_get',
    'website_list',
    'website_create',
    'website_update',
    'website_delete',

    # Configurations
    'configurations',
    'save_configuration',
    'reset_configuration',

    # Contacts
    'contact_list',
    'contact_update',
    'contact_reply',
    'contact_delete',

    # AI Models
    'ai_models',
    'model_get',
    'model_create',
    'model_update',
    'model_delete',

    # Age Ranges
    'age_ranges',
    'age_range_get',
    'age_range_create',
    'age_range_update',
    'age_range_delete',

    # Settings
    'settings',
    'setting_get',
    'setting_create',
    'setting_update',
    'setting_delete',

    # Plots
    'plots',
    'plot_get',
    'plot_create',
    'plot_update',
    'plot_delete',

    # Themes
    'themes',
    'theme_get',
    'theme_create',
    'theme_update',
    'theme_delete',

    # Tones
    'tones',
    'tone_get',
    'tone_create',
    'tone_update',
    'tone_delete',

    # Lengths
    'lengths',
    'length_get',
    'length_create',
    'length_update',
    'length_delete',

    # Image Styles
    'imagestyles',
    'imagestyle_get',
    'imagestyle_create',
    'imagestyle_update',
    'imagestyle_delete',

    # Languages
    'languages',
    'language_get',
    'language_create',
    'language_update',
    'language_delete',

    # Narrators
    'narrators',
    'narrator_get',
    'narrator_create',
    'narrator_update',
    'narrator_delete',
]
