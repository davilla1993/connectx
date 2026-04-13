import uuid

from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    """
    Modèle abstrait dont héritent tous les modèles de ConnectX.

    Inspiré du pattern BaseEntity Java (JPA / Spring Data).

    Champs d'audit :
    - public_id   : UUID exposé dans les URLs (l'id séquentiel reste en BDD, jamais exposé)
    - created_at  : date de création (auto)
    - updated_at  : date de dernière modification (auto)
    - created_by  : utilisateur qui a créé l'objet
    - updated_by  : utilisateur qui a effectué la dernière modification

    Soft delete (suppression logique) :
    - is_deleted  : l'objet est marqué supprimé sans être effacé en BDD
    - deleted_at  : date de suppression logique
    - deleted_by  : utilisateur qui a supprimé l'objet

    Pourquoi le soft delete ?
    - Permet l'audit complet et la traçabilité.
    - Permet la restauration d'un objet supprimé par erreur.
    - Évite les problèmes de CASCADE non souhaités.
    """

    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # %(class)s est remplacé automatiquement par Django par le nom de la classe fille
    # Cela évite les conflits de related_name entre les classes qui héritent de BaseModel
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_created',
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_updated',
        editable=False,
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_deleted',
        editable=False,
    )

    class Meta:
        abstract = True  # Pas de table en BDD pour BaseModel lui-même
