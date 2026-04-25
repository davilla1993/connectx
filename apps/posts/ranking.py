"""
Classement du feed — EdgeRank simplifié.

rank(post, moi) = affinity(moi, auteur) * weight(type) * engagement(post) * decay(age)

Calcul en Python après avoir chargé les posts annotés (likes/comments/images counts).
Échelle raisonnable car la fenêtre du feed est de 72h + limité à 500 posts candidats.
"""
import math
from datetime import timedelta
from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone

from .models import Like, Post

FEED_WINDOW_HOURS = 72
MAX_CANDIDATES = 500
DECAY_TAU_HOURS = 24.0


def _affinity(user, author_id, affinity_map):
    """Nb d'interactions (likes+commentaires) du user avec l'auteur — log-normalisé."""
    raw = affinity_map.get(author_id, 0)
    return 1.0 + math.log1p(raw)


def _weight_type(has_images):
    return 1.2 if has_images else 1.0


def _engagement(likes, comments):
    return 1.0 + math.log1p(likes + 2 * comments)


def _decay(age_hours):
    return math.exp(-age_hours / DECAY_TAU_HOURS)


def build_affinity_map(user):
    """Compte pour chaque auteur : mes likes + mes commentaires envers ses posts."""
    from posts.models import Comment
    likes = (
        Like.objects
        .filter(user=user, is_deleted=False)
        .values('post__author_id')
        .annotate(n=Count('id'))
    )
    comments = (
        Comment.objects
        .filter(author=user, is_deleted=False)
        .values('post__author_id')
        .annotate(n=Count('id'))
    )
    m = {}
    for row in likes:
        m[row['post__author_id']] = m.get(row['post__author_id'], 0) + row['n']
    for row in comments:
        m[row['post__author_id']] = m.get(row['post__author_id'], 0) + 2 * row['n']
    return m


def ranked_feed(user, following_ids, limit=20, before=None):
    """
    Retourne une liste de Post triés par score (desc), paginée par curseur `before`
    (datetime du dernier post déjà affiché).
    """
    window_start = timezone.now() - timedelta(hours=FEED_WINDOW_HOURS)
    liked_sub = Like.objects.filter(
        post=OuterRef('pk'), user=user, is_deleted=False
    )

    author_ids = list(following_ids) + [user.id]
    qs = (
        Post.objects
        .filter(
            is_deleted=False,
            author_id__in=author_ids,
            created_at__gte=window_start,
        )
        .select_related('author', 'author__profile')
        .prefetch_related('images')
        .annotate(
            user_liked=Exists(liked_sub),
            likes_total=Count('likes', filter=Q(likes__is_deleted=False), distinct=True),
            comments_total=Count('comments', filter=Q(comments__is_deleted=False), distinct=True),
            images_total=Count('images', distinct=True),
        )
    )
    if before is not None:
        qs = qs.filter(created_at__lt=before)

    candidates = list(qs.order_by('-created_at')[:MAX_CANDIDATES])

    if not candidates:
        return _fallback_chronological(user, author_ids, limit, before, liked_sub)

    aff_map = build_affinity_map(user)
    now = timezone.now()

    for p in candidates:
        age_h = max(0.0, (now - p.created_at).total_seconds() / 3600.0)
        p.score = (
            _affinity(user, p.author_id, aff_map)
            * _weight_type(p.images_total > 0)
            * _engagement(p.likes_total, p.comments_total)
            * _decay(age_h)
        )

    candidates.sort(key=lambda p: (-p.score, -p.created_at.timestamp()))
    return candidates[:limit]


def _fallback_chronological(user, author_ids, limit, before, liked_sub):
    qs = (
        Post.objects
        .filter(is_deleted=False, author_id__in=author_ids)
        .select_related('author', 'author__profile')
        .prefetch_related('images')
        .annotate(
            user_liked=Exists(liked_sub),
            likes_total=Count('likes', filter=Q(likes__is_deleted=False), distinct=True),
            comments_total=Count('comments', filter=Q(comments__is_deleted=False), distinct=True),
        )
        .order_by('-created_at')
    )
    if before is not None:
        qs = qs.filter(created_at__lt=before)
    return list(qs[:limit])
