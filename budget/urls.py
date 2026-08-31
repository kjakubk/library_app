from django.urls import path
from . import views

urlpatterns = [
    # Dashboard główny
    path('', views.budget_dashboard, name='budget_dashboard'),

    # Transakcje
    path('transakcje/', views.transaction_list, name='transaction_list'),
    path('transakcje/dodaj/', views.transaction_create, name='transaction_create'),
    path('transakcje/<int:pk>/edytuj/', views.transaction_edit, name='transaction_edit'),
    path('transakcje/<int:pk>/usun/', views.transaction_delete, name='transaction_delete'),

    # Konta i portfele
    path('konta/', views.account_list, name='account_list'),
    path('konta/dodaj/', views.account_create, name='account_create'),
    path('konta/<int:pk>/edytuj/', views.account_edit, name='account_edit'),
    path('konta/<int:pk>/usun/', views.account_delete, name='account_delete'),

    # Ustawienia, limity i kategorie
    path('ustawienia/', views.budget_settings, name='budget_settings'),
    path('kategorie/dodaj/', views.category_create, name='category_create'),
    path('kategorie/<int:pk>/usun/', views.category_delete, name='category_delete'),
    path('limity/zapisz/', views.budget_goal_save, name='budget_goal_save'),
    path('limity/<int:pk>/usun/', views.budget_goal_delete, name='budget_goal_delete'),

    # Płatności cykliczne
    path('platnosci-stale/dodaj/', views.recurring_payment_create, name='recurring_payment_create'),
    path('platnosci-stale/<int:pk>/oplac/', views.recurring_payment_toggle_paid, name='recurring_payment_toggle_paid'),
    path('platnosci-stale/<int:pk>/usun/', views.recurring_payment_delete, name='recurring_payment_delete'),
]
