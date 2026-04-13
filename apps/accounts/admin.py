from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = 'user'
    fields = ('bio', 'avatar', 'location', 'website')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ['username', 'email', 'avatar_preview', 'is_online', 'date_joined', 'is_staff']
    list_filter = ['is_staff', 'is_online', 'date_joined']
    search_fields = ['username', 'email']
    readonly_fields = ['date_joined', 'last_login', 'public_id']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('ConnectX', {'fields': ('public_id', 'is_online')}),
    )

    def avatar_preview(self, obj):
        try:
            if obj.profile.avatar:
                return format_html(
                    '<img src="{}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;">',
                    obj.profile.avatar.url
                )
        except Profile.DoesNotExist:
            pass
        return format_html(
            '<div style="width:32px;height:32px;border-radius:50%;background:#f43f5e;'
            'display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;">'
            '{}</div>', obj.username[0].upper()
        )
    avatar_preview.short_description = 'Avatar'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'created_at']
    search_fields = ['user__username', 'location']
    readonly_fields = ['created_at', 'updated_at', 'public_id']
