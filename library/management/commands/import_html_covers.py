import base64
import re
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from library.models import Book

class Command(BaseCommand):
    help = 'Imports book covers from an HTML file containing base64 images'

    def add_arguments(self, parser):
        parser.add_argument('html_file', type=str, help='Path to the HTML file')

    def handle(self, *args, **kwargs):
        html_file = kwargs['html_file']

        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File "{html_file}" not found.'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading file: {e}'))
            return

        books_updated = 0
        books_not_found = 0
        missing_data = 0
        parse_errors = 0

        images = soup.find_all('img', class_='book-image')
        
        self.stdout.write(f'Found {len(images)} images in HTML. Processing...')

        for img in images:
            container = img.find_parent('table')
            if not container:
                container = img.find_parent('li')
                
            if not container:
                self.stdout.write(self.style.WARNING("Skipped an image because no container (table/li) was found."))
                parse_errors += 1
                continue

            isbn_span = container.find('span', {'title': re.compile(r'isbn', re.IGNORECASE)})
            
            if not isbn_span:
                self.stdout.write(self.style.WARNING("Skipped an image because no ISBN span was found in its container."))
                parse_errors += 1
                continue
                
            # Extract text safely
            parent = isbn_span.find_parent('div') or isbn_span.find_parent()
            isbn_raw = parent.get_text(strip=True)
            
            if not isbn_raw:
                next_el = isbn_span.find_next()
                if next_el:
                    isbn_raw = next_el.get_text(strip=True)

            isbn = re.sub(r'[^0-9X-]', '', isbn_raw, flags=re.IGNORECASE)
            
            if not isbn or len(isbn) < 10:
                self.stdout.write(self.style.WARNING(f"Skipped an image because extracted ISBN is invalid: '{isbn_raw}'"))
                parse_errors += 1
                continue

            src = img.get('src', '')
            if not src.startswith('data:image'):
                self.stdout.write(self.style.WARNING(f"Skipped ISBN {isbn} because image src doesn't start with 'data:image'"))
                missing_data += 1
                continue

            match = re.search(r'base64,\s*(.+)', src)
            if not match:
                self.stdout.write(self.style.WARNING(f"Skipped ISBN {isbn} because no base64 data was found in src"))
                missing_data += 1
                continue
                
            b64_data = match.group(1).strip()
            
            try:
                image_data = base64.b64decode(b64_data)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Failed to decode base64 for ISBN {isbn}: {e}'))
                missing_data += 1
                continue
                
            try:
                # Find book. Try direct match first.
                book = Book.objects.filter(isbn=isbn).first()
                if not book:
                    # Try to strip hyphens in DB as well, just in case
                    isbn_no_hyphen = isbn.replace('-', '')
                    book = Book.objects.filter(isbn__iregex=f'^{isbn_no_hyphen}$|^{isbn}$').first()
                    
                if not book:
                    books_not_found += 1
                    self.stdout.write(self.style.WARNING(f'Book with ISBN {isbn} not found in database.'))
                    continue
                
                filename = f"{isbn}_cover.jpg"
                book.image.save(filename, ContentFile(image_data), save=True)
                books_updated += 1
                self.stdout.write(self.style.SUCCESS(f'Updated cover for: {book.title} (ISBN: {isbn})'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating book {isbn}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nFinished importing covers!'))
        self.stdout.write(self.style.SUCCESS(f'Books updated: {books_updated}'))
        self.stdout.write(self.style.WARNING(f'Books not found in DB: {books_not_found}'))
        self.stdout.write(self.style.WARNING(f'Entries with missing/invalid image data: {missing_data}'))
        self.stdout.write(self.style.WARNING(f'Entries with parse errors (e.g. no ISBN found): {parse_errors}'))
