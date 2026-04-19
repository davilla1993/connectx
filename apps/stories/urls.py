from django.urls import path
from . import views

app_name = 'stories'

urlpatterns = [
    path('create/', views.StoryCreateView.as_view(), name='create'),
    path('<int:pk>/', views.StoryDetailView.as_view(), name='detail'),
    path('<int:pk>/delete/', views.StoryDeleteView.as_view(), name='delete'),
]
