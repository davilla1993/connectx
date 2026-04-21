from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),

    # Redirection racine vers le feed
    path('', RedirectView.as_view(pattern_name='posts:feed'), name='home'),

    path('accounts/', include('accounts.urls')),
    path('posts/', include('posts.urls')),
    path('social/', include('social.urls')),
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls')),
    path('stories/', include('stories.urls')),

    # Servir les fichiers media (fonctionne aussi en production avec cette méthode)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
