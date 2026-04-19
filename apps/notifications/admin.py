from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notif_type', 'sender', 'recipient', 'is_read', 'created_at')
    list_filter = ('notif_type', 'is_read')
    search_fields = ('sender__username', 'recipient__username')
    readonly_fields = ('created_at', 'updated_at', 'public_id')
