"""Extraction des hashtags et mentions depuis le texte d'un post."""
import re

from django.contrib.auth import get_user_model

from .models import Mention, PostTag, Tag

TAG_RE = re.compile(r'(?<!\w)#([A-Za-z0-9_À-ɏ]{2,64})')
MENTION_RE = re.compile(r'(?<!\w)@([A-Za-z0-9_.]{3,30})')

User = get_user_model()


def extract_tags(text):
    return {m.group(1).lower() for m in TAG_RE.finditer(text or '')}


def extract_mentions(text):
    return {m.group(1) for m in MENTION_RE.finditer(text or '')}


def apply_to_post(post):
    """Créée les PostTag / Mention pour un post déjà sauvegardé."""
    tag_names = extract_tags(post.content)
    for name in tag_names:
        tag, _ = Tag.objects.get_or_create(name=name, defaults={'created_by': post.author})
        PostTag.objects.get_or_create(
            post=post, tag=tag,
            defaults={'created_by': post.author},
        )
    usernames = extract_mentions(post.content)
    if usernames:
        users = User.objects.filter(username__in=usernames)
        for u in users:
            if u.id != post.author_id:
                Mention.objects.get_or_create(
                    post=post, user=u,
                    defaults={'created_by': post.author},
                )
