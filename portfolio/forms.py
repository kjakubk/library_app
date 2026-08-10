from django import forms
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