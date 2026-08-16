from django import forms
from .models import Book, VinylRecord,Porcelain,BoardGame,VideoGame


class VinylRecordForm(forms.ModelForm):
    class Meta:
        model = VinylRecord
        # Używamy dokładnie tych samych pól, które zdefiniowaliśmy w nowym modelu
        fields = [
            'artist', 'title', 'label', 'genre', 'release_year', 
            'disc_count', 'condition', 'price', 'front_cover', 'back_cover'
        ]
        # Dodajemy klasy Bootstrapa dla ładnego wyglądu w przeglądarce
        widgets = {
            'artist': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Pink Floyd'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. The Dark Side of the Moon'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'genre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Rock'}),
            'release_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'disc_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. NM / VG+'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'front_cover': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'back_cover': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class BookForm(forms.ModelForm):
    """Formularz dynamicznie generujący wszystkie pola modelu Book (poza datą dodania)."""
    
    class Meta:
        model = Book
        exclude = ['date_added']
        
        # Opcjonalnie możesz dodać widgety dla wybranych pól, jeśli zajdzie taka potrzeba, 
        # jednak Django automatycznie parsuje pola modelu do pól formularza.


class CSVImportForm(forms.Form):
    """Formularz obsługujący przesyłanie pliku CSV do masowego importu książek."""
    
    csv_file = forms.FileField(
        label='Wybierz plik CSV',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )


class PorcelainForm(forms.ModelForm):
    signature = forms.CharField(
        required=False,
        label="Sygnatura (Marka)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'signature_datalist',
            'placeholder': 'Wybierz z listy lub wpisz nową sygnaturę...',
            'autocomplete': 'off'
        })
    )

    class Meta:
        model = Porcelain
        fields = [
            'name', 
            'style',
            'signature', 
            'year_of_origin', 
            'condition', 
            'price', 
            'signature_image', 
            'image_1', 
            'image_2', 
            'image_3'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Np. Dzbanek do kawy'}),
            'style': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wpisz styl lub wzór (np. China Blau)'}),
            'year_of_origin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Np. 1920-1930 lub 1945'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cena zakupu lub szacowana wartość'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Zbieramy wszystkie domyślne sygnatury oraz te już zapisane w bazie
        db_sigs = list(
            Porcelain.objects.exclude(signature__isnull=True)
            .exclude(signature__exact='')
            .values_list('signature', flat=True)
            .distinct()
        )
        default_sigs = [val for val, label in Porcelain.SIGNATURE_CHOICES if val.strip()]
        # Łączymy unikalne w kolejności alfabetycznej
        self.available_signatures = sorted(list(set(default_sigs + db_sigs)), key=lambda s: s.lower())

class BoardGameForm(forms.ModelForm):
    class Meta:
        model = BoardGame
        fields = [
            'title', 'publisher', 'category', 'release_year', 
            'min_players', 'max_players', 'playtime', 
            'condition', 'price', 'box_image', 'board_image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. The Witcher: Old World'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Rebel'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Przygodowa / Strategiczna'}),
            'release_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_players': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'max_players': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'playtime': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. 90-150 min'}),
            'condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Idealny, wszystkie żetony'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'box_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'board_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class VideoGameForm(forms.ModelForm):
    class Meta:
        model = VideoGame
        fields = [
            'title', 'platform', 'genre', 'release_year', 
            'condition', 'price', 'cover_image', 'media_image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Cyberpunk 2077'}),
            'platform': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. PC, PS5, Xbox Series X'}),
            'genre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Action RPG'}),
            'release_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Idealny / Folia'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'media_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }