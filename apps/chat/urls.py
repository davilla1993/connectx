from django.urls import path

from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.ConversationListView.as_view(), name='list'),
    path('<uuid:public_id>/', views.ConversationDetailView.as_view(), name='detail'),
    path('start/<str:username>/', views.StartConversationView.as_view(), name='start'),
]
