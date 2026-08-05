from django.urls import path
from . import views

urlpatterns = [
    # Główny adres dla widoku CV
    path('', views.cv_view, name='cv_view'),
]