from django import forms
from .models import Book, VinylRecord,Porcelain


class VinylRecordForm(forms.ModelForm):
    """Formularz do dodawania i edycji płyt winylowych wraz ze stylizacją Bootstrap."""
    
    class Meta:
        model = VinylRecord
        fields = ['artist', 'album_title', 'release_year', 'float', 'image']
        
        labels = {
            'artist': 'Wykonawca',
            'album_title': 'Tytuł albumu',
            'release_year': 'Rok wydania',
            'float': 'Stan',
            'image': 'Zdjęcie okładki (opcjonalne)'
        }
        
        widgets = {
            'artist': forms.TextInput(attrs={'class': 'form-control'}),
            'album_title': forms.TextInput(attrs={'class': 'form-control'}),
            'release_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'float': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
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
            'name': forms.TextInput(attrs={'placeholder': 'Np. Dzbanek do kawy'}),
            'style': forms.TextInput(attrs={'placeholder': 'Wpisz styl lub wzór'}),
            'year_of_origin': forms.TextInput(attrs={'placeholder': 'Np. 1920-1930'}),
            'price': forms.TextInput(attrs={'placeholder': 'Cena zakupu lub szacowana wartość'}),
        }