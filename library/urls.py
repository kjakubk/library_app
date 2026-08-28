from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 1. PORCELANA
    # ==========================================
    path('porcelana/', views.porcelain_list, name='porcelain_list'),
    path('porcelana/dodaj/', views.porcelain_create, name='porcelain_create'),
    path('porcelana/<int:pk>/edytuj/', views.porcelain_edit, name='porcelain_edit'),
    path('porcelana/<int:pk>/duplikuj/', views.porcelain_duplicate, name='porcelain_duplicate'),
    path('porcelana/<int:pk>/usun/', views.porcelain_delete, name='porcelain_delete'),

    # ==========================================
    # 2. PŁYTY WINYLOWE
    # ==========================================
    path('winyle/', views.vinyl_list, name='vinyl_list'),
    path('winyle/dodaj/', views.vinyl_create, name='vinyl_create'),
    path('winyle/<int:pk>/edytuj/', views.vinyl_edit, name='vinyl_edit'),
    path('winyle/<int:pk>/usun/', views.vinyl_delete, name='vinyl_delete'),

    # ==========================================
    # 3. GRY WIDEO
    # ==========================================
    path('gry-wideo/', views.video_game_list, name='video_game_list'),
    path('gry-wideo/dodaj/', views.video_game_create, name='video_game_create'),
    path('gry-wideo/<int:pk>/edytuj/', views.video_game_edit, name='video_game_edit'),
    path('gry-wideo/<int:pk>/usun/', views.video_game_delete, name='video_game_delete'),

    # ==========================================
    # 4. GRY PLANSZOWE
    # ==========================================
    path('planszowki/', views.board_game_list, name='board_game_list'),
    path('planszowki/dodaj/', views.board_game_create, name='board_game_create'),
    path('planszowki/<int:pk>/edytuj/', views.board_game_edit, name='board_game_edit'),
    path('planszowki/<int:pk>/usun/', views.board_game_delete, name='board_game_delete'),

    # ==========================================
    # 5. KSIĄŻKI
    # ==========================================
    path('ksiazki/', views.book_list, name='book_list'),
    path('ksiazki/dodaj/', views.book_create, name='book_create'),
    path('ksiazki/import/', views.book_import_csv, name='book_import_csv'),
    path('ksiazki/napraw-okladki/', views.fix_missing_covers, name='fix_missing_covers'),
    path('ksiazki/napraw-wszystkie-okladki/', views.fix_all_covers, name='fix_all_covers'),
    path('ksiazki/masowa-akcja/', views.book_bulk_update, name='book_bulk_update'),
    path('ksiazki/<int:pk>/', views.book_detail, name='book_detail'),
    path('ksiazki/<int:pk>/edytuj/', views.book_edit, name='book_edit'),
    path('ksiazki/<int:pk>/usun/', views.book_delete, name='book_delete'),
    path('ksiazki/<int:pk>/delete/', views.book_delete),
    path('ksiazki/<int:pk>/postep/', views.book_update_progress, name='book_update_progress'),
    path('ksiazki/<int:pk>/toggle-read/', views.toggle_book_read, name='toggle_book_read'),

    # ==========================================
    # 6. KONSOLE I AKCESORIA
    # ==========================================
    path('konsole/', views.console_list, name='console_list'),
    path('konsole/dodaj/', views.console_create, name='console_create'),
    path('konsole/<int:pk>/edytuj/', views.console_update, name='console_update'),
    path('konsole/<int:pk>/usun/', views.console_delete, name='console_delete'),

    # ==========================================
    # 7. INNE ANTYKI
    # ==========================================
    path('antyki/', views.antique_list, name='antique_list'),
    path('antyki/dodaj/', views.antique_create, name='antique_create'),
    path('antyki/<int:pk>/edytuj/', views.antique_update, name='antique_update'),
    path('antyki/<int:pk>/usun/', views.antique_delete, name='antique_delete'),

    # ==========================================
    # 8. GRY CYFROWE
    # ==========================================
    path('gry-cyfrowe/', views.digital_game_list, name='digital_game_list'),
    path('gry-cyfrowe/dodaj/', views.digital_game_create, name='digital_game_create'),
    path('gry-cyfrowe/<int:pk>/edytuj/', views.digital_game_edit, name='digital_game_edit'),
    path('gry-cyfrowe/<int:pk>/usun/', views.digital_game_delete, name='digital_game_delete'),

    # ==========================================
    # 9. ENDPOINTY API (ISBN LOOKUP)
    # ==========================================
    path('api/ksiazka/<str:isbn>/', views.fetch_book_data, name='fetch_book_data'),
    path('api/steam/fetch_games/', views.steam_fetch_games, name='steam_fetch_games'),
    path('api/steam/import_game/', views.steam_import_game, name='steam_import_game'),
    path('api/heroic/import/', views.heroic_import, name='heroic_import'),
    path('api/gry-cyfrowe/bulk-delete/', views.digital_game_bulk_delete, name='digital_game_bulk_delete'),
    path('api/libib/import_game/', views.libib_import_game, name='libib_import_game'),
]