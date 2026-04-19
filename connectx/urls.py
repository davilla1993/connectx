from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

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
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
