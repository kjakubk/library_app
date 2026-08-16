import csv
import io
import re
from .models import Book
from .book_services import get_unified_book_data, download_and_save_book_cover, find_best_cover_for_book

def process_csv_import(csv_file):
    """
    Parsuje i importuje książki z pliku CSV.
    Zwraca krotkę: (imported_count, covers_count, error_message)
    """
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
            return 0, 0, "Przesłany plik CSV jest pusty."

        # 2. Mapowanie nagłówków
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
        col_bookshelf = get_col_index('bookshelf', 'półka', 'polka', 'regał', 'regal')
        col_tags = get_col_index('tags', 'tagi')
        col_wishlist = get_col_index('wishlist', 'lista życzeń', 'lista zyczen')
        col_pages_read = get_col_index('pages read', 'pages_read', 'przeczytane strony')
        col_rating = get_col_index('my rating', 'my_rating', 'rating', 'ocena')
        col_signed = get_col_index('signed', 'autograf', 'podpisana')
        col_condition = get_col_index('condition', 'stan')
        col_copies = get_col_index('number of copies', 'copies', 'liczba egzemplarzy', 'kopie')
        col_format = get_col_index('format', 'oprawa', 'typ oprawy')
        col_edition = get_col_index('edition', 'wydanie')
        col_series = get_col_index('series', 'seria', 'cykl')
        col_volume = get_col_index('volume', 'tom')
        col_translators = get_col_index('translators', 'translator', 'tłumacze', 'tlumacze', 'tłumacz', 'tlumacz')
        col_illustrators = get_col_index('illustrators', 'illustrator', 'ilustratorzy', 'ilustrator')
        col_editors = get_col_index('editors', 'editor', 'redaktorzy', 'redaktor')
        col_narrators = get_col_index('narrators', 'narrator', 'lektorzy', 'lektor')
        col_photographers = get_col_index('photographers', 'fotografowie')

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

            bookshelf = get_val(col_bookshelf)
            tags = get_val(col_tags)
            wishlist_raw = get_val(col_wishlist).lower()
            wishlist = wishlist_raw in ['1', 'true', 'tak', 'yes']

            pages_read_str = get_val(col_pages_read)
            pages_read = int(float(pages_read_str)) if pages_read_str and pages_read_str.replace('.', '', 1).isdigit() else 0

            rating_str = get_val(col_rating)
            my_rating = int(float(rating_str)) if rating_str and rating_str.replace('.', '', 1).isdigit() else None

            signed_raw = get_val(col_signed).lower()
            signed = signed_raw in ['1', 'true', 'tak', 'yes']

            condition = get_val(col_condition)
            
            copies_str = get_val(col_copies)
            number_of_copies = int(float(copies_str)) if copies_str and copies_str.replace('.', '', 1).isdigit() else 1

            format_val = get_val(col_format)
            edition = get_val(col_edition)
            series = get_val(col_series)
            volume = get_val(col_volume)
            translators = get_val(col_translators)
            illustrators = get_val(col_illustrators)
            editors = get_val(col_editors)
            narrators = get_val(col_narrators)
            photographers = get_val(col_photographers)

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
                bookshelf=bookshelf,
                tags=tags,
                wishlist=wishlist,
                read=read_status,
                pages_read=pages_read,
                my_rating=my_rating,
                signed=signed,
                condition=condition,
                number_of_copies=number_of_copies,
                format=format_val,
                edition=edition,
                series=series,
                volume=volume,
                translators=translators,
                illustrators=illustrators,
                editors=editors,
                narrators=narrators,
                photographers=photographers
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
                    
        return imported_count, covers_count, None
    except Exception as e:
        return 0, 0, str(e)
