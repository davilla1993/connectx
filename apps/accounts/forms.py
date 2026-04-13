from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Supprime les textes d'aide verbeux — la validation est gérée en JS
        for field in self.fields.values():
            field.help_text = None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('bio', 'avatar', 'location', 'website')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
