import os

os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connectx.settings')

from django.core.asgi import get_asgi_application

# On initialise Django avant d'importer les consumers Channels
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns as chat_ws
from notifications.routing import websocket_urlpatterns as notif_ws

application = ProtocolTypeRouter({
    # Requêtes HTTP classiques → Django
    'http': django_asgi_app,

    # Connexions WebSocket → Channels
    # AuthMiddlewareStack injecte l'utilisateur Django dans le scope
    'websocket': AuthMiddlewareStack(
        URLRouter(chat_ws + notif_ws)
    ),
})
