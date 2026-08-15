import csv
import json
import ssl
import io
import re
import urllib.request

from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookForm, CSVImportForm, VinylRecordForm, PorcelainForm, BoardGameForm, VideoGameForm
from .models import BoardGame, Book, Porcelain, VideoGame, VinylRecord, CATEGORY_CHOICES
from .book_services import (
    get_unified_book_data, 
    download_and_save_book_cover, 
    find_best_cover_for_book,
    find_cover_in_google_books,
    find_cover_in_openlibrary_cdn,
    find_cover_in_openlibrary_search,
    find_cover_in_wolne_lektury,
    get_all_isbn_variants
)


# ==========================================
# 1. PORCELANA
# ==========================================

@login_required
def porcelain_list(request):
    """Lista elementów porcelany z wyszukiwarką, filtrami i sortowaniem."""
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'name')
    selected_style = request.GET.get('style', '').strip()
    selected_signature = request.GET.get('signature', '').strip()
    
    items = Porcelain.objects.all()

    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(signature__icontains=query) |
            Q(style__icontains=query)
        )

    if selected_style:
        items = items.filter(style=selected_style)

    if selected_signature:
        items = items.filter(signature=selected_signature)

    sort_mapping = {
        'name': 'name',
        '-name': '-name',
        'signature': 'signature',
        '-signature': '-signature',
        'condition': 'condition',
        '-condition': '-condition',
    }
    
    if sort_by in sort_mapping:
        items = items.order_by(sort_mapping[sort_by])

    available_styles = Porcelain.objects.exclude(style__isnull=True).exclude(style__exact='').values_list('style', flat=True).distinct().order_by('style')
    available_signatures = Porcelain.objects.exclude(signature__isnull=True).exclude(signature__exact='').values_list('signature', flat=True).distinct().order_by('signature')

    name_stats = Porcelain.objects.values('name').annotate(count=Count('id')).order_by('-count')[:5]
    signature_stats = Porcelain.objects.exclude(signature__isnull=True).exclude(signature__exact='').values_list('signature').annotate(count=Count('id')).order_by('-count')[:5]
    total_count = items.count()

    context = {
        'items': items,
        'name_stats': name_stats,
        'signature_stats': signature_stats,
        'total_count': total_count,
        'current_sort': sort_by,
        'available_styles': available_styles,
        'available_signatures': available_signatures,
        'selected_style': selected_style,
        'selected_signature': selected_signature,
    }
    return render(request, 'library/porcelain_list.html', context)


@login_required
def porcelain_create(request):
    """Dodawanie nowego elementu porcelany."""
    if request.method == 'POST':
        form = PorcelainForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pomyślnie dodano nowy element porcelany!')
            return redirect('porcelain_list')
    else:
        form = PorcelainForm()
        
    return render(request, 'library/porcelain_form.html', {'form': form})


@login_required
def porcelain_edit(request, pk):
    """Edycja elementu porcelany z opcją usuwania pojedynczych zdjęć."""
    item = get_object_or_404(Porcelain, pk=pk)
    
    delete_img_field = request.GET.get('delete_img')
    if delete_img_field in ['signature_image', 'image_1', 'image_2', 'image_3']:
        image_field = getattr(item, delete_img_field, None)
        if image_field:
            image_field.delete(save=False)
            setattr(item, delete_img_field, None)
            item.save()
            messages.success(request, 'Zdjęcie zostało pomyślnie usunięte.')
            return redirect('porcelain_edit', pk=item.pk)

    if request.method == 'POST':
        form = PorcelainForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zmiany w elemencie porcelany zostały pomyślnie zapisane.')
            return redirect('porcelain_list')
    else:
        form = PorcelainForm(instance=item)
    
    return render(request, 'library/porcelain_form.html', {'form': form, 'item': item})


@login_required
def porcelain_delete(request, pk):
    """Usuwanie elementu porcelany."""
    item = get_object_or_404(Porcelain, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Element porcelany został pomyślnie usunięty z kolekcji.')
        return redirect('porcelain_list')
    
    return render(request, 'library/porcelain_confirm_delete.html', {'item': item})


# ==========================================
# 2. PŁYTY WINYLOWE
# ==========================================

@login_required
def vinyl_list(request):
    """Lista płyt winylowych z wyszukiwaniem i filtrowaniem po gatunkach."""
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'artist')
    selected_genre = request.GET.get('genre', '').strip()
    
    items = VinylRecord.objects.all()

    if query:
        items = items.filter(
            Q(artist__icontains=query) |
            Q(title__icontains=query) |
            Q(label__icontains=query)
        )

    if selected_genre:
        items = items.filter(genre=selected_genre)

    sort_mapping = {
        'artist': 'artist',
        '-artist': '-artist',
        'title': 'title',
        '-title': '-title',
        'release_year': 'release_year',
        '-release_year': '-release_year',
        'condition': 'condition',
        '-condition': '-condition',
    }
    
    if sort_by in sort_mapping:
        items = items.order_by(sort_mapping[sort_by])

    available_genres = VinylRecord.objects.exclude(genre__isnull=True).exclude(genre__exact='').values_list('genre', flat=True).distinct().order_by('genre')
    artist_stats = VinylRecord.objects.values('artist').annotate(count=Count('id')).order_by('-count')[:5]
    genre_stats = VinylRecord.objects.exclude(genre__isnull=True).exclude(genre__exact='').values('genre').annotate(count=Count('id')).order_by('-count')[:5]
    total_count = items.count()

    context = {
        'items': items,
        'artist_stats': artist_stats,
        'genre_stats': genre_stats,
        'total_count': total_count,
        'current_sort': sort_by,
        'available_genres': available_genres,
        'selected_genre': selected_genre,
    }
    return render(request, 'library/vinyl_list.html', context)


@login_required
def vinyl_create(request):
    """Dodawanie nowej płyty winylowej."""
    if request.method == 'POST':
        form = VinylRecordForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Płyta winylowa została pomyślnie dodana!')
            return redirect('vinyl_list')
    else:
        form = VinylRecordForm()
    
    return render(request, 'library/vinyl_form.html', {'form': form, 'is_edit': False})


@login_required
def vinyl_edit(request, pk):
    """Edycja płyty winylowej."""
    item = get_object_or_404(VinylRecord, pk=pk)
    if request.method == 'POST':
        form = VinylRecordForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zaktualizowano dane płyty winylowej.')
            return redirect('vinyl_list')
    else:
        form = VinylRecordForm(instance=item)
    
    return render(request, 'library/vinyl_form.html', {'form': form, 'item': item, 'is_edit': True})


@login_required
def vinyl_delete(request, pk):
    """Usuwanie płyty winylowej."""
    item = get_object_or_404(VinylRecord, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Płyta winylowa została usunięta.')
        return redirect('vinyl_list')
    return redirect('vinyl_list')


# ==========================================
# 3. GRY WIDEO
# ==========================================

@login_required
def video_game_list(request):
    """Lista gier wideo z filtrowaniem po platformie."""
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'title')
    selected_platform = request.GET.get('platform', '').strip()
    
    items = VideoGame.objects.all()

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(genre__icontains=query)
        )

    if selected_platform:
        items = items.filter(platform=selected_platform)

    sort_mapping = {
        'title': 'title', '-title': '-title',
        'platform': 'platform', '-platform': '-platform',
        'release_year': 'release_year', '-release_year': '-release_year',
        'condition': 'condition', '-condition': '-condition',
    }
    
    if sort_by in sort_mapping:
        items = items.order_by(sort_mapping[sort_by])

    available_platforms = VideoGame.objects.exclude(platform__isnull=True).exclude(platform__exact='').values_list('platform', flat=True).distinct().order_by('platform')
    platform_stats = VideoGame.objects.exclude(platform__isnull=True).exclude(platform__exact='').values('platform').annotate(count=Count('id')).order_by('-count')[:5]
    genre_stats = VideoGame.objects.exclude(genre__isnull=True).exclude(genre__exact='').values('genre').annotate(count=Count('id')).order_by('-count')[:5]
    total_count = items.count()

    context = {
        'items': items,
        'platform_stats': platform_stats,
        'genre_stats': genre_stats,
        'total_count': total_count,
        'current_sort': sort_by,
        'available_platforms': available_platforms,
        'selected_platform': selected_platform,
    }
    return render(request, 'library/video_game_list.html', context)


@login_required
def video_game_create(request):
    """Dodawanie nowej gry wideo."""
    if request.method == 'POST':
        form = VideoGameForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gra wideo została dodana do kolekcji!')
            return redirect('video_game_list')
    else:
        form = VideoGameForm()
    
    return render(request, 'library/video_game_form.html', {'form': form, 'is_edit': False})


@login_required
def video_game_edit(request, pk):
    """Edycja gry wideo."""
    item = get_object_or_404(VideoGame, pk=pk)
    if request.method == 'POST':
        form = VideoGameForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zaktualizowano dane gry.')
            return redirect('video_game_list')
    else:
        form = VideoGameForm(instance=item)
    
    return render(request, 'library/video_game_form.html', {'form': form, 'item': item, 'is_edit': True})


@login_required
def video_game_delete(request, pk):
    """Usuwanie gry wideo."""
    item = get_object_or_404(VideoGame, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Gra została usunięta z kolekcji.')
        return redirect('video_game_list')
    return redirect('video_game_list')


# ==========================================
# 4. GRY PLANSZOWE
# ==========================================

@login_required
def board_game_list(request):
    """Lista gier planszowych z filtrowaniem po kategoriach."""
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'title')
    selected_category = request.GET.get('category', '').strip()
    
    items = BoardGame.objects.all()

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(publisher__icontains=query)
        )

    if selected_category:
        items = items.filter(category=selected_category)

    sort_mapping = {
        'title': 'title', '-title': '-title',
        'publisher': 'publisher', '-publisher': '-publisher',
        'release_year': 'release_year', '-release_year': '-release_year',
        'condition': 'condition', '-condition': '-condition',
    }
    
    if sort_by in sort_mapping:
        items = items.order_by(sort_mapping[sort_by])

    available_categories = BoardGame.objects.exclude(category__isnull=True).exclude(category__exact='').values_list('category', flat=True).distinct().order_by('category')
    publisher_stats = BoardGame.objects.exclude(publisher__isnull=True).exclude(publisher__exact='').values('publisher').annotate(count=Count('id')).order_by('-count')[:5]
    category_stats = BoardGame.objects.exclude(category__isnull=True).exclude(category__exact='').values('category').annotate(count=Count('id')).order_by('-count')[:5]
    total_count = items.count()

    context = {
        'items': items,
        'publisher_stats': publisher_stats,
        'category_stats': category_stats,
        'total_count': total_count,
        'current_sort': sort_by,
        'available_categories': available_categories,
        'selected_category': selected_category,
    }
    return render(request, 'library/board_game_list.html', context)


@login_required
def board_game_create(request):
    """Dodawanie nowej gry planszowej."""
    if request.method == 'POST':
        form = BoardGameForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gra planszowa została dodana do kolekcji!')
            return redirect('board_game_list')
    else:
        form = BoardGameForm()
    
    return render(request, 'library/board_game_form.html', {'form': form, 'is_edit': False})


@login_required
def board_game_edit(request, pk):
    """Edycja gry planszowej."""
    item = get_object_or_404(BoardGame, pk=pk)
    if request.method == 'POST':
        form = BoardGameForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zaktualizowano dane gry planszowej.')
            return redirect('board_game_list')
    else:
        form = BoardGameForm(instance=item)
    
    return render(request, 'library/board_game_form.html', {'form': form, 'item': item, 'is_edit': True})


@login_required
def board_game_delete(request, pk):
    """Usuwanie gry planszowej."""
    item = get_object_or_404(BoardGame, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Gra planszowa została usunięta.')
        return redirect('board_game_list')
    return redirect('board_game_list')


# ==========================================
# 5. KSIĄŻKI & SMART ENGINE
# ==========================================

@login_required
def book_list(request):
    """Lista książek z grupowaniem alfabetycznym i stałą listą kategorii."""
    books = Book.objects.all().order_by('title')
    categories_list = [choice[0] for choice in CATEGORY_CHOICES]
    total_count = books.count()
    
    alphabet_groups = {}
    for book in books:
        first_letter = book.title[0].upper() if book.title else '#'
        if first_letter not in alphabet_groups:
            alphabet_groups[first_letter] = []
        alphabet_groups[first_letter].append(book)
    
    grouped_books = [(letter, alphabet_groups[letter]) for letter in sorted(alphabet_groups.keys())]

    context = {
        'grouped_books': grouped_books,
        'total_count': total_count,
        'categories_list': categories_list,
    }
    return render(request, 'library/book_list.html', context)


@login_required
def book_detail(request, pk):
    """Szczegółowe informacje o książce."""
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'library/book_detail.html', {'book': book})


@login_required
def book_create(request):
    """Dodawanie nowej książki z inteligentnym pobieraniem okładki."""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        image_url = request.POST.get('cover_url', '').strip()
        
        if form.is_valid():
            isbn_val = form.cleaned_data.get('isbn')
            
            existing_book = Book.objects.filter(isbn=isbn_val).first() if isbn_val else None
                
            if existing_book:
                existing_book.number_of_copies = (existing_book.number_of_copies or 1) + 1
                existing_book.save()
                messages.success(request, f"Książka '{existing_book.title}' już była w bazie. Zwiększono liczbę egzemplarzy do {existing_book.number_of_copies}!")
                return redirect('book_list')
            else:
                book = form.save()
                
                # Jeśli użytkownik nie wgrał ręcznie pliku, a mamy link do okładki -> pobierz ją
                if image_url and not request.FILES.get('image'):
                    download_and_save_book_cover(book, image_url)
                
                messages.success(request, f"Książka '{book.title}' została pomyślnie dodana!")
                return redirect('book_list')
    else:
        form = BookForm()
        image_url = ''
        
    return render(request, 'library/book_form.html', {'form': form, 'cover_url': image_url})


@login_required
def book_edit(request, pk):
    """Edycja książki z możliwością aktualizacji okładki po linku."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        image_url = request.POST.get('cover_url', '').strip()
        
        if form.is_valid():
            book = form.save()
            
            if image_url and not request.FILES.get('image'):
                download_and_save_book_cover(book, image_url)
            
            messages.success(request, 'Zaktualizowano dane książki.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
        image_url = book.image.url if book.image else ''
    
    return render(request, 'library/book_form.html', {'form': form, 'cover_url': image_url, 'book': book})


@login_required
def book_delete(request, pk):
    """Usuwanie książki."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'Książka „{title}” została pomyślnie usunięta z bazy.')
        return redirect('book_list')
    return redirect('book_detail', pk=pk)


@login_required
def book_import_csv(request):
    """
    Zaawansowany import książek z pliku CSV:
    - Automatycznie wykrywa separator (przecinek, średnik, tabulator).
    - Obsługuje polskie i angielskie nagłówki w dowolnej wielkości liter.
    - Jeśli podano tylko ISBN (lub brakuje autora/opisu), autouzupełnia brakujące dane z Biblioteki Narodowej / Google.
    - Kaskadowo pobiera okładki w jakości HD i zapisuje je w bazie mediów.
    """
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Nie wybrano pliku CSV.')
            return redirect('book_list')
            
        csv_file = request.FILES['csv_file']
        
        try:
            raw_bytes = csv_file.read()
            data_set = raw_bytes.decode('UTF-8', errors='replace')
            
            # 1. Wykrywanie separatora
            sample = data_set[:2048]
            delimiter = ','
            if ';' in sample and sample.count(';') > sample.count(','):
                delimiter = ';'
            elif '\t' in sample and sample.count('\t') > sample.count(','):
                delimiter = '\t'

            io_string = io.StringIO(data_set)
            reader = csv.reader(io_string, delimiter=delimiter)
            
            rows = list(reader)
            if not rows:
                messages.warning(request, "Przesłany plik CSV jest pusty.")
                return redirect('book_list')

            # 2. Mapowanie nagłówków (case-insensitive & polish/english aliases)
            headers = [h.strip().lower() for h in rows[0]]
            
            def get_col_index(*aliases):
                for idx, h in enumerate(headers):
                    if h in aliases or any(alias in h for alias in aliases):
                        return idx
                return None

            col_title = get_col_index('title', 'tytuł', 'tytul', 'nazwa')
            col_authors = get_col_index('authors', 'author', 'autor', 'autorzy', 'twórca', 'tworca')
            col_isbn = get_col_index('isbn', 'kod', 'ean')
            col_publisher = get_col_index('publisher', 'wydawca', 'wydawnictwo')
            col_published_at = get_col_index('published at', 'published_at', 'published', 'rok', 'data wydania', 'rok wydania', 'data')
            col_pages = get_col_index('page count', 'page_count', 'pages', 'strony', 'liczba stron')
            col_categories = get_col_index('categories', 'category', 'kategorie', 'kategoria', 'gatunek')
            col_language = get_col_index('language', 'język', 'jezyk', 'lang')
            col_description = get_col_index('description', 'opis')
            col_read = get_col_index('read', 'przeczytane', 'status', 'czytane')
            col_subtitle = get_col_index('subtitle', 'podtytuł', 'podtytul')

            imported_count = 0
            covers_count = 0

            # 3. Przetwarzanie wierszy
            for row in rows[1:]:
                if not row or not any(row):
                    continue

                def get_val(col_idx):
                    if col_idx is not None and col_idx < len(row):
                        return row[col_idx].strip()
                    return ''

                title = get_val(col_title)
                isbn_val = get_val(col_isbn)
                if '.' in isbn_val:
                    isbn_val = isbn_val.split('.')[0]
                isbn_val = re.sub(r'[^0-9X]', '', isbn_val.upper())

                authors = get_val(col_authors)
                subtitle = get_val(col_subtitle)
                publisher = get_val(col_publisher)
                published_at = get_val(col_published_at)[:10]
                categories = get_val(col_categories)
                language = get_val(col_language)
                description = get_val(col_description)
                
                page_count_str = get_val(col_pages)
                pages = int(float(page_count_str)) if page_count_str and page_count_str.replace('.', '', 1).isdigit() else None
                
                read_raw = get_val(col_read).lower()
                read_status = read_raw in ['1', 'true', 'tak', 'yes', 'przeczytane']

                # Pomiń duplikaty ISBN
                if isbn_val and Book.objects.filter(isbn=isbn_val).exists():
                    continue

                # 4. Jeśli brak tytułu lub danych, a mamy ISBN -> pobierz z API
                api_cover_url = None
                if isbn_val and (not title or not authors or not publisher or not description):
                    api_data = get_unified_book_data(isbn_val)
                    if api_data:
                        if not title:
                            title = api_data.get('title', '')
                        if not authors:
                            authors = api_data.get('authors', '')
                        if not publisher:
                            publisher = api_data.get('publisher', '')
                        if not published_at:
                            published_at = api_data.get('published_at', '')
                        if not pages and api_data.get('page_count'):
                            pages = int(api_data['page_count']) if str(api_data['page_count']).isdigit() else None
                        if not categories:
                            categories = api_data.get('categories', '')
                        if not description:
                            description = api_data.get('description', '')
                        if not language:
                            language = api_data.get('language', 'PL')
                        api_cover_url = api_data.get('cover_url')

                if not title and not isbn_val:
                    continue

                if not title and isbn_val:
                    title = f"Książka ISBN: {isbn_val}"

                book = Book.objects.create(
                    title=title,
                    subtitle=subtitle,
                    authors=authors,
                    publisher=publisher,
                    published_at=published_at,
                    page_count=pages,
                    language=language or 'PL',
                    categories=categories,
                    description=description,
                    isbn=isbn_val if isbn_val else None,
                    number_of_copies=1,
                    read=read_status
                )
                imported_count += 1

                # 5. Kaskadowe poszukiwanie i zapis okładki
                cover_url = api_cover_url or find_best_cover_for_book(
                    isbn=book.isbn,
                    title=book.title,
                    authors=book.authors
                )
                if cover_url:
                    saved = download_and_save_book_cover(book, cover_url)
                    if saved:
                        covers_count += 1

            messages.success(request, f"Sukces! Zaimportowano {imported_count} pozycji (pomyślnie pobrano {covers_count} okładek).")
            return redirect('book_list')
            
        except Exception as e:
            messages.error(request, f"Błąd podczas importu CSV: {e}")
            return redirect('book_list')

    return render(request, 'library/book_import.html')


@login_required
def fetch_book_data(request, isbn):
    """Nowy, zunifikowany endpoint pobierania metadanych i okładek z wielu źródeł."""
    data = get_unified_book_data(isbn)
    if data and (data.get('title') or data.get('cover_url')):
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Nie znaleziono książki w bazach zewnętrznych.'}, status=404)


@login_required
def fix_missing_covers(request):
    """
    Automatycznie skanuje wszystkie książki w bazie bez okładki
    i pobiera je kaskadowo z Open Library CDN, Open Library Search, Google Books Hi-Res oraz Wolnych Lektur.
    """
    books_without_covers = Book.objects.filter(Q(image='') | Q(image__isnull=True))
    fixed_count = 0
    
    for book in books_without_covers:
        cover_url = find_best_cover_for_book(
            isbn=book.isbn, 
            title=book.title, 
            authors=book.authors
        )
        if cover_url:
            saved = download_and_save_book_cover(book, cover_url)
            if saved:
                fixed_count += 1

    messages.success(request, f"Proces zakończony! Zaktualizowano okładki dla {fixed_count} książek.")
    return redirect('book_list')


@login_required
def fix_all_covers(request):
    """Alias do fix_missing_covers."""
    return fix_missing_covers(request)


@login_required
def book_update_progress(request, pk):
    """Aktualizacja liczby przeczytanych stron z poziomu karty szczegółów."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        pages_read_str = request.POST.get('pages_read')
        
        if pages_read_str and pages_read_str.isdigit():
            try:
                pages_read = int(pages_read_str)
                if book.page_count and pages_read > book.page_count:
                    pages_read = book.page_count
                if pages_read < 0:
                    pages_read = 0
                
                book.pages_read = pages_read
                book.read = bool(book.page_count and pages_read >= book.page_count)
                book.save()
                messages.success(request, 'Postęp czytania został zaktualizowany.')
            except ValueError:
                pass
                
    return redirect('book_detail', pk=book.pk)


@login_required
def book_bulk_update(request):
    """Masowa aktualizacja kategorii lub statusu przeczytania dla zaznaczonych książek."""
    if request.method == 'POST':
        selected_ids = request.POST.get('selected_books', '')
        new_category = request.POST.get('new_category', '').strip()
        action_type = request.POST.get('action_type', '')
        
        if not selected_ids:
            messages.warning(request, "Nie wybrano żadnych książek.")
            return redirect('book_list')
            
        id_list = [int(pk) for pk in selected_ids.split(',') if pk.isdigit()]
        books = Book.objects.filter(pk__in=id_list)
        
        if action_type == 'category':
            for book in books:
                if new_category:
                    current_cats = [c.strip() for c in book.categories.split(',')] if book.categories else []
                    if new_category not in current_cats:
                        current_cats.append(new_category)
                        book.categories = ", ".join(current_cats)
                        book.save()
            messages.success(request, f"Pomyślnie zaktualizowano kategorię dla {books.count()} książek!")
            
        elif action_type == 'read_status':
            status_val = request.POST.get('status_val') == 'true'
            books.update(read=status_val)
            messages.success(request, f"Zmieniono status przeczytania dla {books.count()} książek!")
            
    return redirect('book_list')


@login_required
def toggle_book_read(request, pk):
    """Szybka zmiana statusu przeczytania przez AJAX."""
    if request.method == 'POST':
        try:
            book = Book.objects.get(pk=pk)
            book.read = not book.read
            book.save()
            return JsonResponse({'success': True, 'is_read': book.read})
        except Book.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Książka nie istnieje'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
