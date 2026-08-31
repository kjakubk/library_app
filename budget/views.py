import csv
import json
from decimal import Decimal
from datetime import datetime, date, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Account, Category, Transaction, MonthlyBudget, RecurringPayment
from .forms import (
    TransactionForm, AccountForm, CategoryForm,
    MonthlyBudgetForm, RecurringPaymentForm
)


POLISH_MONTHS = [
    (1, 'Styczeń'), (2, 'Luty'), (3, 'Marzec'), (4, 'Kwiecień'),
    (5, 'Maj'), (6, 'Czerwiec'), (7, 'Lipiec'), (8, 'Sierpień'),
    (9, 'Wrzesień'), (10, 'Październik'), (11, 'Listopad'), (12, 'Grudzień')
]


@login_required
def budget_dashboard(request):
    today = timezone.now().date()
    
    # Pobieranie wybranego miesiąca i roku
    try:
        current_year = int(request.GET.get('year', today.year))
        current_month = int(request.GET.get('month', today.month))
        if current_month < 1 or current_month > 12:
            current_month = today.month
    except (ValueError, TypeError):
        current_year = today.year
        current_month = today.month

    selected_date = date(current_year, current_month, 1)

    # Filtr właściciela konta (Profil: all, personal, business, partner, joint)
    selected_owner = request.GET.get('owner', 'all')
    selected_account_id = request.GET.get('account')

    ensure_default_accounts()
    all_active_accounts = Account.objects.filter(is_active=True)

    # 1. Podsumowanie per profil/właściciel konta
    owner_profiles = [
        ('all', '🌐 Wszystkie łącznie', '#0284c7', 'bi-globe2'),
        ('personal', '👤 Moje prywatne', '#0284c7', 'bi-person'),
        ('business', '💼 Moje firmowe (B2B)', '#8b5cf6', 'bi-briefcase'),
        ('partner', '👩‍🦰 Konto partnerki', '#ec4899', 'bi-person-heart'),
        ('joint', '👥 Wspólne domowe', '#10b981', 'bi-piggy-bank'),
    ]

    owner_breakdown = []
    for code, label, color, icon in [
        ('personal', 'Moje prywatne', '#0284c7', 'bi-person'),
        ('business', 'Moje firmowe (B2B)', '#8b5cf6', 'bi-briefcase'),
        ('partner', 'Konto partnerki', '#ec4899', 'bi-person-heart'),
    ]:
        owner_accs = all_active_accounts.filter(owner=code)
        if owner_accs.exists():
            w = sum(a.current_balance for a in owner_accs)
            inc = Transaction.objects.filter(account__in=owner_accs, transaction_type='income', date__year=current_year, date__month=current_month).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            exp = Transaction.objects.filter(account__in=owner_accs, transaction_type='expense', date__year=current_year, date__month=current_month).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            owner_breakdown.append({
                'code': code,
                'label': label,
                'color': color,
                'icon': icon,
                'wealth': w,
                'income': inc,
                'expense': exp,
                'balance': inc - exp,
                'accounts_count': owner_accs.count()
            })

    # Filtrowanie kont według wybranego profilu/konta
    filtered_accounts = all_active_accounts
    if selected_owner and selected_owner != 'all':
        filtered_accounts = filtered_accounts.filter(owner=selected_owner)
    if selected_account_id:
        filtered_accounts = filtered_accounts.filter(pk=selected_account_id)

    total_wealth = sum(acc.current_balance for acc in filtered_accounts)

    # 2. Transakcje z wybranego miesiąca (dla wybranych kont)
    monthly_txs = Transaction.objects.filter(
        account__in=filtered_accounts,
        date__year=current_year,
        date__month=current_month
    )

    monthly_income = monthly_txs.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_expense = monthly_txs.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_balance = monthly_income - monthly_expense
    
    savings_rate = 0.0
    if monthly_income > 0:
        savings_rate = float(min(max((monthly_balance / monthly_income) * 100, Decimal('0.00')), Decimal('100.00')))

    # 3. Wykres kołowy: Podział wydatków wg kategorii w wybranym miesiącu
    category_expenses = (
        Transaction.objects.filter(
            account__in=filtered_accounts,
            transaction_type='expense',
            date__year=current_year,
            date__month=current_month,
            category__isnull=False
        )
        .values('category__name', 'category__color', 'category__icon')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    cat_labels = []
    cat_data = []
    cat_colors = []
    for item in category_expenses:
        icon = item['category__icon'] or '🏷️'
        cat_labels.append(f"{icon} {item['category__name']}")
        cat_data.append(float(item['total']))
        cat_colors.append(item['category__color'] or '#0284c7')

    # 4. Wykres słupkowy: Trend 6 miesięcy wstecz
    trend_labels = []
    trend_incomes = []
    trend_expenses = []

    for i in range(5, -1, -1):
        total_months = current_year * 12 + (current_month - 1) - i
        y = total_months // 12
        m = (total_months % 12) + 1
        month_name = dict(POLISH_MONTHS).get(m, '')[:3]
        trend_labels.append(f"{month_name} {y}")

        inc = Transaction.objects.filter(
            account__in=filtered_accounts,
            transaction_type='income',
            date__year=y,
            date__month=m
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        exp = Transaction.objects.filter(
            account__in=filtered_accounts,
            transaction_type='expense',
            date__year=y,
            date__month=m
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        trend_incomes.append(float(inc))
        trend_expenses.append(float(exp))

    # 5. Limity budżetowe (z automatycznym przenoszeniem z miesiąca na miesiąc)
    budget_items, total_budget_limit, total_budget_spent = get_effective_budget_items(current_year, current_month)

    # 6. Ostatnie transakcje (dla wybranych kont)
    recent_transactions = Transaction.objects.filter(
        account__in=filtered_accounts
    ).select_related('account', 'destination_account', 'category')[:8]

    # 7. Płatności stałe, rachunki i zobowiązania ratalne
    recurring_payments = RecurringPayment.objects.filter(is_active=True).select_related('category', 'account')
    recurring_items = []
    
    for rec in recurring_payments:
        is_paid = rec.is_paid_in_month(current_year, current_month)
        
        due_date = None
        try:
            due_date = date(current_year, current_month, min(rec.due_day, 28))
        except Exception:
            pass

        remaining_inst = rec.get_remaining_installments(current_year, current_month)
        remaining_amt = rec.get_remaining_amount(current_year, current_month)
        progress_pct = rec.get_progress_percentage(current_year, current_month)

        recurring_items.append({
            'obj': rec,
            'is_paid': is_paid,
            'due_date': due_date,
            'remaining_installments': remaining_inst,
            'remaining_amount': remaining_amt,
            'progress_percentage': progress_pct,
            'has_installments': (remaining_inst is not None),
        })

    # Szybki formularz transakcji
    quick_form = TransactionForm(initial={'date': today})

    context = {
        'current_year': current_year,
        'current_month': current_month,
        'month_name': dict(POLISH_MONTHS).get(current_month, ''),
        'polish_months': POLISH_MONTHS,
        'years_list': [today.year - 1, today.year, today.year + 1],
        'selected_owner': selected_owner,
        'owner_profiles': owner_profiles,
        'owner_breakdown': owner_breakdown,
        'total_wealth': total_wealth,
        'accounts': filtered_accounts,
        'all_accounts': all_active_accounts,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'monthly_balance': monthly_balance,
        'savings_rate': savings_rate,
        'cat_labels_json': json.dumps(cat_labels),
        'cat_data_json': json.dumps(cat_data),
        'cat_colors_json': json.dumps(cat_colors),
        'trend_labels_json': json.dumps(trend_labels),
        'trend_incomes_json': json.dumps(trend_incomes),
        'trend_expenses_json': json.dumps(trend_expenses),
        'budget_items': budget_items,
        'total_budget_limit': total_budget_limit,
        'total_budget_spent': total_budget_spent,
        'recent_transactions': recent_transactions,
        'recurring_items': recurring_items,
        'quick_form': quick_form,
    }
    return render(request, 'budget/dashboard.html', context)


@login_required
def transaction_list(request):
    transactions = Transaction.objects.select_related('account', 'destination_account', 'category')

    # Filtrowanie po profilu właściciela
    owner = request.GET.get('owner')
    if owner and owner != 'all':
        transactions = transactions.filter(Q(account__owner=owner) | Q(destination_account__owner=owner))

    # Filtrowanie po typie
    t_type = request.GET.get('type')
    if t_type in ('expense', 'income', 'transfer'):
        transactions = transactions.filter(transaction_type=t_type)

    account_id = request.GET.get('account')
    if account_id:
        transactions = transactions.filter(Q(account_id=account_id) | Q(destination_account_id=account_id))

    category_id = request.GET.get('category')
    if category_id:
        transactions = transactions.filter(category_id=category_id)

    month = request.GET.get('month')
    year = request.GET.get('year')
    if month and year:
        try:
            transactions = transactions.filter(date__year=int(year), date__month=int(month))
        except ValueError:
            pass
    elif year:
        try:
            transactions = transactions.filter(date__year=int(year))
        except ValueError:
            pass

    q = request.GET.get('q', '').strip()
    if q:
        transactions = transactions.filter(
            Q(title__icontains=q) | Q(notes__icontains=q)
        )

    # Eksport CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="transakcje_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Data', 'Typ', 'Właściciel / Profil', 'Tytuł', 'Kwota (PLN)', 'Konto', 'Konto docelowe', 'Kategoria', 'Notatki'])
        
        for t in transactions:
            writer.writerow([
                t.date.strftime('%Y-%m-%d'),
                t.get_transaction_type_display(),
                t.account.get_owner_display() if t.account else '',
                t.title,
                f"{t.amount:.2f}",
                t.account.name if t.account else '',
                t.destination_account.name if t.destination_account else '',
                t.category.name if t.category else '',
                t.notes or ''
            ])
        return response

    # Statystyki przefiltrowanych
    total_income = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_expense = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    net_total = total_income - total_expense

    # Paginacja
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    accounts = Account.objects.all()
    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_total': net_total,
        'accounts': accounts,
        'categories': categories,
        'selected_owner': owner,
        'selected_type': t_type,
        'selected_account': account_id,
        'selected_category': category_id,
        'selected_month': month,
        'selected_year': year,
        'search_query': q,
        'polish_months': POLISH_MONTHS,
    }
    return render(request, 'budget/transaction_list.html', context)


@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            tx = form.save()
            messages.success(request, f'Dodano transakcję: {tx.title} ({tx.amount:,.2f} PLN)')
            next_url = request.POST.get('next') or 'budget_dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Wystąpił błąd formularza. Sprawdź poprawność wpisanych danych.')
    else:
        initial = {'date': timezone.now().date()}
        if request.GET.get('type'):
            initial['transaction_type'] = request.GET.get('type')
        if request.GET.get('account'):
            initial['account'] = request.GET.get('account')
        if request.GET.get('category'):
            initial['category'] = request.GET.get('category')
        form = TransactionForm(initial=initial)

    return render(request, 'budget/transaction_form.html', {'form': form, 'title': 'Nowa transakcja'})


@login_required
def transaction_edit(request, pk):
    tx = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES, instance=tx)
        if form.is_valid():
            form.save()
            messages.success(request, f'Zaktualizowano transakcję: {tx.title}')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=tx)

    return render(request, 'budget/transaction_form.html', {'form': form, 'title': f'Edycja: {tx.title}', 'tx': tx})


@login_required
@require_POST
def transaction_delete(request, pk):
    tx = get_object_or_404(Transaction, pk=pk)
    title = tx.title
    tx.delete()
    messages.info(request, f'Usunięto transakcję: {title}')
    return redirect(request.POST.get('next') or 'transaction_list')


# ==========================================
# KONTA I PORTFELE
# ==========================================

@login_required
def account_list(request):
    accounts = Account.objects.all()
    total_wealth = sum(acc.current_balance for acc in accounts if acc.is_active)
    form = AccountForm()

    return render(request, 'budget/account_list.html', {
        'accounts': accounts,
        'total_wealth': total_wealth,
        'form': form
    })


@login_required
def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            acc = form.save()
            messages.success(request, f'Utworzono konto: {acc.name}')
            return redirect('account_list')
    else:
        form = AccountForm()
    return render(request, 'budget/account_form.html', {'form': form, 'title': 'Nowe konto'})


@login_required
def account_edit(request, pk):
    acc = get_object_or_404(Account, pk=pk)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=acc)
        if form.is_valid():
            form.save()
            messages.success(request, f'Zaktualizowano konto: {acc.name}')
            return redirect('account_list')
    else:
        form = AccountForm(instance=acc)
    return render(request, 'budget/account_form.html', {'form': form, 'title': f'Edycja konta: {acc.name}', 'account': acc})


@login_required
@require_POST
def account_delete(request, pk):
    acc = get_object_or_404(Account, pk=pk)
    if acc.transactions.exists() or acc.incoming_transfers.exists():
        messages.error(request, f'Nie można usunąć konta "{acc.name}", ponieważ są do niego przypisane transakcje. Możesz je dezaktywować.')
    else:
        acc.delete()
        messages.success(request, f'Usunięto konto: {acc.name}')
    return redirect('account_list')


# ==========================================
def get_effective_budget_items(year, month):
    """
    Pobiera limity dla wszystkich kategorii wydatków na dany miesiąc.
    Jeśli dla danego miesiąca nie ma wpisu MonthlyBudget, dziedziczy limit
    z default_budget_limit kategorii lub z ostatniego skonfigurowanego miesiąca.
    """
    categories = Category.objects.filter(category_type='expense').order_by('order', 'name')
    explicit_budgets = {b.category_id: b for b in MonthlyBudget.objects.filter(year=year, month=month)}

    budget_items = []
    total_budget_limit = Decimal('0.00')
    total_budget_spent = Decimal('0.00')

    for cat in categories:
        explicit_b = explicit_budgets.get(cat.id)
        is_custom_month = False
        budget_pk = None

        if explicit_b:
            amount_limit = explicit_b.amount_limit
            is_custom_month = True
            budget_pk = explicit_b.pk
        elif cat.default_budget_limit > 0:
            amount_limit = cat.default_budget_limit
        else:
            # Szukamy ostatniego znanego limitu z przeszłości
            past_b = MonthlyBudget.objects.filter(
                category=cat,
                year__lte=year
            ).exclude(year=year, month__gt=month).order_by('-year', '-month').first()
            if past_b and past_b.amount_limit > 0:
                amount_limit = past_b.amount_limit
            else:
                amount_limit = Decimal('0.00')

        spent = Transaction.objects.filter(
            category=cat,
            transaction_type='expense',
            date__year=year,
            date__month=month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        if amount_limit > 0 or spent > 0:
            total_budget_limit += amount_limit
            total_budget_spent += spent
            percentage = 0.0
            if amount_limit > 0:
                percentage = min(100.0, float((spent / amount_limit) * 100))

            budget_items.append({
                'category': cat,
                'category_id': cat.id,
                'limit': amount_limit,
                'spent': spent,
                'percentage': percentage,
                'remaining': amount_limit - spent,
                'is_exceeded': spent > amount_limit,
                'is_custom_month': is_custom_month,
                'budget_pk': budget_pk,
            })

    return budget_items, total_budget_limit, total_budget_spent


# ==========================================
# USTAWIENIA, LIMITY BUDŻETOWE & PŁATNOŚCI STAŁE
# ==========================================

@login_required
def budget_settings(request):
    today = timezone.now().date()
    current_year = int(request.GET.get('year', today.year))
    current_month = int(request.GET.get('month', today.month))

    categories_expense = Category.objects.filter(category_type='expense')
    categories_income = Category.objects.filter(category_type='income')
    
    budget_items, total_budget_limit, total_budget_spent = get_effective_budget_items(current_year, current_month)
    recurring_payments = RecurringPayment.objects.all().select_related('category', 'account')

    # Przygotowanie danych rat i statusu opłacenia dla płatności stałych
    recurring_items = []
    for rec in recurring_payments:
        recurring_items.append({
            'obj': rec,
            'is_paid': rec.is_paid_in_month(current_year, current_month),
            'remaining_installments': rec.get_remaining_installments(current_year, current_month),
            'remaining_amount': rec.get_remaining_amount(current_year, current_month),
            'progress_percentage': rec.get_progress_percentage(current_year, current_month),
        })

    category_form = CategoryForm()
    budget_form = MonthlyBudgetForm(initial={'year': current_year, 'month': current_month})
    recurring_form = RecurringPaymentForm()

    context = {
        'categories_expense': categories_expense,
        'categories_income': categories_income,
        'budget_items': budget_items,
        'total_budget_limit': total_budget_limit,
        'total_budget_spent': total_budget_spent,
        'recurring_items': recurring_items,
        'current_year': current_year,
        'current_month': current_month,
        'month_name': dict(POLISH_MONTHS).get(current_month, ''),
        'polish_months': POLISH_MONTHS,
        'category_form': category_form,
        'budget_form': budget_form,
        'recurring_form': recurring_form,
    }
    return render(request, 'budget/budget_settings.html', context)


@login_required
@require_POST
def category_create(request):
    form = CategoryForm(request.POST)
    if form.is_valid():
        cat = form.save()
        messages.success(request, f'Dodano kategorię: {cat.name}')
    else:
        messages.error(request, 'Błąd podczas tworzenia kategorii.')
    return redirect('budget_settings')


@login_required
@require_POST
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    name = cat.name
    cat.delete()
    messages.info(request, f'Usunięto kategorię: {name}')
    return redirect('budget_settings')


@login_required
@require_POST
def budget_goal_save(request):
    category_id = request.POST.get('category')
    year = int(request.POST.get('year', timezone.now().year))
    month = int(request.POST.get('month', timezone.now().month))
    amount = Decimal(request.POST.get('amount_limit', '0.00'))
    apply_to_future = request.POST.get('apply_to_all_future') == 'on' or request.POST.get('apply_to_all_future') == '1'

    category = get_object_or_404(Category, pk=category_id)

    if apply_to_future:
        category.default_budget_limit = amount
        category.save()

    budget_obj, created = MonthlyBudget.objects.update_or_create(
        category=category,
        year=year,
        month=month,
        defaults={'amount_limit': amount}
    )
    msg_suffix = " (i ustawiono jako stały limit na kolejne miesiące)" if apply_to_future else ""
    messages.success(request, f'Zapisano limit dla: {category.name} ({amount:,.2f} PLN){msg_suffix}')
    return redirect(f'/budzet/ustawienia/?year={year}&month={month}')


@login_required
@require_POST
def budget_goal_delete(request, pk):
    b = get_object_or_404(MonthlyBudget, pk=pk)
    y, m = b.year, b.month
    b.delete()
    messages.info(request, 'Usunięto miesięczny limit budżetowy.')
    return redirect(f'/budzet/ustawienia/?year={y}&month={m}')


@login_required
@require_POST
def recurring_payment_create(request):
    form = RecurringPaymentForm(request.POST)
    if form.is_valid():
        rec = form.save()
        messages.success(request, f'Dodano płatność stałą / ratę: {rec.title}')
    else:
        messages.error(request, 'Błąd podczas dodawania płatności stałej.')
    return redirect('budget_settings')


@login_required
@require_POST
def recurring_payment_toggle_paid(request, pk):
    rec = get_object_or_404(RecurringPayment, pk=pk)
    today = timezone.now().date()

    target_year = int(request.POST.get('year', today.year))
    target_month = int(request.POST.get('month', today.month))
    
    # Sprawdzamy czy w docelowym miesiącu jest już opłacona
    if not rec.is_paid_in_month(target_year, target_month):
        target_day = min(rec.due_day, 28)
        try:
            paid_date = date(target_year, target_month, target_day)
        except Exception:
            paid_date = today

        rec.last_paid_date = paid_date
        rec.save()

        # Tworzymy transakcję wydatku (o ile jeszcze nie istnieje)
        if rec.account:
            tx_title = f"[Stała opłata] {rec.title}"
            if not Transaction.objects.filter(account=rec.account, title=tx_title, date__year=target_year, date__month=target_month).exists():
                Transaction.objects.create(
                    account=rec.account,
                    category=rec.category,
                    transaction_type='expense',
                    amount=rec.amount,
                    date=paid_date,
                    title=tx_title,
                    notes=f"Automatyczny wpis z listy opłat cyklicznych ({rec.get_frequency_display()})"
                )
                messages.success(request, f'Oznaczono jako opłacone w {target_month:02d}/{target_year} i dodano wydatek {rec.amount:,.2f} PLN!')
            else:
                messages.success(request, f'Oznaczono płatność "{rec.title}" jako opłaconą.')
        else:
            messages.success(request, f'Oznaczono płatność "{rec.title}" jako opłaconą.')
    else:
        rec.last_paid_date = None
        rec.save()

        # Usuwamy automatycznie wygenerowany wydatek z tego miesiąca
        Transaction.objects.filter(
            account=rec.account,
            title=f"[Stała opłata] {rec.title}",
            date__year=target_year,
            date__month=target_month
        ).delete()
        messages.info(request, f'Cofnięto status opłacenia dla "{rec.title}".')

    return redirect(request.POST.get('next') or 'budget_dashboard')


@login_required
@require_POST
def recurring_payment_delete(request, pk):
    rec = get_object_or_404(RecurringPayment, pk=pk)
    title = rec.title
    rec.delete()
    messages.info(request, f'Usunięto płatność stałą: {title}')
    return redirect('budget_settings')


def ensure_default_accounts():
    if not Account.objects.filter(is_active=True).exists():
        Account.objects.create(
            name='Konto Prywatne (Jakub)',
            owner='personal',
            account_type='checking',
            initial_balance=Decimal('0.00'),
            currency='PLN',
            icon='bi-person-badge',
            color='#0284c7',
            notes='Główne konto osobiste / ROR'
        )
        Account.objects.create(
            name='Konto Firmowe (B2B / Działalność)',
            owner='business',
            account_type='checking',
            initial_balance=Decimal('0.00'),
            currency='PLN',
            icon='bi-briefcase',
            color='#8b5cf6',
            notes='Rachunek firmowy / B2B'
        )
        Account.objects.create(
            name='Konto Partnerki',
            owner='partner',
            account_type='checking',
            initial_balance=Decimal('0.00'),
            currency='PLN',
            icon='bi-person-heart',
            color='#ec4899',
            notes='Rachunek bankowy partnerki'
        )


# ==========================================
# IMPORT TRANSAKCJI Z PLIKÓW CSV BANKÓW
# ==========================================

@login_required
def import_csv_view(request):
    from .importer import parse_bank_csv, parse_date_str

    ensure_default_accounts()
    accounts = Account.objects.filter(is_active=True)
    categories = Category.objects.all()

    if request.method == 'POST' and request.FILES.get('csv_file'):
        account_id = request.POST.get('account')
        account = get_object_or_404(Account, pk=account_id)
        csv_file = request.FILES['csv_file']

        file_bytes = csv_file.read()
        parsed_rows = parse_bank_csv(file_bytes, account)

        if not parsed_rows:
            messages.warning(request, 'Nie znaleziono żadnych poprawnych transakcji w przesłanym pliku. Upewnij się, że plik ma format CSV.')
            return redirect('import_csv')

        # Zapisanie w sesji na potrzeby potwierdzenia
        session_data = []
        for r in parsed_rows:
            session_data.append({
                'date': r['date_str'],
                'title': r['title'],
                'amount': r['amount_str'],
                'type': r['type'],
                'category_id': r['category_id'],
                'is_duplicate': r['is_duplicate'],
            })
        request.session['import_csv_rows'] = session_data
        request.session['import_csv_account_id'] = account.id

        total_rows = len(parsed_rows)
        duplicates_count = sum(1 for r in parsed_rows if r['is_duplicate'])
        expenses_count = sum(1 for r in parsed_rows if r['type'] == 'expense')
        incomes_count = sum(1 for r in parsed_rows if r['type'] == 'income')

        return render(request, 'budget/import_csv.html', {
            'step': 'preview',
            'account': account,
            'parsed_rows': parsed_rows,
            'categories': categories,
            'total_rows': total_rows,
            'duplicates_count': duplicates_count,
            'expenses_count': expenses_count,
            'incomes_count': incomes_count,
        })

    return render(request, 'budget/import_csv.html', {
        'step': 'upload',
        'accounts': accounts,
    })


@login_required
@require_POST
def import_csv_confirm(request):
    from django.db import transaction as db_atomic
    from .importer import parse_date_str

    session_rows = request.session.get('import_csv_rows')
    account_id = request.session.get('import_csv_account_id')

    if not session_rows or not account_id:
        messages.error(request, 'Sesja importu wygasła lub plik nie został przesłany. Rozpocznij import ponownie.')
        return redirect('import_csv')

    account = get_object_or_404(Account, pk=account_id)
    
    # Obsługa pojedynczego pakietu JSON (wydajne dla setek/tysięcy rekordów)
    payload_str = request.POST.get('import_payload')
    items_to_import = []

    if payload_str:
        try:
            parsed_items = json.loads(payload_str)
            for item in parsed_items:
                idx = item.get('idx')
                cat_id = item.get('cat_id')
                if idx is not None and 0 <= idx < len(session_rows):
                    items_to_import.append((idx, cat_id))
        except Exception:
            items_to_import = []

    # Fallback dla klasycznego POST
    if not items_to_import:
        selected_indices = request.POST.getlist('selected_rows')
        for idx_str in selected_indices:
            try:
                idx = int(idx_str)
                if 0 <= idx < len(session_rows):
                    cat_id = request.POST.get(f'category_{idx}')
                    items_to_import.append((idx, cat_id))
            except (ValueError, TypeError):
                continue

    if not items_to_import:
        messages.warning(request, 'Nie zaznaczono żadnych transakcji do zaimportowania.')
        return redirect('import_csv')

    imported_count = 0
    with db_atomic.atomic():
        for idx, cat_id in items_to_import:
            row = session_rows[idx]

            # Sprawdzenie kategorii
            final_cat_id = cat_id or row.get('category_id')
            cat = None
            if final_cat_id:
                cat = Category.objects.filter(pk=final_cat_id).first()

            t_date = parse_date_str(row['date'])
            t_amount = Decimal(str(row['amount']))
            t_type = row['type']
            t_title = row['title']

            Transaction.objects.create(
                account=account,
                category=cat,
                transaction_type=t_type,
                amount=t_amount,
                date=t_date,
                title=t_title,
                notes="Zaimportowano z wyciągu bankowego CSV"
            )
            imported_count += 1

    request.session.pop('import_csv_rows', None)
    request.session.pop('import_csv_account_id', None)

    messages.success(request, f'Sukces! Zaimportowano {imported_count} transakcji do konta "{account.name}".')
    return redirect('transaction_list')
