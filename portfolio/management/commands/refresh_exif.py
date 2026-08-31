from django.core.management.base import BaseCommand
from portfolio.models import Photo


class Command(BaseCommand):
    help = 'Odświeża i wyciąga pełne dane EXIF (przysłona, czas, ogniskowa, ISO, obiektyw, data) dla wszystkich zdjęć w bazie'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Wymusza ponowne odczytanie EXIF i nadpisanie istniejących pól',
        )

    def handle(self, *args, **options):
        force = options['force']
        photos = Photo.objects.all()
        total = photos.count()
        updated_count = 0

        self.stdout.write(self.style.NOTICE(f'Znaleziono {total} zdjęć do analizy...'))

        for photo in photos:
            if not photo.image:
                continue

            if force:
                photo.camera = None
                photo.lens = None
                photo.focal_length = None
                photo.aperture = None
                photo.shutter_speed = None
                photo.iso = None
                photo.taken_at = None

            fields = photo.extract_exif()
            if fields:
                photo.save(update_fields=fields)
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f' [OK] Zdjęcie #{photo.id} "{photo.title or "Bez tytułu"}": '
                    f'{photo.camera or "-"} | {photo.lens or "-"} | {photo.focal_length or "-"} | '
                    f'{photo.aperture or "-"} | {photo.shutter_speed or "-"} | ISO {photo.iso or "-"} | {photo.taken_at or "-"}'
                ))
            else:
                self.stdout.write(f' [Brak zmian] Zdjęcie #{photo.id} "{photo.title or "Bez tytułu"}"')

        self.stdout.write(self.style.SUCCESS(f'\nGotowe! Zaktualizowano dane EXIF dla {updated_count}/{total} zdjęć.'))
