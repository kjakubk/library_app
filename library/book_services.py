import os
import re
import json
import ssl
import urllib.request
import urllib.parse
from django.core.files.base import ContentFile


# ==========================================
# 1. NARZĘDZIA POMOCNICZE ISBN I CZYSZCZENIA DANYCH
# ==========================================

def clean_isbn_string(isbn_raw):
    """Czyści numer ISBN ze znaków specjalnych, spacji i myślników."""
    if not isbn_raw:
        return ''
    cleaned = re.sub(r'[^0-9X]', '', str(isbn_raw).upper().strip())
    return cleaned


def isbn10_to_isbn13(isbn10):
    """Konwertuje 10-cyfrowy ISBN na 13-cyfrowy ISBN."""
    clean = clean_isbn_string(isbn10)
    if len(clean) != 10:
        return None
    
    core = '978' + clean[:9]
    checksum = 0
    for i, digit in enumerate(core):
        weight = 1 if i % 2 == 0 else 3
        checksum += int(digit) * weight
    check_digit = (10 - (checksum % 10)) % 10
    return core + str(check_digit)


def isbn13_to_isbn10(isbn13):
    """Konwertuje 13-cyfrowy ISBN (o prefiksie 978) na 10-cyfrowy ISBN."""
    clean = clean_isbn_string(isbn13)
    if len(clean) != 13 or not clean.startswith('978'):
        return None
    
    core = clean[3:12]
    checksum = sum(int(digit) * (10 - i) for i, digit in enumerate(core))
    remainder = (11 - (checksum % 11)) % 11
    check_char = 'X' if remainder == 10 else str(remainder)
    return core + check_char


def get_all_isbn_variants(isbn_raw):
    """Zwraca listę wszystkich wariantów danego ISBN (oryginał, czysty, ISBN-10, ISBN-13)."""
    clean = clean_isbn_string(isbn_raw)
    variants = []
    if clean:
        variants.append(clean)
        if len(clean) == 10:
            isbn13 = isbn10_to_isbn13(clean)
            if isbn13 and isbn13 not in variants:
                variants.append(isbn13)
        elif len(clean) == 13:
            isbn10 = isbn13_to_isbn10(clean)
            if isbn10 and isbn10 not in variants:
                variants.append(isbn10)
    return variants


def clean_bn_title(title_raw):
    """Czyści tytuł z formatowania katalogowego MARC Biblioteki Narodowej."""
    if not title_raw:
        return ''
    title = title_raw.split(' / ')[0].strip()
    title = title.split(' : ')[0].strip() if ' : ' in title and len(title.split(' : ')[0]) > 3 else title
    title = re.sub(r'[\r\n\t]+', ' ', title).strip()
    return title.rstrip(' :;,.')


def clean_bn_author(author_raw):
    """
    Czyści autora z formatowania katalogowego MARC Biblioteki Narodowej.
    Prawidłowo wyodrębnia głównego autora (np. 'George Orwell', 'Andrzej Sapkowski', 'J. K. Rowling').
    """
    if not author_raw:
        return ''
    
    cleaned = re.sub(r'\(\s*\d{4}\s*-\s*\d*\s*\)', '', author_raw).strip()
    
    for stop_word in ['Dressler', 'Bellona', 'SuperNowa', 'Helion', 'Media Rodzina', 'Znak', 'Rebis', 'Prószyński', 'Wydawnictwo', 'Wydawn.', 'Marginesy', 'Greg', 'Albatros']:
        cleaned = re.sub(rf'\b{stop_word}\b.*', '', cleaned, flags=re.IGNORECASE).strip()
    
    if ',' in cleaned:
        parts = [p.strip() for p in cleaned.split(',') if p.strip()]
        if len(parts) >= 2:
            last_name = parts[0].strip()
            first_part = parts[1].strip()
            words = first_part.split()
            first_names = []
            for w in words:
                if len(w) <= 2 or w.endswith('.') or len(first_names) == 0:
                    first_names.append(w)
                else:
                    break
            first_name_str = " ".join(first_names)
            return f"{first_name_str} {last_name}".strip().rstrip(' .;,')
            
    return cleaned.rstrip(' .;,')


# ==========================================
# 2. KONTEKST SSL I NAGŁÓWKI
# ==========================================

def get_ssl_context():
    """Tworzy bezpieczny kontekst SSL dla zapytań HTTP."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_headers():
    """Zwraca standardowe nagłówki przeglądarki zapobiegające blokadom."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    }


def is_valid_image_url(url, timeout=2):
    """Sprawdza czy URL prowadzi do istniejącego, prawidłowego obrazka (powyżej 800 bajtów)."""
    if not url:
        return False
    try:
        req = urllib.request.Request(url, headers=get_headers())
        ctx = get_ssl_context()
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            if resp.status == 200:
                content_type = resp.headers.get('Content-Type', '').lower()
                content_length = resp.headers.get('Content-Length')
                if 'image' in content_type or 'jpeg' in content_type or 'jpg' in content_type or 'png' in content_type:
                    if content_length and int(content_length) < 800:
                        return False
                    return True
    except Exception:
        pass
    return False


# ==========================================
# 3. KASKADOWE ŹRÓDŁA OKŁADEK
# ==========================================

def find_cover_in_openlibrary_cdn(isbn_variants):
    """Krok 1: Bezpośrednie odpytanie Open Library Cover CDN po numerach ISBN."""
    ctx = get_ssl_context()
    headers = get_headers()
    for isbn in isbn_variants:
        test_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false"
        try:
            req = urllib.request.Request(test_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=2) as resp:
                if resp.status == 200:
                    length = resp.headers.get('Content-Length')
                    if not length or int(length) > 1000:
                        return test_url
        except Exception:
            continue
    return None


def find_cover_in_openlibrary_search(title, authors=None):
    """
    Krok 2: Wielopoziomowe wyszukiwanie w Open Library Search API:
    1) Tytuł + Autor
    2) Sam Tytuł
    """
    if not title:
        return None
    ctx = get_ssl_context()
    headers = get_headers()
    
    clean_title = title.split('/')[0].split(':')[0].strip()
    queries = []
    
    if authors:
        first_author = authors.split(',')[0].strip()
        queries.append(f"title={urllib.parse.quote(clean_title)}&author={urllib.parse.quote(first_author)}")
    
    queries.append(f"title={urllib.parse.quote(clean_title)}")

    for q in queries:
        try:
            url = f"https://openlibrary.org/search.json?{q}&limit=3"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=2.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for doc in data.get('docs', []):
                    cover_id = doc.get('cover_i')
                    if cover_id:
                        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                        if is_valid_image_url(cover_url, timeout=2):
                            return cover_url
        except Exception:
            continue
            
    return None


def get_best_google_cover_url(volume_info):
    """Ekstrahuje najwyższą dostępną jakość okładki z obiektu volumeInfo Google Books."""
    if not volume_info:
        return None
    image_links = volume_info.get('imageLinks', {})
    if not image_links:
        return None
    
    for key in ['extraLarge', 'large', 'medium', 'small', 'thumbnail', 'smallThumbnail']:
        if key in image_links and image_links[key]:
            url = image_links[key]
            url = url.replace('http://', 'https://')
            url = url.replace('&edge=curl', '')
            if 'zoom=1' in url:
                url = url.replace('zoom=1', 'zoom=2')
            return url
    return None


def find_cover_in_google_books(isbn_variants, title=None, authors=None):
    """Krok 3: Przeszukuje Google Books API po numerach ISBN oraz po tytule/autorze."""
    ctx = get_ssl_context()
    headers = get_headers()
    api_key = os.getenv('GOOGLE_BOOKS_API_KEY', '').strip()
    key_param = f"&key={api_key}" if api_key else ""
    
    # 1. Po ISBN
    if isbn_variants:
        isbn = isbn_variants[0]
        query_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&country=PL&maxResults=1{key_param}"
        try:
            req = urllib.request.Request(query_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=2.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('totalItems', 0) > 0 and 'items' in data:
                    v_info = data['items'][0].get('volumeInfo', {})
                    cover = get_best_google_cover_url(v_info)
                    if cover:
                        return cover
        except Exception:
            pass

    # 2. Fallback po tytule i autorze
    if title:
        clean_title = title.split('/')[0].strip()
        search_terms = [f'intitle:"{clean_title}"']
        if authors:
            first_author = authors.split(',')[0].strip()
            search_terms.append(f'inauthor:"{first_author}"')
        query = urllib.parse.quote(' '.join(search_terms))
        query_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&country=PL&maxResults=1{key_param}"
        try:
            req = urllib.request.Request(query_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=2.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for item in data.get('items', []):
                    v_info = item.get('volumeInfo', {})
                    cover = get_best_google_cover_url(v_info)
                    if cover:
                        return cover
        except Exception:
            pass

    return None


def find_cover_in_wolne_lektury(title):
    """Krok 4: Szuka okładek w Wolne Lektury API dla klasyki literatury."""
    if not title:
        return None
    ctx = get_ssl_context()
    headers = get_headers()
    try:
        clean_title = urllib.parse.quote(title.split('/')[0].split(':')[0].strip())
        url = f"https://wolnelektury.pl/api/books/?query={clean_title}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=2.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, list) and len(data) > 0:
                cover_thumb = data[0].get('cover') or data[0].get('cover_thumb')
                if cover_thumb and is_valid_image_url(cover_thumb, timeout=2):
                    return cover_thumb
    except Exception:
        pass
    return None


def find_best_cover_for_book(isbn=None, title=None, authors=None):
    """
    Główny kaskadowy agregator okładek.
    Przeszukuje niezależne źródła (CDN po ISBN -> Open Library Search -> Google Books -> Wolne Lektury).
    """
    isbn_variants = get_all_isbn_variants(isbn) if isbn else []

    # 1. Open Library CDN (po numerach ISBN)
    if isbn_variants:
        ol_cdn = find_cover_in_openlibrary_cdn(isbn_variants)
        if ol_cdn:
            return ol_cdn

    # 2. Open Library Search (po tytule i autorze)
    if title:
        ol_search = find_cover_in_openlibrary_search(title, authors)
        if ol_search:
            return ol_search

    # 3. Google Books Hi-Res
    gb_cover = find_cover_in_google_books(isbn_variants, title=title, authors=authors)
    if gb_cover and is_valid_image_url(gb_cover, timeout=2):
        return gb_cover

    # 4. Wolne Lektury
    if title:
        wl_cover = find_cover_in_wolne_lektury(title)
        if wl_cover:
            return wl_cover

    return None


# ==========================================
# 4. GŁÓWNY AGREGATOR METADANYCH I OKŁADEK
# ==========================================

def get_unified_book_data(isbn_raw):
    """
    Pobiera i scala metadane z Biblioteki Narodowej, Google Books oraz Open Library,
    gwarantując kaskadowe poszukiwanie okładki z wielu źródeł.
    """
    clean_isbn = clean_isbn_string(isbn_raw)
    if not clean_isbn:
        return None

    isbn_variants = get_all_isbn_variants(clean_isbn)
    ctx = get_ssl_context()
    headers = get_headers()

    result = {
        'isbn': clean_isbn,
        'title': '',
        'subtitle': '',
        'authors': '',
        'publisher': '',
        'published_at': '',
        'page_count': '',
        'language': 'PL',
        'categories': '',
        'description': '',
        'cover_url': '',
        'sources_used': []
    }

    # --- KROK 1: BIBLIOTEKA NARODOWA (Polskie metadane najwyższej jakości) ---
    try:
        bn_url = f"https://data.bn.org.pl/api/bibs.json?isbnIssn={clean_isbn}"
        req = urllib.request.Request(bn_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            bn_data = json.loads(resp.read().decode('utf-8'))
            if bn_data.get('bibs'):
                info = bn_data['bibs'][0]
                result['title'] = clean_bn_title(info.get('title', ''))
                result['authors'] = clean_bn_author(info.get('author', ''))
                result['publisher'] = info.get('publisher', '').strip().rstrip(' ,;')
                result['published_at'] = str(info.get('publicationYear', '')).strip()
                result['categories'] = info.get('genre', '').strip()
                if info.get('languageOfPublication'):
                    result['language'] = info.get('languageOfPublication', '').upper()
                result['sources_used'].append('Biblioteka Narodowa')
    except Exception:
        pass

    # --- KROK 2: GOOGLE BOOKS API (Uzupełnienie braków i opisu jeśli potrzeba) ---
    api_key = os.getenv('GOOGLE_BOOKS_API_KEY', '').strip()
    key_param = f"&key={api_key}" if api_key else ""
    
    if not result['title'] or not result['description']:
        try:
            g_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{clean_isbn}&country=PL&maxResults=1{key_param}"
            req = urllib.request.Request(g_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=2.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('totalItems', 0) > 0 and 'items' in data:
                    v_info = data['items'][0].get('volumeInfo', {})
                    if not result['title']:
                        result['title'] = v_info.get('title', '').strip()
                    if not result['subtitle']:
                        result['subtitle'] = v_info.get('subtitle', '').strip()
                    if not result['authors'] and v_info.get('authors'):
                        result['authors'] = ', '.join(v_info['authors'])
                    if not result['publisher']:
                        result['publisher'] = v_info.get('publisher', '').strip()
                    if not result['published_at']:
                        result['published_at'] = v_info.get('publishedDate', '')[:10]
                    if not result['page_count'] and v_info.get('pageCount'):
                        result['page_count'] = v_info['pageCount']
                    if not result['description']:
                        result['description'] = v_info.get('description', '').strip()
                    if not result['categories'] and v_info.get('categories'):
                        result['categories'] = ', '.join(v_info['categories'])
                    if not result['language'] and v_info.get('language'):
                        result['language'] = v_info.get('language', '').upper()

                    result['sources_used'].append('Google Books')
        except Exception:
            pass

    # --- KROK 3: OPEN LIBRARY API (Dalsze uzupełnienie jeśli nadal brak tytułu) ---
    if not result['title']:
        try:
            ol_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=data"
            req = urllib.request.Request(ol_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=2.5) as resp:
                ol_data = json.loads(resp.read().decode('utf-8'))
                key = f"ISBN:{clean_isbn}"
                if key in ol_data:
                    ol_info = ol_data[key]
                    result['title'] = ol_info.get('title', '').strip()
                    result['subtitle'] = ol_info.get('subtitle', '').strip()
                    if ol_info.get('authors'):
                        result['authors'] = ', '.join([a.get('name', '') for a in ol_info['authors']])
                    if ol_info.get('publishers'):
                        result['publisher'] = ', '.join([p.get('name', '') for p in ol_info['publishers']])
                    result['published_at'] = ol_info.get('publish_date', '')[:10]
                    result['page_count'] = ol_info.get('number_of_pages')
                    result['sources_used'].append('Open Library')
        except Exception:
            pass

    # --- KROK 4: KASKADOWE POSZUKIWANIE OKŁADKI ZE WSZYSTKICH ŹRÓDEŁ ---
    best_cover = find_best_cover_for_book(
        isbn=clean_isbn, 
        title=result['title'], 
        authors=result['authors']
    )

    result['cover_url'] = best_cover or ''
    return result


# ==========================================
# 5. BEZPIECZNE POBIERANIE OBRAZKA DO MODELU
# ==========================================

def download_and_save_book_cover(book_instance, image_url):
    """
    Pobiera obraz z podanego URL i zapisuje go w polu image modelu Book.
    Zwraca True w przypadku sukcesu, False w razie błędu.
    """
    if not image_url or not book_instance:
        return False

    if image_url.startswith('http://'):
        image_url = image_url.replace('http://', 'https://', 1)

    ctx = get_ssl_context()
    headers = get_headers()
    try:
        req = urllib.request.Request(image_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
            if response.status == 200:
                data = response.read()
                if len(data) > 800:
                    file_name = f"cover_{book_instance.isbn or book_instance.pk or 'book'}.jpg"
                    book_instance.image.save(file_name, ContentFile(data), save=True)
                    return True
    except Exception as e:
        print(f"Błąd zapisu okładki dla {book_instance}: {e}")

    return False
