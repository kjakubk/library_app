from django.db import models
from PIL import Image
from PIL.ExifTags import TAGS


class Album(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa albumu (Kategoria)")
    description = models.TextField(blank=True, null=True, verbose_name="Krótki opis")
    cover_photo = models.ForeignKey(
        'Photo',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cover_for_albums',
        verbose_name="Zdjęcie okładki"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")

    class Meta:
        verbose_name = "Album"
        verbose_name_plural = "Albumy"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def photo_count(self):
        return self.photos.count()

    @property
    def cover_url(self):
        if self.cover_photo and self.cover_photo.image:
            return self.cover_photo.image.url
        first = self.photos.order_by('sort_order', '-uploaded_at').first()
        return first.image.url if first and first.image else None


class Photo(models.Model):
    album = models.ForeignKey(
        Album,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        verbose_name="Album"
    )
    image = models.ImageField(upload_to='portfolio/photos/', verbose_name="Zdjęcie")
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name="Tytuł / Podpis")
    description = models.TextField(blank=True, null=True, verbose_name="Opis / Historia zdjęcia")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Miejsce wykonania")
    taken_at = models.DateField(blank=True, null=True, verbose_name="Data wykonania")
    tags = models.CharField(max_length=300, blank=True, null=True, verbose_name="Tagi (oddzielone przecinkami)")
    is_featured = models.BooleanField(default=False, verbose_name="Wyróżnione (na stronie głównej)")
    sort_order = models.IntegerField(default=0, verbose_name="Kolejność w albumie")

    # Parametry EXIF (uzupełniane automatycznie)
    camera = models.CharField(max_length=100, blank=True, null=True, verbose_name="Aparat")
    lens = models.CharField(max_length=150, blank=True, null=True, verbose_name="Obiektyw")
    focal_length = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ogniskowa")
    aperture = models.CharField(max_length=50, blank=True, null=True, verbose_name="Przysłona")
    shutter_speed = models.CharField(max_length=50, blank=True, null=True, verbose_name="Czas naświetlania")
    iso = models.CharField(max_length=50, blank=True, null=True, verbose_name="ISO")

    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Zdjęcie"
        verbose_name_plural = "Zdjęcia"
        ordering = ['sort_order', '-uploaded_at']
        indexes = [
            models.Index(fields=['album', 'sort_order', '-uploaded_at']),
            models.Index(fields=['-uploaded_at']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return self.title if self.title else f"Zdjęcie #{self.id}"

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def extract_exif(self):
        """Pełna ekstrakcja metadanych EXIF z pliku zdjęcia (IFD0 + Exif Sub-IFD + _getexif)."""
        if not self.image:
            return

        try:
            from fractions import Fraction
            from datetime import datetime as dt
            from PIL import Image, ExifTags

            img = Image.open(self.image.path)
            raw_tags = {}

            # 1. Główny IFD (Make, Model itp.)
            exif = img.getexif()
            if exif:
                for k, v in exif.items():
                    raw_tags[ExifTags.TAGS.get(k, k)] = v

                # 2. Exif Sub-IFD (0x8769 - Ogniskowa, Przysłona, ISO, Czas, Obiektyw)
                try:
                    if hasattr(ExifTags, 'IFD') and hasattr(ExifTags.IFD, 'Exif'):
                        sub = exif.get_ifd(ExifTags.IFD.Exif)
                    else:
                        sub = exif.get_ifd(0x8769)
                    if sub:
                        for k, v in sub.items():
                            raw_tags[ExifTags.TAGS.get(k, k)] = v
                except Exception:
                    pass

            # 3. Fallback do _getexif() jeśli dostępny
            if hasattr(img, '_getexif') and callable(img._getexif):
                g = img._getexif()
                if g:
                    for k, v in g.items():
                        tag_name = ExifTags.TAGS.get(k, k)
                        if tag_name not in raw_tags:
                            raw_tags[tag_name] = v

            update_fields = []

            # Aparat
            if not self.camera:
                model = str(raw_tags.get('Model') or '').strip()
                make = str(raw_tags.get('Make') or '').strip()
                if model:
                    if make and make.lower() not in model.lower():
                        self.camera = f"{make} {model}".strip()
                    else:
                        self.camera = model
                    update_fields.append('camera')

            # Obiektyw
            if not self.lens:
                lens = raw_tags.get('LensModel') or raw_tags.get('LensSpecification') or raw_tags.get('Lens')
                if lens:
                    self.lens = str(lens).strip()
                    update_fields.append('lens')

            # ISO
            if not self.iso:
                iso_val = raw_tags.get('ISOSpeedRatings') or raw_tags.get('PhotographicSensitivity') or raw_tags.get('ISO')
                if iso_val is not None:
                    if isinstance(iso_val, (list, tuple)) and len(iso_val) > 0:
                        self.iso = str(iso_val[0])
                    else:
                        self.iso = str(iso_val)
                    update_fields.append('iso')

            # Ogniskowa
            if not self.focal_length:
                focal = raw_tags.get('FocalLength')
                if focal is not None:
                    try:
                        val = float(focal)
                        self.focal_length = f"{int(val)}mm" if val.is_integer() else f"{val:.1f}mm"
                    except Exception:
                        self.focal_length = str(focal)
                    update_fields.append('focal_length')

            # Przysłona
            if not self.aperture:
                fnum = raw_tags.get('FNumber') or raw_tags.get('ApertureValue')
                if fnum is not None:
                    try:
                        val = float(fnum)
                        self.aperture = f"f/{val:.1f}".rstrip('0').rstrip('.') if val == int(val) else f"f/{val:.1f}"
                    except Exception:
                        self.aperture = str(fnum)
                    update_fields.append('aperture')

            # Czas naświetlania
            if not self.shutter_speed:
                exp = raw_tags.get('ExposureTime') or raw_tags.get('ShutterSpeedValue')
                if exp is not None:
                    try:
                        val = float(exp)
                        if 0 < val < 1.0:
                            frac = Fraction(val).limit_denominator(10000)
                            self.shutter_speed = f"1/{frac.denominator}s"
                        else:
                            self.shutter_speed = f"{int(val)}s" if val.is_integer() else f"{val:.1f}s"
                    except Exception:
                        self.shutter_speed = str(exp)
                    update_fields.append('shutter_speed')

            # Data wykonania
            if not self.taken_at:
                dt_str = raw_tags.get('DateTimeOriginal') or raw_tags.get('DateTimeDigitized') or raw_tags.get('DateTime')
                if dt_str:
                    for fmt in ('%Y:%m:%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y:%m:%d', '%Y-%m-%d'):
                        try:
                            self.taken_at = dt.strptime(str(dt_str).strip(), fmt).date()
                            update_fields.append('taken_at')
                            break
                        except Exception:
                            pass

            return update_fields
        except Exception:
            return []

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Jeśli brakuje kluczowych pól EXIF, wyciągnij je z pliku
        if self.image and (not self.camera or not self.iso or not self.focal_length or not self.aperture or not self.shutter_speed):
            update_fields = self.extract_exif()
            if update_fields:
                super().save(update_fields=update_fields)


class Experience(models.Model):
    job_title = models.CharField(max_length=150, verbose_name="Stanowisko")
    company = models.CharField(max_length=150, verbose_name="Firma / Organizacja")
    location = models.CharField(max_length=100, blank=True, default="", verbose_name="Lokalizacja / Tryb")
    start_date = models.DateField(null=True, blank=True, verbose_name="Data rozpoczęcia")
    end_date = models.DateField(null=True, blank=True, verbose_name="Data zakończenia")
    is_current = models.BooleanField(default=False, verbose_name="Aktualne stanowisko")
    description = models.TextField(verbose_name="Opis obowiązków i osiągnięć")
    order = models.IntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        verbose_name = "Doświadczenie zawodowe"
        verbose_name_plural = "Doświadczenia zawodowe"
        ordering = ['-is_current', '-start_date', '-id']

    def __str__(self):
        return f"{self.job_title} w {self.company}"


class CVProfile(models.Model):
    full_name = models.CharField(max_length=150, default="Jakub", verbose_name="Imię i nazwisko")
    title = models.CharField(max_length=150, default="Specjalista ds. Danych / Programista", verbose_name="Tytuł zawodowy")
    summary = models.TextField(blank=True, default="Pasjonat technologii, automatyzacji procesów i analizy danych z wieloletnim doświadczeniem w tworzeniu dedykowanych systemów i zarządzaniu bazami danych.", verbose_name="Podsumowanie zawodowe (Bio)")
    email = models.CharField(max_length=100, blank=True, default="", verbose_name="Email")
    phone = models.CharField(max_length=50, blank=True, default="", verbose_name="Telefon")
    location = models.CharField(max_length=100, blank=True, default="Polska", verbose_name="Lokalizacja")
    linkedin = models.CharField(max_length=200, blank=True, default="", verbose_name="LinkedIn URL")
    github = models.CharField(max_length=200, blank=True, default="", verbose_name="GitHub URL")
    website = models.CharField(max_length=200, blank=True, default="", verbose_name="Strona WWW")
    avatar = models.ImageField(upload_to='portfolio/avatars/', blank=True, null=True, verbose_name="Zdjęcie profilowe")

    class Meta:
        verbose_name = "Profil CV"
        verbose_name_plural = "Profile CV"

    def __str__(self):
        return self.full_name


class Education(models.Model):
    school = models.CharField(max_length=200, verbose_name="Uczelnia / Szkoła")
    degree = models.CharField(max_length=150, verbose_name="Tytuł / Stopień")
    field_of_study = models.CharField(max_length=150, verbose_name="Kierunek / Specjalizacja")
    years = models.CharField(max_length=50, verbose_name="Lata nauki (np. 2019 - 2023)")
    description = models.TextField(blank=True, default="", verbose_name="Opis / Osiągnięcia")
    order = models.IntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        verbose_name = "Edukacja"
        verbose_name_plural = "Edukacja"
        ordering = ['order', '-id']

    def __str__(self):
        return f"{self.degree} - {self.school}"


class Skill(models.Model):
    category = models.CharField(max_length=100, default="Umiejętności techniczne", verbose_name="Kategoria")
    name = models.CharField(max_length=100, verbose_name="Umiejętność / Narzędzie")
    level = models.IntegerField(default=5, verbose_name="Poziom (1-5)")
    order = models.IntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        verbose_name = "Umiejętność"
        verbose_name_plural = "Umiejętności"
        ordering = ['order', 'category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"


class Language(models.Model):
    name = models.CharField(max_length=100, verbose_name="Język")
    level = models.CharField(max_length=100, default="B2", verbose_name="Poziom biegłości")
    order = models.IntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        verbose_name = "Język obcy"
        verbose_name_plural = "Języki obce"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.level}"


class Certificate(models.Model):
    title = models.CharField(max_length=200, verbose_name="Nazwa certyfikatu / Kursu")
    issuer = models.CharField(max_length=150, verbose_name="Wydawca / Organizacja")
    year = models.CharField(max_length=50, verbose_name="Data / Rok")
    order = models.IntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        verbose_name = "Certyfikat"
        verbose_name_plural = "Certyfikaty"
        ordering = ['order', '-id']

    def __str__(self):
        return self.title


class Project(models.Model):
    title = models.CharField(max_length=200, verbose_name="Nazwa projektu")
    role = models.CharField(max_length=150, blank=True, default="", verbose_name="Rola / Stanowisko w projekcie")
    technologies = models.CharField(max_length=255, blank=True, default="", verbose_name="Technologie (po przecinku)")
    url = models.CharField(max_length=255, blank=True, default="", verbose_name="Link do projektu / GitHub")
    description = models.TextField(blank=True, default="", verbose_name="Opis projektu i osiągniętych rezultatów")
    order = models.IntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        verbose_name = "Projekt"
        verbose_name_plural = "Projekty"
        ordering = ['order', '-id']

    def __str__(self):
        return self.title


class Hobby(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nazwa hobby / Zainteresowania")
    icon = models.CharField(max_length=50, blank=True, default="🎮", verbose_name="Ikona / Emoji")
    order = models.IntegerField(default=0, verbose_name="Kolejność")

    class Meta:
        verbose_name = "Hobby"
        verbose_name_plural = "Hobby i Zainteresowania"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name