from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # Profile management URLs
    path('profile/create/', views.create_profile_view, name='create_profile'),
    path('profile/', views.profile_page_view, name='profile_page'),
    path('profile/delete/', views.delete_profile_view, name='delete_profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
]




# urlpatterns = [
#     path('accounts/login/', views.login_view, name='account_login'),
#     path('accounts/signup/', views.signup_view, name='account_signup'),
#     path('accounts/logout/', views.logout_view, name='account_logout'),
#     path('accounts/password/reset/', views.password_reset_view, name='account_reset_password'),
#     path('accounts/password/reset/done/', views.password_reset_done_view, name='account_reset_password_done'),
#     path('accounts/password/change/', views.password_change_view, name='account_change_password'),
#     path('accounts/password/change/done/', views.password_change_done_view, name='account_change_password_done'),
#     path('accounts/password/reset/key/<uidb36>/<key>/', views.password_reset_from_key_view, name='account_reset_password_from_key'),
# ]
# Only for reference in the projects templates Below are the urls for the accounts app

# accounts/login
# accounts/signup/
# accounts/logout/
# accounts/password/reset/
# accounts/password/reset/done/
# accounts/password/change/
# accounts/password/change/done/
# accounts/password/reset/key/<uidb36>/<key>/