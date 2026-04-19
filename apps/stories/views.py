from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import View

from accounts.views import SocialLoginRequired
from .forms import StoryForm
from .models import Story

MAX_STORY_SIZE = 10 * 1024 * 1024   # 10 Mo
ALLOWED_TYPES  = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}


class StoryCreateView(SocialLoginRequired, View):
    template_name = 'stories/story_create.html'

    def get(self, request):
        return render(request, self.template_name, {'form': StoryForm()})

    def post(self, request):
        form = StoryForm(request.POST, request.FILES)
        image = request.FILES.get('image')

        if image:
            if image.size > MAX_STORY_SIZE:
                messages.error(request, 'L\'image dépasse 10 Mo.')
                return render(request, self.template_name, {'form': form})
            if image.content_type not in ALLOWED_TYPES:
                messages.error(request, 'Format non supporté (jpg, png, gif, webp).')
                return render(request, self.template_name, {'form': form})

        if form.is_valid():
            story = form.save(commit=False)
            story.author = request.user
            story.created_by = request.user
            story.save()
            messages.success(request, 'Story publiée ! Elle sera visible pendant 24h.')
            return redirect('posts:feed')

        return render(request, self.template_name, {'form': form})


class StoryDetailView(SocialLoginRequired, View):
    template_name = 'stories/story_detail.html'

    def get(self, request, pk):
        story = get_object_or_404(Story, pk=pk, is_deleted=False)
        if story.is_expired:
            messages.warning(request, 'Cette story a expiré.')
            return redirect('posts:feed')
        return render(request, self.template_name, {'story': story})


class StoryDeleteView(SocialLoginRequired, View):
    def post(self, request, pk):
        story = get_object_or_404(Story, pk=pk, author=request.user)
        story.is_deleted = True
        story.deleted_by = request.user
        story.deleted_at = timezone.now()
        story.save()
        messages.success(request, 'Story supprimée.')
        return redirect('posts:feed')
