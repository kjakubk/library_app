from django.contrib import admin
from .models import Account, Category, Transaction, MonthlyBudget, RecurringPayment


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'initial_balance', 'currency', 'is_active', 'created_at')
    list_filter = ('account_type', 'is_active', 'currency')
    search_fields = ('name', 'notes')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'category_type', 'color', 'is_default', 'order')
    list_filter = ('category_type', 'is_default')
    search_fields = ('name',)
    list_editable = ('order',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'transaction_type', 'amount', 'account', 'destination_account', 'category', 'created_at')
    list_filter = ('transaction_type', 'account', 'category', 'date')
    search_fields = ('title', 'notes')
    date_hierarchy = 'date'


@admin.register(MonthlyBudget)
class MonthlyBudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'year', 'month', 'amount_limit', 'created_at')
    list_filter = ('year', 'month', 'category')


@admin.register(RecurringPayment)
class RecurringPaymentAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'category', 'account', 'frequency', 'due_day', 'is_active', 'last_paid_date')
    list_filter = ('frequency', 'is_active', 'account')
    search_fields = ('title', 'notes')
