from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 1. AUTORYZACJA I SESJA
    # ==========================================
    path('dostep/', views.library_access, name='library_access'),
    path('wyloguj/', views.library_logout, name='library_logout'),

    # ==========================================
    # 2. LISTY KOLEKCJI
    # ==========================================
    path('porcelana/', views.porcelain_list, name='porcelain_list'),
    path('winyle/', views.vinyl_list, name='vinyl_list'),
    path('ksiazki/', views.book_list, name='book_list'),
    path('planszowki/', views.board_game_list, name='board_game_list'),
    path('gry-wideo/', views.video_game_list, name='video_game_list'),

    # ==========================================
    # 3. FORMULARZE I AKCJE (INNE KOLEKCJE)
    # ==========================================
    path('winyle/dodaj/', views.vinyl_create, name='vinyl_create'),

    # ==========================================
    # 4. KSIĄŻKI (DODawanie, IMPORT, SZCZEGÓŁY, EDYCJA)
    # WAŻNE: Ścieżki statyczne (dodaj, import) muszą być PRZED dynamicznymi (<int:pk>)!
    # ==========================================
    path('ksiazki/dodaj/', views.book_create, name='book_create'),
    path('ksiazki/import/', views.book_import_csv, name='book_import_csv'),
    path('ksiazki/<int:pk>/', views.book_detail, name='book_detail'),
    path('ksiazki/<int:pk>/edytuj/', views.book_edit, name='book_edit'),
    path('ksiazki/<int:pk>/postep/', views.book_update_progress, name='book_update_progress'),
    path('ksiazki/napraw-okladki/', views.fix_missing_covers, name='fix_missing_covers'),
    path('ksiazki/napraw-okladki/', views.fix_all_covers, name='fix_all_covers'),
    path('ksiazki/masowa-akcja/', views.book_bulk_update, name='book_bulk_update'),
    path('ksiazki/<int:pk>/toggle-read/', views.toggle_book_read, name='toggle_book_read'),
    path('porcelana/', views.porcelain_list, name='porcelain_list'),
    path('porcelana/dodaj/', views.porcelain_create, name='porcelain_create'),
    path('porcelana/<int:pk>/edytuj/', views.porcelain_edit, name='porcelain_edit'),
    path('porcelana/<int:pk>/usun/', views.porcelain_delete, name='porcelain_delete'),

    # ==========================================
    # 5. ENDPOINTY API (ASYNCHRONICZNE POBIERANIE)
    # ==========================================
    path('api/ksiazka/<str:isbn>/', views.fetch_book_data, name='fetch_book_data'),

]

# Serwowanie plików multimedialnych (zdjęć okładek) w trybie deweloperskim
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)