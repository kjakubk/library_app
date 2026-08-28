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
    path('cv/', portfolio_views.cv_view, name='cv_view'),
    path('cv/profil/zapisz/', portfolio_views.cv_profile_update, name='cv_profile_update'),
    path('cv/doswiadczenie/zapisz/', portfolio_views.cv_experience_save, name='cv_experience_add'),
    path('cv/doswiadczenie/<int:pk>/zapisz/', portfolio_views.cv_experience_save, name='cv_experience_edit'),
    path('cv/doswiadczenie/<int:pk>/usun/', portfolio_views.cv_experience_delete, name='cv_experience_delete'),
    path('cv/edukacja/zapisz/', portfolio_views.cv_education_save, name='cv_education_add'),
    path('cv/edukacja/<int:pk>/zapisz/', portfolio_views.cv_education_save, name='cv_education_edit'),
    path('cv/edukacja/<int:pk>/usun/', portfolio_views.cv_education_delete, name='cv_education_delete'),
    path('cv/umiejetnosc/dodaj/', portfolio_views.cv_skill_add, name='cv_skill_add'),
    path('cv/umiejetnosc/<int:pk>/usun/', portfolio_views.cv_skill_delete, name='cv_skill_delete'),
    path('cv/jezyk/dodaj/', portfolio_views.cv_language_add, name='cv_language_add'),
    path('cv/jezyk/<int:pk>/usun/', portfolio_views.cv_language_delete, name='cv_language_delete'),
    path('cv/certyfikat/dodaj/', portfolio_views.cv_certificate_add, name='cv_certificate_add'),
    path('cv/certyfikat/<int:pk>/usun/', portfolio_views.cv_certificate_delete, name='cv_certificate_delete'),
    path('cv/projekt/zapisz/', portfolio_views.cv_project_save, name='cv_project_add'),
    path('cv/projekt/<int:pk>/zapisz/', portfolio_views.cv_project_save, name='cv_project_edit'),
    path('cv/projekt/<int:pk>/usun/', portfolio_views.cv_project_delete, name='cv_project_delete'),
    path('cv/hobby/dodaj/', portfolio_views.cv_hobby_add, name='cv_hobby_add'),
    path('cv/hobby/<int:pk>/usun/', portfolio_views.cv_hobby_delete, name='cv_hobby_delete'),
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