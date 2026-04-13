from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import BaseModel


class User(AbstractUser):
    """
    Utilisateur personnalisé. Étend AbstractUser (auth Django native).
    On n'hérite pas de BaseModel ici car AbstractUser a déjà sa propre
    structure d'id et de dates. On ajoute uniquement public_id manuellement.
    """
    import uuid as _uuid
    email = models.EmailField(unique=True)
    public_id = models.UUIDField(default=_uuid.uuid4, editable=False, unique=True, db_index=True)
    is_online = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return self.username


class Profile(BaseModel):
    """
    Informations sociales de l'utilisateur.
    Créé automatiquement via signal à la création de l'utilisateur.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    location = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'

    def __str__(self):
        return f'Profil de {self.user.username}'
