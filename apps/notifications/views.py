from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import View

from accounts.views import SocialLoginRequired
from .models import Notification


class NotificationListView(SocialLoginRequired, View):
    """
    Affiche toutes les notifications de l'utilisateur et les marque comme lues.
    """
    template_name = 'notifications/notification_list.html'

    def get(self, request):
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_deleted=False,
        ).select_related('sender', 'post').order_by('-created_at')

        # Marquer toutes comme lues à l'ouverture de la page
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)

        return render(request, self.template_name, {
            'notifications': notifications,
        })


class NotificationMarkReadView(SocialLoginRequired, View):
    """Marque toutes les notifications comme lues (appelé en AJAX)."""

    def post(self, request):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return JsonResponse({'status': 'ok'})
