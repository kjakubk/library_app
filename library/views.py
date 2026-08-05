import csv
import json
import ssl
import io
import urllib.request
from functools import wraps

from django.db.models import Q, Count
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from itertools import groupby

from .forms import BookForm, CSVImportForm, VinylRecordForm, PorcelainForm
from .models import BoardGame, Book, Porcelain, VideoGame, VinylRecord, CATEGORY_CHOICES





# ==========================================
# 1. AUTORYZACJA I SESJA
# ==========================================

def require_access_code(view_func):
    """Dekorator sprawdzający, czy użytkownik wpisał poprawny kod dostępu do kolekcji."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('has_library_access'):
            return view_func(request, *args, **kwargs)
        else:
            return redirect('library_access')
    return _wrapped_view


def library_access(request):
    """Obsługuje ekran logowania do zabezpieczonej sekcji kolekcji."""
    error_message = None
    if request.method == 'POST':
        code = request.POST.get('access_code')
        if code == 'Dostep2137':
            request.session['has_library_access'] = True
            return redirect('porcelain_list') 
        else:
            error_message = 'Nieprawidłowy kod dostępu. Spróbuj ponownie.'

    return render(request, 'library/access.html', {'error_message': error_message})


def library_logout(request):
    """Wylogowuje użytkownika, czyszcząc sesję dostępu."""
    if 'has_library_access' in request.session:
        del request.session['has_library_access']
    return redirect('home')


# ==========================================
# 2. WIDOKI LIST KOLEKCJI PORCELANA
# ==========================================

@require_access_code
def porcelain_list(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'name')
    selected_style = request.GET.get('style', '')
    selected_signature = request.GET.get('signature', '')
    
    items = Porcelain.objects.all()

    # Wyszukiwanie tekstowe
    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(signature__icontains=query) |
            Q(style__icontains=query)
        )

    # Filtrowanie po stylu
    if selected_style:
        items = items.filter(style=selected_style)

    # Filtrowanie po sygnaturze
    if selected_signature:
        items = items.filter(signature=selected_signature)

    # Sortowanie
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

    # Pobieramy listy unikalnych stylów i sygnatur do rozwijanych list w filtrach
    available_styles = Porcelain.objects.exclude(style__isnull=True).exclude(style__exact='').values_list('style', flat=True).distinct().order_by('style')
    available_signatures = Porcelain.objects.exclude(signature__isnull=True).exclude(signature__exact='').values_list('signature', flat=True).distinct().order_by('signature')

    # Statystyki
    name_stats = Porcelain.objects.values('name').annotate(count=Count('id')).order_by('-count')[:5]
    signature_stats = Porcelain.objects.exclude(signature__isnull=True).exclude(signature__exact='').values('signature').annotate(count=Count('id')).order_by('-count')[:5]
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

def porcelain_create(request):
    if request.method == 'POST':
        form = PorcelainForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pomyślnie dodano nowy element porcelany!')
            return redirect('porcelain_list')
    else:
        form = PorcelainForm()
        
    return render(request, 'library/porcelain_form.html', {'form': form})

def porcelain_edit(request, pk):
    item = get_object_or_404(Porcelain, pk=pk)
    
    # Obsługa natychmiastowego usunięcia wybranego zdjęcia przez przycisk
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
            messages.success(request, 'Zmiany zostały pomyślnie zapisane.')
            return redirect('porcelain_list')
    else:
        form = PorcelainForm(instance=item)
    
    return render(request, 'library/porcelain_form.html', {'form': form})

def porcelain_delete(request, pk):
    item = get_object_or_404(Porcelain, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Element został pomyślnie usunięty z kolekcji.')
        return redirect('porcelain_list')
    
    return render(request, 'library/porcelain_confirm_delete.html', {'item': item})


# ==========================================
# 2. WIDOKI LIST KOLEKCJI PORCELANA
# ==========================================


@require_access_code
def vinyl_list(request):
    """Wyświetla listę płyt winylowych."""
    items = VinylRecord.objects.all()
    return render(request, 'library/vinyl_list.html', {'items': items})


@require_access_code
def video_game_list(request):
    """Wyświetla listę gier wideo."""
    items = VideoGame.objects.all()
    return render(request, 'library/video_game_list.html', {'items': items})


@require_access_code
def board_game_list(request):
    """Wyświetla listę gier planszowych."""
    items = BoardGame.objects.all()
    return render(request, 'library/board_game_list.html', {'items': items})


@require_access_code
def book_list(request):
    """Widok listy książek z obsługą filtrowania, grupowania i stałą listą kategorii."""
    
    # Pobieramy wszystkie książki (lub Twoją dotychczasową logiku querysetu)
    books = Book.objects.all().order_by('title')
    
    # Przygotowujemy stałą listę kategorii do wyboru z przekazanego tuples
    categories_list = [choice[0] for choice in CATEGORY_CHOICES]
    
    # Grupowanie książek (jeśli używasz grupowania alfabetycznego)
    # Poniżej prosty przykład grupowania lub przekazania listy bezpośrednio do szablonu
    total_count = books.count()
    
    # Przykładowe pogrupowanie alfabetyczne po pierwszej literze tytułu (jeśli tak miałeś wcześniej)
    grouped_books = []
    alphabet_groups = {}
    for book in books:
        first_letter = book.title[0].upper() if book.title else '#'
        if first_letter not in alphabet_groups:
            alphabet_groups[first_letter] = []
        alphabet_groups[first_letter].append(book)
    
    for letter in sorted(alphabet_groups.keys()):
        grouped_books.append((letter, alphabet_groups[letter]))

    context = {
        'grouped_books': grouped_books,
        'total_count': total_count,
        'categories_list': categories_list,  # <--- Tutaj przekazujemy Twoją stałą listę kategorii!
    }
    
    return render(request, 'library/book_list.html', context)


def book_detail(request, pk):
    """Wyświetla szczegółowe informacje o wybranej książce."""
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'library/book_detail.html', {'book': book})


# ==========================================
# 3. TWORZENIE I EDYCJA REKORDÓW
# ==========================================

@require_access_code
def vinyl_create(request):
    """Obsługuje dodawanie nowej płyty winylowej."""
    if request.method == 'POST':
        form = VinylRecordForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('vinyl_list')
    else:
        form = VinylRecordForm()
        
    return render(request, 'library/vinyl_form.html', {'form': form})



@require_access_code
def book_create(request):
    """Obsługuje dodawanie nowej książki (zapobiega duplikatom po ISBN, zwiększając liczbę kopii)."""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        image_url = request.POST.get('cover_url', '')
        
        if form.is_valid():
            isbn_val = form.cleaned_data.get('isbn')
            
            # Sprawdzamy, czy książka z tym ISBN już istnieje w bazie
            existing_book = None
            if isbn_val:
                existing_book = Book.objects.filter(isbn=isbn_val).first()
                
            if existing_book:
                # Jeśli istnieje, zwiększamy liczbę kopii zamiast tworzyć duplikat
                existing_book.number_of_copies = (existing_book.number_of_copies or 1) + 1
                existing_book.save()
                messages.success(request, f"Książka '{existing_book.title}' już była w bazie. Zwiększono liczbę kopii do {existing_book.number_of_copies}!")
                return redirect('book_list')
            else:
                book = form.save(commit=False)
                if image_url and not book.image:
                    try:
                        if image_url.startswith('http://'):
                            image_url = image_url.replace('http://', 'https://', 1)
                        ssl_context = ssl._create_unverified_context()
                        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, context=ssl_context) as response:
                            file_name = f"cover_{book.isbn or 'unknown'}.jpg"
                            book.image.save(file_name, ContentFile(response.read()), save=False)
                    except Exception as e:
                        print(f"Błąd pobierania okładki: {e}")
                
                book.save()
                return redirect('book_list')
    else:
        form = BookForm()
        image_url = ''
        
    return render(request, 'library/book_form.html', {'form': form, 'cover_url': image_url})


@require_access_code
def book_edit(request, pk):
    """Obsługuje edycję istniejącej książki."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        image_url = request.POST.get('cover_url', '') # Przechowujemy link przy błędzie
        
        if form.is_valid():
            book = form.save(commit=False)
            
            if image_url and not request.FILES.get('image'):
                try:
                    if image_url.startswith('http://'):
                        image_url = image_url.replace('http://', 'https://', 1)

                    ssl_context = ssl._create_unverified_context()
                    req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, context=ssl_context) as response:
                        file_name = f"cover_{book.isbn or 'unknown'}.jpg"
                        book.image.save(file_name, ContentFile(response.read()), save=False)
                except Exception as e:
                    print(f"Błąd pobierania okładki przy edycji: {e}")
            
            book.save()
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
        image_url = book.image.url if book.image else ''
    
    return render(request, 'library/book_form.html', {'form': form, 'cover_url': image_url})



@require_access_code
def book_edit(request, pk):
    """Obsługuje edycję istniejącej książki."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        image_url = request.POST.get('cover_url', '') # Przechowujemy link przy błędzie
        
        if form.is_valid():
            book = form.save(commit=False)
            
            if image_url and not request.FILES.get('image'):
                try:
                    if image_url.startswith('http://'):
                        image_url = image_url.replace('http://', 'https://', 1)

                    ssl_context = ssl._create_unverified_context()
                    req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, context=ssl_context) as response:
                        file_name = f"cover_{book.isbn or 'unknown'}.jpg"
                        book.image.save(file_name, ContentFile(response.read()), save=False)
                except Exception as e:
                    print(f"Błąd pobierania okładki przy edycji: {e}")
            
            book.save()
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
        image_url = book.image.url if book.image else ''
    
    return render(request, 'library/book_form.html', {'form': form, 'cover_url': image_url})


@require_access_code
def book_import_csv(request):
    """Importuje książki z CSV i pobiera okładki z Open Library oraz Google Books."""
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Nie wybrano pliku.')
            return redirect('book_list')
            
        csv_file = request.FILES['csv_file']
        
        try:
            data_set = csv_file.read().decode('UTF-8', errors='replace')
            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)
            
            imported_count = 0
            
            for row in reader:
                title = row.get('Title', '').strip()
                if not title:
                    continue
                
                isbn_val = str(row.get('ISBN', '')).strip()
                if '.' in isbn_val:
                    isbn_val = isbn_val.split('.')[0]

                if isbn_val and Book.objects.filter(isbn=isbn_val).exists():
                    continue

                page_count_str = row.get('Page Count', '')
                pages = int(float(page_count_str)) if page_count_str and str(page_count_str).replace('.','',1).isdigit() else None
                read_status = str(row.get('Read', '0')).strip() == '1'

                book = Book.objects.create(
                    title=title,
                    subtitle=row.get('Subtitle', '').strip() if row.get('Subtitle') else '',
                    authors=row.get('Authors', '').strip() if row.get('Authors') else '',
                    publisher=row.get('Publisher', '').strip() if row.get('Publisher') else '',
                    published_at=str(row.get('Published At', ''))[:10],
                    page_count=pages,
                    language=row.get('Language', '').strip() if row.get('Language') else '',
                    categories=row.get('Categories', '').strip() if row.get('Categories') else '',
                    description=row.get('Description', '').strip() if row.get('Description') else '',
                    isbn=isbn_val if isbn_val else None,
                    number_of_copies=1,
                    read=read_status
                )
                imported_count += 1
                
                # --- POBIERANIE OKŁADKI (Open Library -> Fallback do Google Books) ---
                if book.isbn:
                    cover_downloaded = False
                    ssl_context = ssl._create_unverified_context()
                    
                    # 1. Próba z Open Library
                    try:
                        api_url = f"https://openlibrary.org/isbn/{book.isbn}.json"
                        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, context=ssl_context, timeout=3) as response:
                            api_data = json.loads(response.read().decode('utf-8'))
                            cover_id = api_data.get('covers')
                            if cover_id:
                                image_url = f"https://covers.openlibrary.org/b/id/{cover_id[0]}-L.jpg"
                                img_req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                                with urllib.request.urlopen(img_req, context=ssl_context, timeout=3) as img_resp:
                                    file_name = f"cover_{book.isbn}.jpg"
                                    book.image.save(file_name, ContentFile(img_resp.read()), save=True)
                                    cover_downloaded = True
                    except Exception:
                        pass

                    # 2. Jeśli Open Library nie dała rady, próbujemy z Google Books API
                    if not cover_downloaded:
                        try:
                            g_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{book.isbn}"
                            req = urllib.request.Request(g_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, context=ssl_context, timeout=3) as response:
                                g_data = json.loads(response.read().decode('utf-8'))
                                items = g_data.get('items')
                                if items:
                                    volume_info = items[0].get('volumeInfo', {})
                                    image_links = volume_info.get('imageLinks', {})
                                    # Pobieramy największą dostępną okładkę i zmieniamy http na https
                                    thumb_url = image_links.get('large') or image_links.get('medium') or image_links.get('thumbnail')
                                    if thumb_url:
                                        thumb_url = thumb_url.replace('http://', 'https://').replace('&edge=curl', '')
                                        img_req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
                                        with urllib.request.urlopen(img_req, context=ssl_context, timeout=3) as img_resp:
                                            file_name = f"cover_{book.isbn}.jpg"
                                            book.image.save(file_name, ContentFile(img_resp.read()), save=True)
                        except Exception:
                            pass

            messages.success(request, f"Sukces! Zaimportowano {imported_count} książek.")
            return redirect('book_list')
            
        except Exception as e:
            raise Exception(f"BŁĄD PODCZAS IMPORTU CSV: {e}")

    return render(request, 'library/book_import.html')



# ==========================================
# 4. INTEGRACJA Z ZEWNĘTRZNYMI API (ISBN)
# ==========================================

def fetch_book_data(request, isbn):
    """Przeszukuje zewnętrzne bazy (Google Books, Biblioteka Narodowa, Open Library) po kodzie ISBN."""
    clean_isbn = isbn.replace('-', '').strip()
    ssl_context = ssl._create_unverified_context()

    # 1. Próba: Google Books (Ścisłe wyszukiwanie)
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean_isbn}"
        with urllib.request.urlopen(url, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('totalItems', 0) > 0:
                book = data['items'][0]['volumeInfo']
                image_url = book.get('imageLinks', {}).get('thumbnail', '').replace('http://', 'https://')
                
                return JsonResponse({
                    'source': 'Google',
                    'title': book.get('title', ''),
                    'subtitle': book.get('subtitle', ''),
                    'author': ', '.join(book.get('authors', [])),
                    'publisher': book.get('publisher', ''),
                    'published_at': book.get('publishedDate', ''),
                    'page_count': book.get('pageCount', ''),
                    'language': book.get('language', '').upper(),
                    'categories': ', '.join(book.get('categories', [])),
                    'description': book.get('description', ''),
                    'cover_url': image_url
                })
    except Exception as e:
        print(f"Błąd Google Strict: {e}")

    # 2. Próba: Google Books (Wyszukiwanie ogólne)
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q={clean_isbn}"
        with urllib.request.urlopen(url, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('totalItems', 0) > 0:
                book = data['items'][0]['volumeInfo']
                image_url = book.get('imageLinks', {}).get('thumbnail', '').replace('http://', 'https://')
                
                return JsonResponse({
                    'source': 'Google',
                    'title': book.get('title', ''),
                    'subtitle': book.get('subtitle', ''),
                    'author': ', '.join(book.get('authors', [])),
                    'publisher': book.get('publisher', ''),
                    'published_at': book.get('publishedDate', ''),
                    'page_count': book.get('pageCount', ''),
                    'language': book.get('language', '').upper(),
                    'categories': ', '.join(book.get('categories', [])),
                    'description': book.get('description', ''),
                    'cover_url': image_url
                })
    except Exception as e:
        print(f"Błąd Google Broad: {e}")

    # 3. Próba: Biblioteka Narodowa (Z MYŚLNIKAMI)
    try:
        url = f"https://data.bn.org.pl/api/bibs.json?isbnIssn={isbn}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ssl_context) as response:
            bn_data = json.loads(response.read().decode('utf-8'))
            if bn_data.get('bibs'):
                book_info = bn_data['bibs'][0]
                return JsonResponse({
                    'source': 'BN (z myślnikami)',
                    'title': book_info.get('title', ''),
                    'author': book_info.get('author', ''),
                    'publisher': book_info.get('publisher', ''),
                    'published_at': book_info.get('publicationYear', ''),
                    'language': book_info.get('languageOfPublication', ''),
                    'categories': book_info.get('genre', '')
                })
    except Exception as e:
        print(f"Błąd BN (z myślnikami): {e}")

    # 4. Próba: Biblioteka Narodowa (BEZ MYŚLNIKÓW)
    try:
        url = f"https://data.bn.org.pl/api/bibs.json?isbnIssn={clean_isbn}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ssl_context) as response:
            bn_data = json.loads(response.read().decode('utf-8'))
            if bn_data.get('bibs'):
                book_info = bn_data['bibs'][0]
                return JsonResponse({
                    'source': 'BN (bez myślników)',
                    'title': book_info.get('title', ''),
                    'author': book_info.get('author', ''),
                    'publisher': book_info.get('publisher', ''),
                    'published_at': book_info.get('publicationYear', ''),
                    'language': book_info.get('languageOfPublication', ''),
                    'categories': book_info.get('genre', '')
                })
    except Exception as e:
        print(f"Błąd BN (bez myślników): {e}")

    # 5. Próba: Open Library
    try:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=data"
        with urllib.request.urlopen(url, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            key = f"ISBN:{clean_isbn}"
            if key in data:
                book = data[key]
                authors = [a.get('name', '') for a in book.get('authors', [])]
                publishers = [p.get('name', '') for p in book.get('publishers', [])]
                subjects = [s.get('name', '') for s in book.get('subjects', [])]
                
                cover_data = book.get('cover', {})
                cover_url = cover_data.get('large', cover_data.get('medium', ''))
                
                return JsonResponse({
                    'source': 'Open Library',
                    'title': book.get('title', ''),
                    'subtitle': book.get('subtitle', ''),
                    'author': ', '.join(authors),
                    'publisher': ', '.join(publishers),
                    'published_at': book.get('publish_date', ''),
                    'page_count': book.get('number_of_pages', ''),
                    'categories': ', '.join(subjects),
                    'cover_url': cover_url
                })
    except Exception as e:
        print(f"Błąd Open Library: {e}")

    # Jeśli wszystkie bazy zawiodą
    return JsonResponse({'error': 'Nie znaleziono książki.'}, status=404)



#PROGRES W CZYTANIU KSIAŻKI 
@require_access_code
def book_update_progress(request, pk):
    """Szybko aktualizuje liczbę przeczytanych stron bezpośrednio z widoku szczegółów."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        pages_read_str = request.POST.get('pages_read')
        
        # Poprawiona walidacja
        if pages_read_str and pages_read_str.isdigit():
            try:
                pages_read = int(pages_read_str)
                # Zabezpieczenie przed wpisaniem większej liczby stron niż książka posiada
                if book.page_count and pages_read > book.page_count:
                    pages_read = book.page_count
                if pages_read < 0:
                    pages_read = 0
                
                book.pages_read = pages_read
                # Jeśli użytkownik przeczyta całość, automatycznie zaznaczamy flagę przeczytania
                if book.page_count and pages_read >= book.page_count:
                    book.read = True
                else:
                    book.read = False
                    
                book.save()
            except ValueError:
                pass
                
    return redirect('book_detail', pk=book.pk)

@require_access_code
def fix_missing_covers(request):
    """Przechodzi przez wszystkie książki bez okładki i próbuje je pobrać z internetu po ISBN."""
    books_without_covers = Book.objects.filter(image='') | Book.objects.filter(image__isnull=True)
    fixed_count = 0
    
    for book in books_without_covers:
        if not book.isbn:
            continue
            
        # Przykładowe zapytanie do Open Library lub Google Books po ISBN
        api_url = f"https://openlibrary.org/isbn/{book.isbn.strip()}.json"
        try:
            ssl_context = ssl._create_unverified_context()
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, context=ssl_context) as response:
                import json
                data = json.loads(response.read().decode('utf-8'))
                cover_id = data.get('covers')
                if cover_id:
                    image_url = f"https://covers.openlibrary.org/b/id/{cover_id[0]}-L.jpg"
                    
                    img_req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(img_req, context=ssl_context) as img_resp:
                        file_name = f"cover_{book.isbn}.jpg"
                        book.image.save(file_name, ContentFile(img_resp.read()), save=True)
                        fixed_count += 1
        except Exception as e:
            print(f"Nie udało się pobrać okładki dla {book.title}: {e}")
            
    return HttpResponse(f"Naprawiono okładki dla {fixed_count} książek!")

def fix_all_covers(request):
    """Przeszukuje wszystkie książki bez okładki i pobiera je z Google Books / Open Library."""
    books_without_cover = Book.objects.filter(image='') | Book.objects.filter(image__isnull=True)
    fixed = 0
    ssl_context = ssl._create_unverified_context()

    for book in books_without_cover:
        if not book.isbn:
            continue
            
        # Próba Google Books
        try:
            g_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{book.isbn}"
            req = urllib.request.Request(g_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ssl_context, timeout=3) as response:
                g_data = json.loads(response.read().decode('utf-8'))
                items = g_data.get('items')
                if items:
                    image_links = items[0].get('volumeInfo', {}).get('imageLinks', {})
                    thumb_url = image_links.get('large') or image_links.get('medium') or image_links.get('thumbnail')
                    if thumb_url:
                        thumb_url = thumb_url.replace('http://', 'https://').replace('&edge=curl', '')
                        img_req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, context=ssl_context, timeout=3) as img_resp:
                            file_name = f"cover_{book.isbn}.jpg"
                            book.image.save(file_name, ContentFile(img_resp.read()), save=True)
                            fixed += 1
                            continue
        except Exception:
            pass

    return HttpResponse(f"Zaktualizowano okładki dla {fixed} książek! Możesz wrócić do listy.")

@require_access_code
def book_bulk_update(request):
    """Masowo aktualizuje kategorię lub status dla zaznaczonych książek."""
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


@require_access_code
def toggle_book_read(request, pk):
    """Szybka zmiana statusu przeczytania przez suwak (AJAX)."""
    if request.method == 'POST':
        try:
            book = Book.objects.get(pk=pk)
            book.read = not book.read  # Odwracamy status
            book.save()
            return JsonResponse({'success': True, 'is_read': book.read})
        except Book.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Książka nie istnieje'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)