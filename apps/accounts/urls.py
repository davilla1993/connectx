from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/<uidb64>/<token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Mot de passe oublié
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html', 
                                            email_template_name='accounts/password_reset_email.html',
                                            success_url='/accounts/password-reset/done/'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html',
                                                   success_url='/accounts/password-reset-complete/'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), 
         name='password_reset_complete'),

    # Changement de mot de passe (quand on est connecté)
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html',
                                             success_url='/accounts/password-change-done/'), 
         name='password_change'),
    path('password-change-done/', 
         auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), 
         name='password_change_done'),

    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('suggestions/', views.SuggestionsView.as_view(), name='suggestions'),
    # Doit rester en dernier (capture tout les <username>)
    path('<str:username>/', views.UserProfileView.as_view(), name='user_profile'),
]
