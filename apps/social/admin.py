from django.contrib import admin

from .models import Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['follower__username', 'following__username']
    readonly_fields = ['public_id', 'created_at', 'updated_at']
