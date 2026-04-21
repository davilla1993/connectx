from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.FeedView.as_view(), name='feed'),
    path('create/', views.PostCreateView.as_view(), name='create'),
    path('<uuid:public_id>/', views.PostDetailView.as_view(), name='detail'),
    path('<uuid:public_id>/delete/', views.PostDeleteView.as_view(), name='delete'),
    path('<uuid:public_id>/like/', views.LikeToggleView.as_view(), name='like'),
    path('<uuid:public_id>/save/', views.SavePostToggleView.as_view(), name='save'),
    path('<uuid:public_id>/react/', views.ReactionToggleView.as_view(), name='react'),
    path('saved/', views.SavedListView.as_view(), name='saved'),
    path('explore/', views.ExploreView.as_view(), name='explore'),
    path('<uuid:public_id>/repost/', views.RepostToggleView.as_view(), name='repost'),
    path('tag/<str:name>/', views.TagDetailView.as_view(), name='tag_detail'),
]
