from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import View
from django.contrib.auth.tokens import default_token_generator

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
            user.is_active = False  # Désactive le compte jusqu'à vérification
            user.save()

            # Envoi de l'email de vérification
            try:
                current_site = get_current_site(request)
                mail_subject = 'Activez votre compte ConnectX'
                message = render_to_string('accounts/acc_active_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                email = EmailMessage(mail_subject, message, to=[user.email])
                email.send(fail_silently=True)
                messages.info(request, 'Un email de confirmation a été envoyé. Veuillez vérifier votre boîte de réception pour activer votre compte.')
            except Exception as e:
                messages.error(request, "Erreur lors de l'envoi de l'email.")

            return redirect('accounts:login')
        return render(request, self.template_name, {'form': form})


class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True  # Réactive le compte
            user.is_email_verified = True
            user.save()
            messages.success(request, 'Votre email a été vérifié ! Vous pouvez maintenant vous connecter.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Le lien de confirmation est invalide ou a expiré.')
            return redirect('accounts:login')


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
            .filter(is_staff=False, is_superuser=False)
            .select_related('profile')
        )
        return render(request, self.template_name, {'suggestions': suggestions})
