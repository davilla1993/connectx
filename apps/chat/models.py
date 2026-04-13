from django.conf import settings
from django.db import models

from core.models import BaseModel


class Conversation(BaseModel):
    """
    Conversation privée entre utilisateurs.
    ManyToMany participants : supporte 2 users maintenant, groupes plus tard.
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )

    class Meta:
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']

    def __str__(self):
        usernames = ', '.join(u.username for u in self.participants.all())
        return f'Conversation [{usernames}]'

    def get_other_participant(self, user):
        """Retourne l'autre participant dans une conversation à 2."""
        return self.participants.exclude(pk=user.pk).first()


class Message(BaseModel):
    """
    Message envoyé dans une conversation.
    is_read : permet d'afficher les notifications de messages non lus.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender} → Conv#{self.conversation_id} : {self.content[:40]}'
