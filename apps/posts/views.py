from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.views import SocialLoginRequired
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from .forms import CommentForm, PostForm
from .models import Comment, Like, Post


class FeedView(SocialLoginRequired, View):
    """
    Fil d'actualité : posts des utilisateurs suivis + posts de l'utilisateur connecté.
    """
    template_name = 'posts/feed.html'

    def get(self, request):
        from django.contrib.auth import get_user_model
        from django.db.models import Exists, OuterRef
        User = get_user_model()

        following_ids = list(
            request.user.following_relations
            .filter(is_deleted=False)
            .values_list('following_id', flat=True)
        )

        # Annote chaque post avec user_liked (booléen, calculé en SQL)
        liked_subquery = Like.objects.filter(
            post=OuterRef('pk'), user=request.user, is_deleted=False
        )
        posts = (
            Post.objects
            .filter(is_deleted=False, author_id__in=following_ids + [request.user.id])
            .select_related('author', 'author__profile')
            .prefetch_related('images', 'likes', 'comments')
            .annotate(user_liked=Exists(liked_subquery))
            .order_by('-created_at')
        )

        suggestions = (
            User.objects
            .exclude(pk=request.user.pk)
            .exclude(pk__in=following_ids)
            .select_related('profile')[:5]
        )

        form = PostForm()
        return render(request, self.template_name, {
            'posts': posts,
            'form': form,
            'suggestions': suggestions,
        })


MAX_IMAGES     = 5
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5 Mo
ALLOWED_TYPES  = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


class PostCreateView(SocialLoginRequired, View):
    def post(self, request):
        form = PostForm(request.POST)
        images = request.FILES.getlist('images')

        # Validation images
        errors = []
        if len(images) > MAX_IMAGES:
            errors.append(f'Maximum {MAX_IMAGES} images par publication.')
        for img in images:
            if img.size > MAX_IMAGE_SIZE:
                errors.append(f'"{img.name}" dépasse 5 Mo.')
            if img.content_type not in ALLOWED_TYPES:
                errors.append(f'"{img.name}" : format non supporté (jpg, png, gif, webp).')

        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('posts:feed')

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.created_by = request.user
            post.save()
            for image in images:
                post.images.create(image=image, created_by=request.user)
            messages.success(request, 'Publication créée.')
        return redirect('posts:feed')


class PostDetailView(SocialLoginRequired, View):
    template_name = 'posts/post_detail.html'

    def get(self, request, public_id):
        post = get_object_or_404(Post, public_id=public_id, is_deleted=False)
        comments = post.comments.filter(is_deleted=False).select_related('author')
        form = CommentForm()
        liked = post.likes.filter(user=request.user, is_deleted=False).exists()
        return render(request, self.template_name, {
            'post': post,
            'comments': comments,
            'form': form,
            'liked': liked,
        })

    def post(self, request, public_id):
        post = get_object_or_404(Post, public_id=public_id, is_deleted=False)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.created_by = request.user
            comment.save()
        return redirect('posts:detail', public_id=public_id)


class PostDeleteView(SocialLoginRequired, View):
    def post(self, request, public_id):
        post = get_object_or_404(Post, public_id=public_id, author=request.user)
        post.is_deleted = True
        post.deleted_by = request.user
        from django.utils import timezone
        post.deleted_at = timezone.now()
        post.save()
        messages.success(request, 'Publication supprimée.')
        return redirect('posts:feed')


class LikeToggleView(SocialLoginRequired, View):
    """
    Like / Unlike. Répond en JSON pour pouvoir être appelé en AJAX.
    """
    def post(self, request, public_id):
        post = get_object_or_404(Post, public_id=public_id, is_deleted=False)
        like = post.likes.filter(user=request.user).first()

        if like:
            if like.is_deleted:
                # Re-like
                like.is_deleted = False
                like.deleted_at = None
                like.deleted_by = None
                like.save()
                liked = True
            else:
                # Unlike (soft delete)
                from django.utils import timezone
                like.is_deleted = True
                like.deleted_at = timezone.now()
                like.deleted_by = request.user
                like.save()
                liked = False
        else:
            Like.objects.create(user=request.user, post=post, created_by=request.user)
            liked = True

        return JsonResponse({
            'liked': liked,
            'count': post.likes.filter(is_deleted=False).count(),
        })
