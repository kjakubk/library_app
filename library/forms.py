from django import forms
from .models import Book, VinylRecord, Porcelain, BoardGame, VideoGame, ConsoleHardware, Antique


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
    signature_select = forms.ChoiceField(
        required=False,
        label="Sygnatura (Wybierz z listy lub dodaj nową)",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'signatureSelectField'})
    )
    custom_signature = forms.CharField(
        required=False,
        label="Wpisz nową nazwę sygnatury",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'customSignatureField',
            'placeholder': 'Wpisz nową nazwę sygnatury (np. KPM Krister Waldenburg)...'
        })
    )

    class Meta:
        model = Porcelain
        fields = [
            'name', 
            'style',
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
        
        # 1. Zbieramy wszystkie sygnatury z bazy oraz domyślne
        db_sigs = list(
            Porcelain.objects.exclude(signature__isnull=True)
            .exclude(signature__exact='')
            .values_list('signature', flat=True)
            .distinct()
        )
        default_sigs = [val for val, label in Porcelain.SIGNATURE_CHOICES if val.strip()]
        all_sigs = sorted(list(set(default_sigs + db_sigs)), key=lambda s: s.lower())

        choices = [
            ('', '--- Wybierz sygnaturę z listy ---'),
            ('__CUSTOM__', '➕ ✍️ [WPISZ NOWĄ / INNĄ SYGNATURĘ...]')
        ]
        for sig in all_sigs:
            choices.append((sig, sig))
        choices.append(('__CUSTOM__', '➕ ✍️ [WPISZ NOWĄ / INNĄ SYGNATURĘ...]'))
        self.fields['signature_select'].choices = choices

        # 2. Ustawiamy wartości początkowe przy edycji
        if self.instance and self.instance.pk and self.instance.signature:
            curr_sig = self.instance.signature.strip()
            if curr_sig in all_sigs:
                self.initial['signature_select'] = curr_sig
            else:
                self.initial['signature_select'] = '__CUSTOM__'
                self.initial['custom_signature'] = curr_sig

    def clean(self):
        cleaned_data = super().clean()
        sig_choice = cleaned_data.get('signature_select', '').strip()
        custom_sig = cleaned_data.get('custom_signature', '').strip()

        if sig_choice == '__CUSTOM__':
            if not custom_sig:
                self.add_error('custom_signature', 'Wpisz nazwę nowej sygnatury lub wybierz sygnaturę z listy.')
            final_signature = custom_sig
        elif sig_choice:
            final_signature = sig_choice
        elif custom_sig:
            final_signature = custom_sig
        else:
            final_signature = ''

        cleaned_data['signature'] = final_signature
        self.instance.signature = final_signature
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.signature = self.cleaned_data.get('signature', '')
        if commit:
            instance.save()
        return instance

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


class ConsoleHardwareForm(forms.ModelForm):
    class Meta:
        model = ConsoleHardware
        fields = [
            'name', 'manufacturer', 'category', 'release_year', 
            'condition', 'price', 'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. PlayStation 5 / DualSense'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Sony, Nintendo'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Konsola, Pad'}),
            'release_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Idealny / Używany'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class AntiqueForm(forms.ModelForm):
    class Meta:
        model = Antique
        fields = [
            'name', 'material', 'style', 'year_of_origin', 
            'condition', 'price', 'image'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Lampa naftowa, Mosiężny świecznik'}),
            'material': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Mosiądz, Miedź, Szkło'}),
            'style': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Art Deco, Secesja'}),
            'year_of_origin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. 1920-1930'}),
            'condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. Dobry, do renowacji'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }