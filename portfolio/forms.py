from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import Photo, Album


class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = [
            'album', 'image', 'title', 'description',
            'location', 'taken_at', 'tags', 'is_featured', 'sort_order',
        ]
        widgets = {
            'album': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'np. Poranek nad rzeką Słupią...',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rounded-3',
                'rows': 3,
                'placeholder': 'Krótka historia tego zdjęcia (opcjonalnie)...',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'np. Tatry, Morskie Oko',
            }),
            'taken_at': forms.DateInput(attrs={
                'class': 'form-control rounded-3',
                'type': 'date',
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'np. krajobraz, góry, złota godzina',
            }),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 0}),
        }


class PhotoEditForm(forms.ModelForm):
    """Formularz edycji istniejącego zdjęcia (bez pola image)."""
    class Meta:
        model = Photo
        fields = [
            'album', 'title', 'description',
            'location', 'taken_at', 'tags', 'is_featured', 'sort_order',
            'camera', 'lens', 'focal_length', 'aperture', 'shutter_speed', 'iso',
        ]
        widgets = {
            'album': forms.Select(attrs={'class': 'form-select rounded-3'}),
            'title': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'Tytuł zdjęcia'}),
            'description': forms.Textarea(attrs={'class': 'form-control rounded-3', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'np. Tatry, Morskie Oko'}),
            'taken_at': forms.DateInput(attrs={'class': 'form-control rounded-3', 'type': 'date'}),
            'tags': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'krajobraz, góry, złota godzina'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control rounded-3', 'min': 0}),
            'camera': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'np. Canon EOS R5'}),
            'lens': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'np. EF 50mm f/1.8'}),
            'focal_length': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'np. 50mm'}),
            'aperture': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'np. f/2.8'}),
            'shutter_speed': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'np. 1/500s'}),
            'iso': forms.TextInput(attrs={'class': 'form-control rounded-3', 'placeholder': 'np. 400'}),
        }


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control rounded-3',
                'placeholder': 'np. Finlandia 2026, Geocaching...',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control rounded-3',
                'rows': 3,
                'placeholder': 'Krótki opis (opcjonalnie)',
            }),
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