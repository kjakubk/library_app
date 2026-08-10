from django.urls import path
from . import views

urlpatterns = [
    # Główny adres dla widoku CV
    path('cv/', views.cv_view, name='cv_view'),
    path('', views.portfolio_gallery, name='portfolio_gallery'),
    path('dodaj/', views.add_photo, name='add_photo'),
    path('dodaj-album/', views.add_album, name='add_album'),
    path('zdjecie/<int:pk>/usun/', views.delete_photo, name='delete_photo'),
]