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
            'owner',
            'account_type',
            'initial_balance',
            'currency',
            'icon',
            'color',
            'is_active',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'np. mBank eKonto, ING Firmowe, Santander...'}),
            'owner': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'account_type': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'PLN'}),
            'icon': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'bi-wallet2 lub emoji 💳'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color rounded-3 shadow-none', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control rounded-3 shadow-none', 'rows': 2}),
        }


class CategoryForm(forms.ModelForm):
    default_budget_limit = forms.DecimalField(
        required=False,
        initial=Decimal('0.00'),
        label="Domyślny stały limit miesięczny (PLN)",
        widget=forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'step': '1.00', 'placeholder': 'np. 500.00 (opcjonalnie)'})
    )
    order = forms.IntegerField(
        required=False,
        initial=0,
        label="Kolejność",
        widget=forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': '0'})
    )
    icon = forms.CharField(
        required=False,
        initial='🏷️',
        label="Ikona / Emoji",
        widget=forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'Emoji np. 🛒, 🚗, 🍕 lub bi-tag'})
    )
    color = forms.CharField(
        required=False,
        initial='#3b82f6',
        label="Kolor kafelka",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-color rounded-3 shadow-none', 'type': 'color'})
    )

    class Meta:
        model = Category
        fields = [
            'name',
            'category_type',
            'icon',
            'color',
            'default_budget_limit',
            'order',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'np. Paliwo, Prezenty, Inwestycje...'}),
            'category_type': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
        }

    def clean_default_budget_limit(self):
        val = self.cleaned_data.get('default_budget_limit')
        return val if val is not None else Decimal('0.00')

    def clean_order(self):
        val = self.cleaned_data.get('order')
        return val if val is not None else 0

    def clean_icon(self):
        val = self.cleaned_data.get('icon')
        return val if val else '🏷️'

    def clean_color(self):
        val = self.cleaned_data.get('color')
        return val if val else '#3b82f6'


class MonthlyBudgetForm(forms.ModelForm):
    apply_to_all_future = forms.BooleanField(
        required=False,
        initial=True,
        label="Ustaw ten limit jako stały i przenieś automatycznie na kolejne miesiące",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

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
    is_paid_this_month = forms.BooleanField(
        required=False,
        label="Oznacz jako opłacone w bieżącym miesiącu",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = RecurringPayment
        fields = [
            'title',
            'amount',
            'category',
            'account',
            'frequency',
            'due_day',
            'start_date',
            'end_date',
            'total_installments',
            'is_active',
            'notes',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control rounded-3 shadow-none', 'placeholder': 'np. Czynsz, Kredyt hipoteczny, Raty za auto, Netflix...'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'account': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'frequency': forms.Select(attrs={'class': 'form-select rounded-3 shadow-none'}),
            'due_day': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'min': 1, 'max': 31}),
            'start_date': forms.DateInput(attrs={'class': 'form-control rounded-3 shadow-none', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control rounded-3 shadow-none', 'type': 'date'}),
            'total_installments': forms.NumberInput(attrs={'class': 'form-control rounded-3 shadow-none', 'min': 1, 'placeholder': 'np. 24 raty (opcjonalnie)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control rounded-3 shadow-none', 'rows': 2, 'placeholder': 'Opcjonalne szczegóły, numer umowy kredytowej...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            today = timezone.now().date()
            self.fields['is_paid_this_month'].initial = self.instance.is_paid_in_month(today.year, today.month)

    def save(self, commit=True):
        instance = super().save(commit=False)
        is_paid = self.cleaned_data.get('is_paid_this_month')
        today = timezone.now().date()
        if is_paid:
            if not instance.is_paid_in_month(today.year, today.month):
                instance.last_paid_date = today
        else:
            if instance.is_paid_in_month(today.year, today.month):
                instance.last_paid_date = None
        if commit:
            instance.save()
        return instance
