import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket pour la messagerie en temps réel.

    Cycle de vie :
      connect()    → authentification + vérification participant → group_add → accept()
      receive()    → sauvegarde BDD → group_send → tous les membres reçoivent
      disconnect() → group_discard

    Sécurité :
      - Connexion refusée si non authentifié.
      - Connexion refusée si l'utilisateur n'est pas participant de la conversation.
    """

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        if not await self.is_participant():
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Signale aux autres membres que cet utilisateur est en ligne
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'user_status', 'username': self.user.username, 'online': True}
        )

    async def disconnect(self, close_code):
        # Guard : room_group_name n'existe pas si connect() a échoué avant group_add
        if not hasattr(self, 'room_group_name'):
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'user_status', 'username': self.user.username, 'online': False}
        )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        # Indicateur de frappe (pas de sauvegarde BDD)
        if 'typing' in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'typing_event', 'username': self.user.username, 'typing': data['typing']}
            )
            return

        content = data.get('message', '').strip()
        if not content:
            return

        message = await self.save_message(content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': content,
                'sender': self.user.username,
                'sender_id': self.user.id,
                'message_id': message.id,
                'created_at': message.created_at.isoformat(),
            }
        )

    async def chat_message(self, event):
        """Diffuse un message texte à ce client."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'message_id': event['message_id'],
            'created_at': event['created_at'],
        }))

    async def user_status(self, event):
        """Diffuse le statut en ligne/hors-ligne d'un participant."""
        await self.send(text_data=json.dumps({
            'type': 'status',
            'username': event['username'],
            'online': event['online'],
        }))

    async def typing_event(self, event):
        """Diffuse l'indicateur de frappe."""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username'],
            'typing': event['typing'],
        }))

    # ------------------------------------------------------------------ #
    # Méthodes BDD (synchrones wrappées en async)                         #
    # ------------------------------------------------------------------ #

    @database_sync_to_async
    def is_participant(self):
        return Conversation.objects.filter(
            id=self.conversation_id,
            participants=self.user,
            is_deleted=False,
        ).exists()

    @database_sync_to_async
    def save_message(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content,
            created_by=self.user,
        )
        conversation.save()  # met à jour updated_at
        return message
