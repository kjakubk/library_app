from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Photo, Album

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['album', 'image', 'title']
        widgets = {
            'album': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Poranek nad rzeką Słupią...'}),
        }


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Finlandia 2026, Geocaching...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Krótki opis (opcjonalnie)'}),
        }


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Nazwa użytkownika lub e-mail'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg',
        'placeholder': 'Hasło'
    }))


class UserAdminCreateForm(forms.ModelForm):
    """Formularz dodawania nowego użytkownika z poziomu panelu po zalogowaniu."""
    password = forms.CharField(
        label="Hasło",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Wpisz hasło dla użytkownika'})
    )
    password_confirm = forms.CharField(
        label="Powtórz hasło",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Powtórz hasło'})
    )
    is_administrator = forms.BooleanField(
        label="Nadaj uprawnienia administratora (Superuser / Staff)",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. anna, marek'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'opcjonalnie (np. anna@przyklad.pl)'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Użytkownik o takim loginie już istnieje w bazie!")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Hasła nie są identyczne!")

        return cleaned_data


class UserAdminPasswordChangeForm(forms.Form):
    """Formularz zmiany hasła użytkownika z poziomu panelu."""
    new_password = forms.CharField(
        label="Nowe hasło",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Wpisz nowe hasło'})
    )
    new_password_confirm = forms.CharField(
        label="Powtórz nowe hasło",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Powtórz nowe hasło'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('new_password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password_confirm', "Podane hasła nie są identyczne!")
        return cleaned_data