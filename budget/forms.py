from django import forms
from .models import Transaction, Account, Category, MonthlyBudget, RecurringPayment
from decimal import Decimal


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'transaction_type',
            'title',
            'amount',
            'date',
            'account',
            'destination_account',
            'category',
            'notes',
            'receipt_image',
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none', 'id': 'id_transaction_type'}),
            'title': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'np. Zakupy Biedronka, Czynsz, Wynagrodzenie...'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': '0.00', 'step': '0.01', 'min': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'form-control rounded-3 shadow-none', 'type': 'date'}),
            'account': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'destination_account': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'category': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'notes': forms.Textarea(attrs={'class': 'form-control rounded-3 shadow-none', 'rows': 2, 'placeholder': 'Opcjonalne uwagi lub numer paragonu...'}),
            'receipt_image': forms.FileInput(attrs={'class': 'form-control rounded-3 shadow-none', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrujemy tylko aktywne konta
        self.fields['account'].queryset = Account.objects.filter(is_active=True)
        self.fields['destination_account'].queryset = Account.objects.filter(is_active=True)
        self.fields['destination_account'].required = False
        self.fields['category'].required = False

    def clean(self):
        cleaned_data = super().clean()
        t_type = cleaned_data.get('transaction_type')
        acc = cleaned_data.get('account')
        dest_acc = cleaned_data.get('destination_account')
        cat = cleaned_data.get('category')

        if t_type == 'transfer':
            if not dest_acc:
                self.add_error('destination_account', 'Wybierz konto docelowe dla przelewu.')
            elif acc and dest_acc and acc == dest_acc:
                self.add_error('destination_account', 'Konto docelowe musi być inne niż konto źródłowe.')
        elif t_type in ('expense', 'income'):
            if not cat:
                # Ostrzeżenie / domyślne przypisanie nieblokujące
                pass

        return cleaned_data


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = [
            'name',
            'account_type',
            'initial_balance',
            'currency',
            'icon',
            'color',
            'is_active',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'np. mBank eKonto, Portfel, Oszczędności...'}),
            'account_type': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'PLN'}),
            'icon': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'bi-wallet2 lub emoji 💳'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color rounded-3 shadow-none', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control rounded-3 shadow-none', 'rows': 2}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            'name',
            'category_type',
            'icon',
            'color',
            'order',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'np. Paliwo, Prezenty, Inwestycje...'}),
            'category_type': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'icon': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'Emoji np. 🛒, 🚗, 🍕 lub klasa bi-tag'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color rounded-3 shadow-none', 'type': 'color'}),
            'order': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none'}),
        }


class MonthlyBudgetForm(forms.ModelForm):
    class Meta:
        model = MonthlyBudget
        fields = [
            'category',
            'amount_limit',
            'month',
            'year',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'amount_limit': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'step': '1.00', 'placeholder': 'np. 1500.00'}),
            'month': forms.Select(choices=[(i, f"{i:02d}") for i in range(1, 13)], attrs={'class': 'form-select rounded-3 shadow-none'}),
            'year': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(category_type='expense')


class RecurringPaymentForm(forms.ModelForm):
    class Meta:
        model = RecurringPayment
        fields = [
            'title',
            'amount',
            'category',
            'account',
            'frequency',
            'due_day',
            'is_active',
            'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'np. Czynsz, Internet, Spotify, Netflix...'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'account': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'frequency': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'due_day': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'min': 1, 'max': 31}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control rounded-3 shadow-none', 'rows': 2, 'placeholder': 'Opcjonalne szczegóły...'}),
        }
