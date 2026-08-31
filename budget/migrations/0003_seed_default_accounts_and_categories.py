from django.db import migrations
from decimal import Decimal


def seed_data(apps, schema_editor):
    Account = apps.get_model('budget', 'Account')
    Category = apps.get_model('budget', 'Category')

    # Domyślne konta
    default_accounts = [
        {
            'name': 'Konto Prywatne (Jakub)',
            'owner': 'personal',
            'account_type': 'checking',
            'initial_balance': Decimal('0.00'),
            'currency': 'PLN',
            'icon': 'bi-person-badge',
            'color': '#0284c7',
            'notes': 'Główne konto osobiste / ROR',
            'is_active': True,
        },
        {
            'name': 'Konto Firmowe (B2B / Działalność)',
            'owner': 'business',
            'account_type': 'checking',
            'initial_balance': Decimal('0.00'),
            'currency': 'PLN',
            'icon': 'bi-briefcase',
            'color': '#8b5cf6',
            'notes': 'Rachunek firmowy / B2B',
            'is_active': True,
        },
        {
            'name': 'Konto Partnerki',
            'owner': 'partner',
            'account_type': 'checking',
            'initial_balance': Decimal('0.00'),
            'currency': 'PLN',
            'icon': 'bi-person-heart',
            'color': '#ec4899',
            'notes': 'Rachunek bankowy partnerki',
            'is_active': True,
        },
        {
            'name': 'Konto Oszczędnościowe / Wspólne',
            'owner': 'joint',
            'account_type': 'savings',
            'initial_balance': Decimal('0.00'),
            'currency': 'PLN',
            'icon': 'bi-piggy-bank',
            'color': '#10b981',
            'notes': 'Oszczędności i wspólny fundusz domowy',
            'is_active': True,
        },
        {
            'name': 'Gotówka / Portfel',
            'owner': 'personal',
            'account_type': 'cash',
            'initial_balance': Decimal('0.00'),
            'currency': 'PLN',
            'icon': 'bi-cash-coin',
            'color': '#14b8a6',
            'notes': 'Pieniądze w gotówce',
            'is_active': True,
        },
    ]

    for acc_data in default_accounts:
        if not Account.objects.filter(name=acc_data['name']).exists():
            Account.objects.create(**acc_data)

    # Domyślne kategorie
    default_categories = [
        # Wydatki
        ('Jedzenie & Artykuły spożywcze', 'expense', '🛒', '#f59e0b', 1),
        ('Mieszkanie & Czynsz', 'expense', '🏠', '#ef4444', 2),
        ('Rachunki & Media', 'expense', '⚡', '#3b82f6', 3),
        ('Transport & Paliwo', 'expense', '🚗', '#6366f1', 4),
        ('Zdrowie & Apteka', 'expense', '💊', '#ec4899', 5),
        ('Rozrywka & Wyjścia', 'expense', '🎬', '#8b5cf6', 6),
        ('Kolekcje & Hobby', 'expense', '💎', '#14b8a6', 7),
        ('Ubrania & Zakupy', 'expense', '👕', '#06b6d4', 8),
        ('Edukacja & Kursy', 'expense', '📚', '#10b981', 9),
        ('Inne wydatki', 'expense', '🏷️', '#64748b', 10),
        # Przychody
        ('Wynagrodzenie / Pensja', 'income', '💼', '#10b981', 1),
        ('Faktura B2B / Kontrakt', 'income', '🏢', '#8b5cf6', 2),
        ('Premia / Bonus', 'income', '🎁', '#f59e0b', 3),
        ('Zwrot podatku / Urząd', 'income', '🏛️', '#3b82f6', 4),
        ('Odsetki / Lokaty', 'income', '📈', '#06b6d4', 5),
        ('Inne przychody', 'income', '💰', '#64748b', 6),
    ]

    for name, cat_type, icon, color, order in default_categories:
        if not Category.objects.filter(name=name, category_type=cat_type).exists():
            Category.objects.create(
                name=name,
                category_type=cat_type,
                icon=icon,
                color=color,
                order=order,
                is_default=True
            )


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0002_alter_account_options_account_owner'),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_func),
    ]
