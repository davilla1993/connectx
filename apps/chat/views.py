from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.views import SocialLoginRequired
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from .models import Conversation

User = get_user_model()


class ConversationListView(SocialLoginRequired, View):
    template_name = 'chat/conversation_list.html'

    def get(self, request):
        conversations = (
            request.user.conversations
            .filter(is_deleted=False)
            .prefetch_related('participants__profile')
            .order_by('-updated_at')
        )
        return render(request, self.template_name, {'conversations': conversations})


class ConversationDetailView(SocialLoginRequired, View):
    template_name = 'chat/conversation_detail.html'

    def get(self, request, public_id):
        conversation = get_object_or_404(
            Conversation,
            public_id=public_id,
            participants=request.user,
            is_deleted=False,
        )
        messages_qs = (
            conversation.messages
            .filter(is_deleted=False)
            .select_related('sender')
        )
        # Marquer les messages non lus comme lus
        messages_qs.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

        return render(request, self.template_name, {
            'conversation': conversation,
            'messages': messages_qs,
            'other_user': conversation.get_other_participant(request.user),
        })


class StartConversationView(SocialLoginRequired, View):
    """
    Démarre ou retrouve une conversation privée avec un utilisateur.
    Redirige vers la conversation existante si elle existe déjà.
    """
    def get(self, request, username):
        other_user = get_object_or_404(User, username=username)

        if other_user == request.user:
            return redirect('chat:list')

        # Cherche une conversation existante entre les deux utilisateurs
        conversation = (
            Conversation.objects
            .filter(participants=request.user, is_deleted=False)
            .filter(participants=other_user)
            .first()
        )

        if not conversation:
            conversation = Conversation.objects.create(created_by=request.user)
            conversation.participants.add(request.user, other_user)

        return redirect('chat:detail', public_id=conversation.public_id)
