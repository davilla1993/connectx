from channels.generic.websocket import AsyncWebsocketConsumer
import json


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour les notifications en temps réel.

    Chaque utilisateur connecté rejoint son groupe personnel `notif_{user_id}`.
    Quand un signal crée une notification, il envoie un message à ce groupe,
    et ce consumer le transmet immédiatement au client.
    """

    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f'notif_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_notification(self, event):
        """Reçoit un événement du channel layer et le transmet au client WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': event['id'],
            'notif_type': event['notif_type'],
            'message': event['message'],
            'sender': event['sender'],
        }))
