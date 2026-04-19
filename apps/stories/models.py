from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import BaseModel

STORY_DURATION_HOURS = 24


class Story(BaseModel):
    """
    Story : contenu éphémère visible pendant 24 heures.

    author     : utilisateur qui publie la story
    image      : photo obligatoire (format libre)
    caption    : légende optionnelle (max 200 caractères)
    expires_at : calculé automatiquement à la création (created_at + 24h)
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stories',
    )
    image = models.ImageField(upload_to='stories/')
    caption = models.CharField(max_length=200, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Story'
        verbose_name_plural = 'Stories'
        ordering = ['-created_at']

    def __str__(self):
        return f'Story de {self.author} ({self.created_at:%d/%m/%Y %H:%M})'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(hours=STORY_DURATION_HOURS)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def time_remaining(self):
        """Durée restante avant expiration (timedelta ou None si expirée)."""
        delta = self.expires_at - timezone.now()
        return delta if delta.total_seconds() > 0 else None
