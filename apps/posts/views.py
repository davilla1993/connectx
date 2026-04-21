from datetime import datetime

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import View

from accounts.views import SocialLoginRequired
from social.recommendations import get_suggestions
from stories.models import Story

from .forms import CommentForm, PostForm
from .models import Comment, Like, Post, Reaction, SavedPost, Tag
from .parser import apply_to_post
from .ranking import ranked_feed

FEED_PAGE_SIZE = 20


class FeedView(SocialLoginRequired, View):
    """Fil d'actualité classé par pertinence (EdgeRank simplifié)."""
    template_name = 'posts/feed.html'

    def get(self, request):
        following_ids = list(
            request.user.following_relations
            .filter(is_deleted=False)
            .values_list('following_id', flat=True)
        )

        before_param = request.GET.get('before')
        before = None
        if before_param:
            try:
                before = datetime.fromisoformat(before_param)
            except ValueError:
                before = None

        posts = ranked_feed(
            request.user, following_ids,
            limit=FEED_PAGE_SIZE, before=before,
        )

        next_cursor = posts[-1].created_at.isoformat() if len(posts) == FEED_PAGE_SIZE else None

        # Requête partielle (infinite scroll) → fragment uniquement
        if request.headers.get('HX-Request') or request.GET.get('partial') == '1':
            return render(request, 'posts/_feed_items.html', {
                'posts': posts,
                'next_cursor': next_cursor,
            })

        suggestions = get_suggestions(request.user, limit=5)

        stories = (
            Story.objects
            .filter(
                is_deleted=False,
                expires_at__gt=timezone.now(),
                author_id__in=following_ids + [request.user.id],
            )
            .select_related('author', 'author__profile')
            .order_by('-created_at')
        )
        my_story = stories.filter(author=request.user).first()

        return render(request, self.template_name, {
            'posts': posts,
            'form': PostForm(),
            'suggestions': suggestions,
            'stories': stories,
            'my_story': my_story,
            'next_cursor': next_cursor,
        })


MAX_IMAGES     = 5
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5 Mo
ALLOWED_TYPES  = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


class PostCreateView(SocialLoginRequired, View):
    def post(self, request):
        form = PostForm(request.POST)
        images = request.FILES.getlist('images')

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
            apply_to_post(post)
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
        post.deleted_at = timezone.now()
        post.save()
        messages.success(request, 'Publication supprimée.')
        return redirect('posts:feed')


class LikeToggleView(SocialLoginRequired, View):
    """Like / Unlike. Répond en JSON pour AJAX."""
    def post(self, request, public_id):
        post = get_object_or_404(Post, public_id=public_id, is_deleted=False)
        like = post.likes.filter(user=request.user).first()

        if like:
            if like.is_deleted:
                like.is_deleted = False
                like.deleted_at = None
                like.deleted_by = None
                like.save()
                liked = True
            else:
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


class SavePostToggleView(SocialLoginRequired, View):
    def post(self, request, public_id):
        post = get_object_or_404(Post, public_id=public_id, is_deleted=False)
        obj, created = SavedPost.objects.get_or_create(
            user=request.user, post=post,
            defaults={'created_by': request.user},
        )
        if not created:
            if obj.is_deleted:
                obj.is_deleted = False
                obj.deleted_at = None
                obj.save()
                saved = True
            else:
                obj.is_deleted = True
                obj.deleted_at = timezone.now()
                obj.save()
                saved = False
        else:
            saved = True
        return JsonResponse({'saved': saved})


class SavedListView(SocialLoginRequired, View):
    template_name = 'posts/saved_list.html'

    def get(self, request):
        saves = (
            SavedPost.objects
            .filter(user=request.user, is_deleted=False)
            .select_related('post__author__profile')
            .prefetch_related('post__images')
            .order_by('-created_at')
        )
        posts = [s.post for s in saves if not s.post.is_deleted]
        return render(request, self.template_name, {'posts': posts})


class ReactionToggleView(SocialLoginRequired, View):
    """Crée/met à jour/supprime la réaction du user sur un post."""
    def post(self, request, public_id):
        post = get_object_or_404(Post, public_id=public_id, is_deleted=False)
        rtype = request.POST.get('type', Reaction.LIKE)
        valid = {t for t, _ in Reaction.TYPES}
        if rtype not in valid:
            return JsonResponse({'error': 'type invalide'}, status=400)

        existing = Reaction.objects.filter(user=request.user, post=post).first()
        if existing and existing.type == rtype and not existing.is_deleted:
            existing.is_deleted = True
            existing.deleted_at = timezone.now()
            existing.save()
            current = None
        elif existing:
            existing.type = rtype
            existing.is_deleted = False
            existing.deleted_at = None
            existing.save()
            current = rtype
        else:
            Reaction.objects.create(
                user=request.user, post=post, type=rtype,
                created_by=request.user,
            )
            current = rtype

        counts = {}
        for t, _ in Reaction.TYPES:
            counts[t] = Reaction.objects.filter(post=post, type=t, is_deleted=False).count()
        return JsonResponse({'current': current, 'counts': counts})


class TagDetailView(SocialLoginRequired, View):
    template_name = 'posts/tag_detail.html'

    def get(self, request, name):
        from django.db.models import Count, Exists, OuterRef, Q
        name = name.lower()
        tag = get_object_or_404(Tag, name=name, is_deleted=False)
        liked_sub = Like.objects.filter(
            post=OuterRef('pk'), user=request.user, is_deleted=False
        )
        posts = (
            Post.objects
            .filter(is_deleted=False, post_tags__tag=tag)
            .select_related('author', 'author__profile')
            .prefetch_related('images')
            .annotate(
                user_liked=Exists(liked_sub),
                likes_total=Count('likes', filter=Q(likes__is_deleted=False), distinct=True),
                comments_total=Count('comments', filter=Q(comments__is_deleted=False), distinct=True),
            )
            .order_by('-created_at')[:50]
        )
        return render(request, self.template_name, {'tag': tag, 'posts': posts})
