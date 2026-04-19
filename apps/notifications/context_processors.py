from .models import Notification


def unread_notifications_count(request):
    """Injecte le nombre de notifications non lues dans tous les templates."""
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}

    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
        is_deleted=False,
    ).count()

    return {'unread_notifications_count': count}
