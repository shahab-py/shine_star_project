from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import custom_logout, CustomPasswordChangeView


app_name = 'accounts'

urlpatterns = [
    # User Management & Profile
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    
    # Authentication (Login/Logout)
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'), 

    # Password Change (Standard/Custom)
    path('password-change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),

    #Password Reset Flow (The Fixed Part)
     path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset/password_reset.html',
        email_template_name='accounts/password_reset/password_reset_email.html',
        subject_template_name='accounts/password_reset/password_reset_subject.txt',
        success_url='/accounts/password-reset/done/'
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset/password_reset_done.html'
    ), name='password_reset_done'),

    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset/password_reset_confirm.html'
    ), name='password_reset_confirm'), 

    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset/password_reset_complete.html'
    ), name='password_reset_complete'),
]
