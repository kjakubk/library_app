from django.urls import path
from . import views

urlpatterns = [
    path('', views.portfolio_gallery, name='portfolio_gallery'),
    path('dodaj/', views.add_photo, name='add_photo'),
    path('dodaj-album/', views.add_album, name='add_album'),
    path('zdjecie/<int:pk>/edytuj/', views.edit_photo, name='edit_photo'),
    path('zdjecie/<int:pk>/usun/', views.delete_photo, name='delete_photo'),
    path('album/<int:pk>/edytuj/', views.edit_album, name='edit_album'),
    path('album/<int:pk>/usun/', views.delete_album, name='delete_album'),
    path('api/kolejnosc/', views.update_photo_order, name='update_photo_order'),
    path('logowanie/', views.login_view, name='login'),
    path('wyloguj/', views.logout_view, name='logout'),
]