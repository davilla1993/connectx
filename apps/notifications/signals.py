"""
Signaux Django qui créent des notifications à chaque événement social.

Connexions :
  - Like     (post_save) → notifie l'auteur du post
  - Comment  (post_save) → notifie l'auteur du post
  - Follow   (post_save) → notifie l'utilisateur suivi
  - Message  (post_save) → notifie les autres participants de la conversation

On utilise async_to_sync pour envoyer l'événement WebSocket depuis un contexte
synchrone (le signal Django).
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver


def push_notification(notification):
    """Envoie la notification en temps réel via le channel layer."""
    channel_layer = get_channel_layer()
    group_name = f'notif_{notification.recipient_id}'
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'new_notification',
            'id': notification.id,
            'notif_type': notification.notif_type,
            'message': notification.get_message(),
            'sender': notification.sender.username,
        }
    )


# ── Like ─────────────────────────────────────────────────────────────────────

@receiver(post_save, sender='posts.Like')
def on_like(sender, instance, created, **kwargs):
    """Notifie l'auteur d'un post quand quelqu'un like sa publication."""
    from .models import Notification

    # Ne notifie que lors d'une création, pas d'une mise à jour (soft-delete)
    if not created:
        return
    # Ne notifie pas si l'auteur se like lui-même
    if instance.user == instance.post.author:
        return

    notif = Notification.objects.create(
        recipient=instance.post.author,
        sender=instance.user,
        notif_type=Notification.TYPE_LIKE,
        post=instance.post,
        created_by=instance.user,
    )
    push_notification(notif)


# ── Comment ───────────────────────────────────────────────────────────────────

@receiver(post_save, sender='posts.Comment')
def on_comment(sender, instance, created, **kwargs):
    """Notifie l'auteur d'un post quand quelqu'un commente sa publication."""
    from .models import Notification

    if not created:
        return
    if instance.author == instance.post.author:
        return

    notif = Notification.objects.create(
        recipient=instance.post.author,
        sender=instance.author,
        notif_type=Notification.TYPE_COMMENT,
        post=instance.post,
        created_by=instance.author,
    )
    push_notification(notif)


# ── Follow ───────────────────────────────────────────────────────────────────

@receiver(post_save, sender='social.Follow')
def on_follow(sender, instance, created, **kwargs):
    """Notifie un utilisateur quand quelqu'un commence à le suivre."""
    from .models import Notification

    if not created:
        return

    notif = Notification.objects.create(
        recipient=instance.following,
        sender=instance.follower,
        notif_type=Notification.TYPE_FOLLOW,
        created_by=instance.follower,
    )
    push_notification(notif)


# ── Message ───────────────────────────────────────────────────────────────────

@receiver(post_save, sender='chat.Message')
def on_message(sender, instance, created, **kwargs):
    """Notifie les autres participants d'une conversation lors d'un nouveau message."""
    from .models import Notification

    if not created:
        return

    recipients = instance.conversation.participants.exclude(pk=instance.sender_id)
    for recipient in recipients:
        notif = Notification.objects.create(
            recipient=recipient,
            sender=instance.sender,
            notif_type=Notification.TYPE_MESSAGE,
            created_by=instance.sender,
        )
        push_notification(notif)
