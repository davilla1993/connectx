from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('suggestions/', views.SuggestionsView.as_view(), name='suggestions'),
    # Doit rester en dernier (capture tout les <username>)
    path('<str:username>/', views.UserProfileView.as_view(), name='user_profile'),
]
