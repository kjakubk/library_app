import csv
import json
from decimal import Decimal
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

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

    # 1. Konta i majątek całkowity
    accounts = Account.objects.filter(is_active=True)
    total_wealth = sum(acc.current_balance for acc in accounts)

    # 2. Transakcje z wybranego miesiąca
    monthly_txs = Transaction.objects.filter(
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
        m_date = selected_date - relativedelta(months=i)
        y, m = m_date.year, m_date.month
        month_name = dict(POLISH_MONTHS).get(m, '')[:3]
        trend_labels.append(f"{month_name} {y}")

        inc = Transaction.objects.filter(
            transaction_type='income',
            date__year=y,
            date__month=m
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        exp = Transaction.objects.filter(
            transaction_type='expense',
            date__year=y,
            date__month=m
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        trend_incomes.append(float(inc))
        trend_expenses.append(float(exp))

    # 5. Limity budżetowe na dany miesiąc
    monthly_budgets = MonthlyBudget.objects.filter(
        year=current_year,
        month=current_month
    ).select_related('category')

    budget_items = []
    total_budget_limit = Decimal('0.00')
    total_budget_spent = Decimal('0.00')

    for b in monthly_budgets:
        spent = b.spent_amount
        total_budget_limit += b.amount_limit
        total_budget_spent += spent
        budget_items.append({
            'obj': b,
            'spent': spent,
            'limit': b.amount_limit,
            'percentage': b.percentage_used,
            'remaining': b.remaining_amount,
            'is_exceeded': b.is_exceeded,
        })

    # 6. Ostatnie 8 transakcji
    recent_transactions = Transaction.objects.select_related('account', 'destination_account', 'category')[:8]

    # 7. Płatności stałe i rachunki
    recurring_payments = RecurringPayment.objects.filter(is_active=True).select_related('category', 'account')
    recurring_items = []
    
    for rec in recurring_payments:
        # Sprawdzamy czy w bieżącym miesiącu istnieje wydatek powiązany
        is_paid = False
        if rec.last_paid_date and rec.last_paid_date.year == current_year and rec.last_paid_date.month == current_month:
            is_paid = True
        
        due_date = None
        try:
            due_date = date(current_year, current_month, min(rec.due_day, 28))
        except Exception:
            pass

        recurring_items.append({
            'obj': rec,
            'is_paid': is_paid,
            'due_date': due_date,
        })

    # Szybki formularz transakcji
    quick_form = TransactionForm(initial={'date': today})

    context = {
        'current_year': current_year,
        'current_month': current_month,
        'month_name': dict(POLISH_MONTHS).get(current_month, ''),
        'polish_months': POLISH_MONTHS,
        'years_list': [today.year - 1, today.year, today.year + 1],
        'total_wealth': total_wealth,
        'accounts': accounts,
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

    # Filtrowanie
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
        writer.writerow(['Data', 'Typ', 'Tytuł', 'Kwota (PLN)', 'Konto', 'Konto docelowe', 'Kategoria', 'Notatki'])
        
        for t in transactions:
            writer.writerow([
                t.date.strftime('%Y-%m-%d'),
                t.get_transaction_type_display(),
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
# USTAWIENIA, LIMITY BUDŻETOWE & PŁATNOŚCI STAŁE
# ==========================================

@login_required
def budget_settings(request):
    today = timezone.now().date()
    current_year = int(request.GET.get('year', today.year))
    current_month = int(request.GET.get('month', today.month))

    categories_expense = Category.objects.filter(category_type='expense')
    categories_income = Category.objects.filter(category_type='income')
    
    monthly_budgets = MonthlyBudget.objects.filter(year=current_year, month=current_month).select_related('category')
    recurring_payments = RecurringPayment.objects.all().select_related('category', 'account')

    category_form = CategoryForm()
    budget_form = MonthlyBudgetForm(initial={'year': current_year, 'month': current_month})
    recurring_form = RecurringPaymentForm()

    context = {
        'categories_expense': categories_expense,
        'categories_income': categories_income,
        'monthly_budgets': monthly_budgets,
        'recurring_payments': recurring_payments,
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

    category = get_object_or_404(Category, pk=category_id)
    budget_obj, created = MonthlyBudget.objects.update_or_create(
        category=category,
        year=year,
        month=month,
        defaults={'amount_limit': amount}
    )
    messages.success(request, f'Zapisano limit dla: {category.name} ({amount:,.2f} PLN)')
    return redirect(f'/budzet/ustawienia/?year={year}&month={month}')


@login_required
@require_POST
def budget_goal_delete(request, pk):
    b = get_object_or_404(MonthlyBudget, pk=pk)
    y, m = b.year, b.month
    b.delete()
    messages.info(request, 'Usunięto limit budżetowy.')
    return redirect(f'/budzet/ustawienia/?year={y}&month={m}')


@login_required
@require_POST
def recurring_payment_create(request):
    form = RecurringPaymentForm(request.POST)
    if form.is_valid():
        rec = form.save()
        messages.success(request, f'Dodano płatność stałą: {rec.title}')
    else:
        messages.error(request, 'Błąd podczas dodawania płatności stałej.')
    return redirect('budget_settings')


@login_required
@require_POST
def recurring_payment_toggle_paid(request, pk):
    rec = get_object_or_404(RecurringPayment, pk=pk)
    today = timezone.now().date()
    
    # Jeśli oznaczono jako opłacone, twórz automatycznie transakcję wydatku
    if not (rec.last_paid_date and rec.last_paid_date.year == today.year and rec.last_paid_date.month == today.month):
        rec.last_paid_date = today
        rec.save()

        # Tworzymy transakcję wydatku
        if rec.account:
            Transaction.objects.create(
                account=rec.account,
                category=rec.category,
                transaction_type='expense',
                amount=rec.amount,
                date=today,
                title=f"[Stała opłata] {rec.title}",
                notes=f"Automatyczny wpis z listy opłat cyklicznych ({rec.get_frequency_display()})"
            )
            messages.success(request, f'Oznaczono jako opłacone i dodano wydatek {rec.amount:,.2f} PLN!')
        else:
            messages.success(request, f'Oznaczono płatność "{rec.title}" jako opłaconą w tym miesiącu.')
    else:
        rec.last_paid_date = None
        rec.save()
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
