from django.urls import path

from . import views

app_name = 'social'

urlpatterns = [
    path('<str:username>/follow/', views.FollowToggleView.as_view(), name='follow'),
    path('<str:username>/followers/', views.FollowersListView.as_view(), name='followers'),
    path('<str:username>/following/', views.FollowingListView.as_view(), name='following'),
]
