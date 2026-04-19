from django.contrib import admin
from .models import Story


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('author', 'caption', 'created_at', 'expires_at', 'is_deleted')
    list_filter = ('is_deleted',)
    search_fields = ('author__username', 'caption')
    readonly_fields = ('created_at', 'updated_at', 'expires_at', 'public_id')
