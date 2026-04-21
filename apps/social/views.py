from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.views import SocialLoginRequired
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import View

from .models import Follow
from .recommendations import invalidate as invalidate_suggestions

User = get_user_model()


class FollowToggleView(SocialLoginRequired, View):
    """
    Follow / Unfollow. Répond en JSON pour pouvoir être appelé en AJAX.
    """
    def post(self, request, username):
        target = get_object_or_404(User, username=username)

        if target == request.user:
            return JsonResponse({'error': 'Vous ne pouvez pas vous suivre vous-même.'}, status=400)

        follow = Follow.objects.filter(follower=request.user, following=target).first()

        if follow:
            if follow.is_deleted:
                # Re-follow
                follow.is_deleted = False
                follow.deleted_at = None
                follow.deleted_by = None
                follow.save()
                following = True
            else:
                # Unfollow (soft delete)
                follow.is_deleted = True
                follow.deleted_at = timezone.now()
                follow.deleted_by = request.user
                follow.save()
                following = False
        else:
            Follow.objects.create(
                follower=request.user,
                following=target,
                created_by=request.user,
            )
            following = True

        invalidate_suggestions(request.user.id)
        invalidate_suggestions(target.id)

        return JsonResponse({
            'following': following,
            'followers_count': target.follower_relations.filter(is_deleted=False).count(),
        })


class FollowersListView(SocialLoginRequired, View):
    template_name = 'social/followers.html'

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        followers = (
            Follow.objects
            .filter(following=user, is_deleted=False)
            .select_related('follower', 'follower__profile')
        )
        return render(request, self.template_name, {
            'profile_user': user,
            'followers': followers,
        })


class FollowingListView(SocialLoginRequired, View):
    template_name = 'social/following.html'

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        following = (
            Follow.objects
            .filter(follower=user, is_deleted=False)
            .select_related('following', 'following__profile')
        )
        return render(request, self.template_name, {
            'profile_user': user,
            'following': following,
        })
