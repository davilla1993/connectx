from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': "Quoi de neuf ?",
            }),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': "Ajouter un commentaire...",
            }),
        }
