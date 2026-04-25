"""Filtres de templating : linkify hashtags et mentions."""
import re

from django import template
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

TAG_RE = re.compile(r'(?<!\w)#([A-Za-z0-9_À-ɏ]{2,64})')
MENTION_RE = re.compile(r'(?<!\w)@([A-Za-z0-9_.]{3,30})')


@register.filter(name='linkify')
def linkify(text):
    if not text:
        return ''
    safe = escape(text)

    def _tag(m):
        name = m.group(1)
        url = reverse('posts:tag_detail', args=[name.lower()])
        return f'<a href="{url}" class="cx-tag">#{name}</a>'

    def _mention(m):
        name = m.group(1)
        url = reverse('accounts:user_profile', args=[name])
        return f'<a href="{url}" class="cx-mention">@{name}</a>'

    safe = TAG_RE.sub(_tag, safe)
    safe = MENTION_RE.sub(_mention, safe)
    safe = safe.replace('\n', '<br>')
    return mark_safe(safe)
