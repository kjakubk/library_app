from django.db import models
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('checking', 'Konto osobiste (ROR)'),
        ('savings', 'Konto oszczędnościowe'),
        ('cash', 'Gotówka / Portfel'),
        ('card', 'Karta kredytowa'),
        ('investment', 'Inwestycje / Lokata'),
        ('other', 'Inne'),
    ]

    OWNER_CHOICES = [
        ('personal', '👤 Moje prywatne (Jakub)'),
        ('business', '💼 Moje firmowe (B2B / Działalność)'),
        ('partner', '👩‍🦰 Konto partnerki'),
        ('joint', '👥 Wspólne domowe'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nazwa konta / portfela")
    owner = models.CharField(max_length=20, choices=OWNER_CHOICES, default='personal', verbose_name="Właściciel / Profil")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='checking', verbose_name="Typ konta")
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Saldo początkowe (PLN)")
    currency = models.CharField(max_length=10, default='PLN', verbose_name="Waluta")
    icon = models.CharField(max_length=50, default='bi-wallet2', verbose_name="Ikona Bootstrap / Emoji")
    color = models.CharField(max_length=30, default='#0284c7', verbose_name="Kolor akcentu")
    is_active = models.BooleanField(default=True, verbose_name="Konto aktywne")
    notes = models.TextField(blank=True, null=True, verbose_name="Notatki")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")

    class Meta:
        verbose_name = "Konto / Portfel"
        verbose_name_plural = "Konta i Portfele"
        ordering = ['owner', '-is_active', 'name']

    def __str__(self):
        return f"{self.name} ({self.current_balance:,.2f} {self.currency})"

    @property
    def current_balance(self):
        """Oblicza aktualne saldo konta: saldo początkowe + przychody - wydatki + przelewy wchodzące - przelewy wychodzące."""
        expenses = Transaction.objects.filter(account=self, transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        incomes = Transaction.objects.filter(account=self, transaction_type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        transfers_out = Transaction.objects.filter(account=self, transaction_type='transfer').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        transfers_in = Transaction.objects.filter(destination_account=self, transaction_type='transfer').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return self.initial_balance + incomes - expenses - transfers_out + transfers_in


class Category(models.Model):
    CATEGORY_TYPES = [
        ('expense', 'Wydatek'),
        ('income', 'Przychód'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nazwa kategorii")
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default='expense', verbose_name="Typ kategorii")
    icon = models.CharField(max_length=50, default='bi-tag', verbose_name="Ikona (Bootstrap lub Emoji)")
    color = models.CharField(max_length=30, default='#3b82f6', verbose_name="Kolor kafelka")
    default_budget_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Domyślny stały limit miesięczny (PLN)")
    is_default = models.BooleanField(default=False, verbose_name="Kategoria systemowa")
    order = models.IntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        ordering = ['order', 'name']

    def __str__(self):
        icon = self.icon if self.icon else ("🔴" if self.category_type == 'expense' else "🟢")
        return f"{icon} {self.name}"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('expense', 'Wydatek'),
        ('income', 'Przychód'),
        ('transfer', 'Przelew między kontami'),
    ]

    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name="Konto źródłowe"
    )
    destination_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_transfers',
        verbose_name="Konto docelowe (tylko dla przelewów)"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="Kategoria"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
        default='expense',
        verbose_name="Typ transakcji"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Kwota (PLN)"
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name="Data transakcji"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Tytuł / Opis transakcji"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notatki / Szczegóły"
    )
    receipt_image = models.ImageField(
        upload_to='budget/receipts/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Zdjęcie paragonu / Faktura"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data dodania"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Ostatnia zmiana"
    )

    class Meta:
        verbose_name = "Transakcja"
        verbose_name_plural = "Transakcje"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['transaction_type', '-date']),
            models.Index(fields=['account', '-date']),
            models.Index(fields=['category', '-date']),
        ]

    def __str__(self):
        sign = "+" if self.transaction_type == 'income' else ("-" if self.transaction_type == 'expense' else "⇄")
        return f"{self.date.strftime('%d.%m.%Y')} | {self.title}: {sign}{self.amount:,.2f} PLN"


class MonthlyBudget(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='monthly_budgets',
        verbose_name="Kategoria wydatków"
    )
    year = models.IntegerField(verbose_name="Rok")
    month = models.IntegerField(verbose_name="Miesiąc (1-12)")
    amount_limit = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Limit budżetowy (PLN)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Limit budżetowy"
        verbose_name_plural = "Limity budżetowe"
        unique_together = ('category', 'year', 'month')
        ordering = ['-year', '-month', 'category__name']

    def __str__(self):
        return f"{self.category.name} ({self.month:02d}/{self.year}) — Limit: {self.amount_limit:,.2f} PLN"

    def get_spent(self):
        """Zwraca sumę wydatków dla tej kategorii w danym miesiącu."""
        spent = Transaction.objects.filter(
            category=self.category,
            transaction_type='expense',
            date__year=self.year,
            date__month=self.month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return spent

    @property
    def spent_amount(self):
        return self.get_spent()

    @property
    def percentage_used(self):
        spent = self.get_spent()
        if self.amount_limit > 0:
            pct = (spent / self.amount_limit) * 100
            return min(float(pct), 100.0)
        return 0.0

    @property
    def remaining_amount(self):
        return self.amount_limit - self.get_spent()

    @property
    def is_exceeded(self):
        return self.get_spent() > self.amount_limit


class RecurringPayment(models.Model):
    FREQUENCY_CHOICES = [
        ('monthly', 'Miesięcznie'),
        ('quarterly', 'Kwartalnie'),
        ('yearly', 'Rocznie'),
    ]

    title = models.CharField(max_length=150, verbose_name="Nazwa opłaty / Zobowiązanie / Rata")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Kwota raty / opłaty (PLN)")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategoria")
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Domyślne konto płatności")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly', verbose_name="Częstotliwość")
    due_day = models.IntegerField(default=1, verbose_name="Dzień płatności (1-31)")
    start_date = models.DateField(default=timezone.now, verbose_name="Data rozpoczęcia")
    end_date = models.DateField(null=True, blank=True, verbose_name="Data zakończenia / ostatniej raty (opcjonalnie)")
    total_installments = models.IntegerField(null=True, blank=True, verbose_name="Całkowita liczba rat (opcjonalnie)")
    is_active = models.BooleanField(default=True, verbose_name="Aktywna płatność")
    last_paid_date = models.DateField(null=True, blank=True, verbose_name="Data ostatniej opłaty")
    notes = models.TextField(blank=True, null=True, verbose_name="Notatki / Numer umowy / Kredyt")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Płatność cykliczna / Zobowiązanie"
        verbose_name_plural = "Płatności cykliczne i Zobowiązania"
        ordering = ['due_day', 'title']

    def __str__(self):
        return f"{self.title} ({self.amount:,.2f} PLN / {self.get_frequency_display()})"

    def is_paid_in_month(self, year, month):
        """Sprawdza czy płatność została oznaczona jako opłacona w danym miesiącu."""
        if not self.last_paid_date:
            return False
        return self.last_paid_date.year == year and self.last_paid_date.month == month

    def get_remaining_installments(self, current_year=None, current_month=None):
        """Zwraca liczbę rat/miesięcy pozostałych do końca spłaty."""
        today = timezone.now().date()
        c_year = current_year or today.year
        c_month = current_month or today.month

        if self.end_date:
            months = (self.end_date.year - c_year) * 12 + (self.end_date.month - c_month) + 1
            return max(0, months)
        elif self.total_installments and self.start_date:
            elapsed = (c_year - self.start_date.year) * 12 + (c_month - self.start_date.month)
            remaining = self.total_installments - max(0, elapsed)
            return max(0, remaining)
        return None

    def get_remaining_amount(self, current_year=None, current_month=None):
        """Zwraca łączną kwotę pozostałą do całkowitej spłaty."""
        rem = self.get_remaining_installments(current_year, current_month)
        if rem is not None:
            return Decimal(rem) * self.amount
        return None

    def get_progress_percentage(self, current_year=None, current_month=None):
        """Zwraca procent spłaconych rat."""
        today = timezone.now().date()
        c_year = current_year or today.year
        c_month = current_month or today.month

        if self.total_installments and self.total_installments > 0:
            rem = self.get_remaining_installments(c_year, c_month)
            if rem is not None:
                paid = self.total_installments - rem
                return min(100.0, max(0.0, (paid / self.total_installments) * 100))
        elif self.end_date and self.start_date:
            total_months = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month) + 1
            rem = self.get_remaining_installments(c_year, c_month)
            if total_months > 0 and rem is not None:
                paid = total_months - rem
                return min(100.0, max(0.0, (paid / total_months) * 100))
        return None
