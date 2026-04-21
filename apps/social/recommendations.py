"""
Recommandation d'utilisateurs à suivre — score hybride FoF + affinité + fraîcheur.

On évite toute dépendance ML : tout se calcule en une passe SQL annotée,
puis est mis en cache par utilisateur pour 1h.
"""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

CACHE_TTL = 60 * 60  # 1h
WEIGHT_FOF = 3.0
WEIGHT_AFFINITY = 1.5
WEIGHT_FRESH = 0.5


def _cache_key(user_id):
    return f'suggestions:user:{user_id}'


def compute_suggestions(user, limit=10):
    """Calcule les meilleurs candidats à suivre pour `user`."""
    my_follows = list(
        user.following_relations
        .filter(is_deleted=False)
        .values_list('following_id', flat=True)
    )
    seven_days_ago = timezone.now() - timedelta(days=7)

    qs = (
        User.objects
        .exclude(pk=user.pk)
        .exclude(pk__in=my_follows)
        .filter(is_active=True, is_staff=False, is_superuser=False)
        .annotate(
            fof=Count(
                'follower_relations',
                filter=Q(follower_relations__follower_id__in=my_follows,
                         follower_relations__is_deleted=False),
                distinct=True,
            ),
            affinity=Count(
                'posts__likes',
                filter=Q(posts__likes__user_id__in=my_follows,
                         posts__likes__is_deleted=False),
                distinct=True,
            ),
            fresh=Count(
                'posts',
                filter=Q(posts__created_at__gte=seven_days_ago,
                         posts__is_deleted=False),
                distinct=True,
            ),
        )
        .select_related('profile')
    )

    scored = []
    for u in qs:
        score = (
            WEIGHT_FOF * u.fof
            + WEIGHT_AFFINITY * u.affinity
            + WEIGHT_FRESH * u.fresh
        )
        if score > 0 or not my_follows:
            scored.append((score, u))

    scored.sort(key=lambda t: (-t[0], -t[1].id))
    return [u for _, u in scored[:limit]]


def get_suggestions(user, limit=5, use_cache=True):
    if not use_cache:
        return compute_suggestions(user, limit=limit)
    key = _cache_key(user.id)
    cached = cache.get(key)
    if cached is not None:
        return cached[:limit]
    full = compute_suggestions(user, limit=max(limit, 10))
    cache.set(key, full, CACHE_TTL)
    return full[:limit]


def invalidate(user_id):
    cache.delete(_cache_key(user_id))
