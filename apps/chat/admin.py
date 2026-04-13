from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender', 'content', 'is_read', 'created_at']
    fields = ['sender', 'content', 'is_read', 'is_deleted', 'created_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'participant_list', 'message_count', 'updated_at']
    readonly_fields = ['public_id', 'created_at', 'updated_at']
    inlines = [MessageInline]

    def participant_list(self, obj):
        return ', '.join(u.username for u in obj.participants.all())
    participant_list.short_description = 'Participants'

    def message_count(self, obj):
        return obj.messages.filter(is_deleted=False).count()
    message_count.short_description = 'Messages'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'short_content', 'is_read', 'is_deleted', 'created_at']
    list_filter = ['is_read', 'is_deleted', 'created_at']
    search_fields = ['sender__username', 'content']
    readonly_fields = ['public_id', 'created_at']

    def short_content(self, obj):
        return obj.content[:60] + '…' if len(obj.content) > 60 else obj.content
    short_content.short_description = 'Message'
