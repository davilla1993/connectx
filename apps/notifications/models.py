from django.conf import settings
from django.db import models

from core.models import BaseModel


class Notification(BaseModel):
    """
    Notification déclenchée par une action sociale :
    like, commentaire, nouvel abonné, ou message reçu.

    recipient : utilisateur qui reçoit la notification
    sender    : utilisateur qui a déclenché l'action
    notif_type: catégorie de l'événement
    post      : publication concernée (nullable — absent pour follow/message)
    is_read   : marque la notification comme lue
    """

    TYPE_LIKE     = 'like'
    TYPE_COMMENT  = 'comment'
    TYPE_FOLLOW   = 'follow'
    TYPE_MESSAGE  = 'message'
    TYPE_MENTION  = 'mention'
    TYPE_REACTION = 'reaction'
    TYPE_REPOST   = 'repost'
    TYPE_REPLY    = 'reply'

    NOTIF_TYPES = [
        (TYPE_LIKE,     'Like'),
        (TYPE_COMMENT,  'Commentaire'),
        (TYPE_FOLLOW,   'Abonnement'),
        (TYPE_MESSAGE,  'Message'),
        (TYPE_MENTION,  'Mention'),
        (TYPE_REACTION, 'Réaction'),
        (TYPE_REPOST,   'Repost'),
        (TYPE_REPLY,    'Réponse'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications_received',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications_sent',
    )
    notif_type = models.CharField(max_length=10, choices=NOTIF_TYPES)
    post = models.ForeignKey(
        'posts.Post',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.notif_type}] {self.sender} → {self.recipient}'

    def get_message(self):
        """Retourne le texte de la notification affiché à l'utilisateur."""
        if self.notif_type == self.TYPE_LIKE:
            return f'{self.sender.username} a aimé votre publication.'
        if self.notif_type == self.TYPE_COMMENT:
            return f'{self.sender.username} a commenté votre publication.'
        if self.notif_type == self.TYPE_FOLLOW:
            return f'{self.sender.username} a commencé à vous suivre.'
        if self.notif_type == self.TYPE_MESSAGE:
            return f'{self.sender.username} vous a envoyé un message.'
        if self.notif_type == self.TYPE_MENTION:
            return f'{self.sender.username} vous a mentionné.'
        if self.notif_type == self.TYPE_REACTION:
            return f'{self.sender.username} a réagi à votre publication.'
        if self.notif_type == self.TYPE_REPOST:
            return f'{self.sender.username} a partagé votre publication.'
        if self.notif_type == self.TYPE_REPLY:
            return f'{self.sender.username} a répondu à votre commentaire.'
        return 'Nouvelle notification.'
