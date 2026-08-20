"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from portfolio import views as portfolio_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', portfolio_views.home_view, name='home'),
    path('galeria/', include('portfolio.urls')),
    path('logowanie/', portfolio_views.login_view, name='login'),
    path('wyloguj/', portfolio_views.logout_view, name='logout'),
    path('uzytkownicy/', portfolio_views.user_list_view, name='user_list'),
    path('uzytkownicy/dodaj/', portfolio_views.user_create_view, name='user_create'),
    path('uzytkownicy/<int:pk>/usun/', portfolio_views.user_delete_view, name='user_delete'),
    path('uzytkownicy/<int:pk>/haslo/', portfolio_views.user_change_password_view, name='user_change_password'),
    path('kopia-zapasowa/pobierz/', portfolio_views.download_backup_zip, name='download_backup_zip'),
    path('kolekcje/', include('library.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')