from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from .forms import ProfileEditForm, RegisterForm
from .models import User


class SocialLoginRequired(LoginRequiredMixin):
    """
    Mixin pour les vues du réseau social.
    - Redirige vers login si non connecté.
    - Redirige vers /admin/ si le compte est staff (admin).
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('/admin/')
        return super().dispatch(request, *args, **kwargs)


class CustomLoginView(LoginView):
    """
    Après connexion :
    - Staff → /admin/
    - Utilisateur normal → feed
    """
    template_name = 'accounts/login.html'

    def get_success_url(self):
        if self.request.user.is_staff:
            return '/admin/'
        return '/'


class RegisterView(View):
    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/admin/' if request.user.is_staff else '/')
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenue, {user.username} !')
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


class ProfileView(SocialLoginRequired, View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        return render(request, self.template_name, {
            'profile_user': request.user,
            'profile': request.user.profile,
        })


class UserProfileView(SocialLoginRequired, View):
    template_name = 'accounts/user_profile.html'

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        # is_deleted=False : on ne compte pas les unfollows
        is_following = request.user.following_relations.filter(
            following=user, is_deleted=False
        ).exists()
        followers_count = user.follower_relations.filter(is_deleted=False).count()
        following_count = user.following_relations.filter(is_deleted=False).count()
        posts = user.posts.filter(is_deleted=False).order_by('-created_at')
        return render(request, self.template_name, {
            'profile_user': user,
            'profile': user.profile,
            'is_following': is_following,
            'followers_count': followers_count,
            'following_count': following_count,
            'posts': posts,
        })


class ProfileEditView(SocialLoginRequired, View):
    template_name = 'accounts/profile_edit.html'

    def get(self, request):
        form = ProfileEditForm(instance=request.user.profile)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour.')
            return redirect('accounts:profile')
        return render(request, self.template_name, {'form': form})


class SearchView(SocialLoginRequired, View):
    template_name = 'accounts/search.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        users = []
        if query:
            # Exclut l'utilisateur connecté, cherche dans username et email
            users = (
                User.objects
                .filter(Q(username__icontains=query) | Q(email__icontains=query))
                .exclude(pk=request.user.pk)
                .select_related('profile')
            )
            # Annote si l'utilisateur connecté les suit déjà
            following_ids = set(
                request.user.following_relations
                .filter(is_deleted=False)
                .values_list('following_id', flat=True)
            )
            for user in users:
                user.is_following = user.pk in following_ids

        return render(request, self.template_name, {
            'query': query,
            'users': users,
        })


class SuggestionsView(SocialLoginRequired, View):
    """Page dédiée : tous les utilisateurs que je ne suis pas encore."""
    template_name = 'accounts/suggestions.html'

    def get(self, request):
        following_ids = set(
            request.user.following_relations
            .filter(is_deleted=False)
            .values_list('following_id', flat=True)
        )
        suggestions = (
            User.objects
            .exclude(pk=request.user.pk)
            .exclude(pk__in=following_ids)
            .select_related('profile')
        )
        return render(request, self.template_name, {'suggestions': suggestions})
