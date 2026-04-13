from .models import Message


def unread_messages_count(request):
    """
    Injecte le nombre de messages non lus dans tous les templates.
    Utilisé pour afficher le badge dans la navbar.
    """
    if not request.user.is_authenticated:
        return {'unread_messages_count': 0}

    count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False,
        is_deleted=False,
    ).exclude(sender=request.user).count()

    return {'unread_messages_count': count}
