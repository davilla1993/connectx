from django import forms
from .models import Story


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={
                'placeholder': 'Ajouter une légende…',
                'class': 'form-control',
            }),
            'image': forms.ClearableFileInput(attrs={
                'accept': 'image/jpeg,image/png,image/gif,image/webp',
                'class': 'form-control',
            }),
        }
        labels = {
            'image': 'Photo',
            'caption': 'Légende (optionnelle)',
        }
