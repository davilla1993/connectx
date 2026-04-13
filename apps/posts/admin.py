from django.contrib import admin
from django.utils.html import format_html

from .models import Comment, Like, Post, PostImage


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0
    readonly_fields = ['image_preview', 'created_at']
    fields = ['image', 'image_preview', 'alt_text']

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:6px;">',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Aperçu'


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['author', 'content', 'created_at']
    fields = ['author', 'content', 'is_deleted', 'created_at']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'short_content', 'likes_count', 'comments_count',
                    'is_edited', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'is_edited', 'created_at']
    search_fields = ['author__username', 'content']
    readonly_fields = ['public_id', 'created_at', 'updated_at', 'created_by']
    inlines = [PostImageInline, CommentInline]
    date_hierarchy = 'created_at'

    def short_content(self, obj):
        return obj.content[:60] + '…' if len(obj.content) > 60 else obj.content
    short_content.short_description = 'Contenu'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'short_content', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['author__username', 'content']
    readonly_fields = ['public_id', 'created_at', 'updated_at']

    def short_content(self, obj):
        return obj.content[:60] + '…' if len(obj.content) > 60 else obj.content
    short_content.short_description = 'Contenu'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'is_deleted', 'created_at']
    list_filter = ['is_deleted']
    readonly_fields = ['public_id', 'created_at']
