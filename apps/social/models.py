from django.conf import settings
from django.db import models

from core.models import BaseModel


class Follow(BaseModel):
    """
    Relation de suivi entre deux utilisateurs.
    - follower  : celui qui suit
    - following : celui qui est suivi
    """
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following_relations'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower_relations'
    )

    class Meta:
        verbose_name = 'Abonnement'
        verbose_name_plural = 'Abonnements'
        unique_together = ('follower', 'following')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.follower} → {self.following}'
