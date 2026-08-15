# da_portfolio/urls.py
from django.urls import path
from . import views

app_name = 'da_portfolio'

urlpatterns = [
    path('', views.game_market_view, name='game_market'),
]