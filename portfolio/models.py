from django.db import models
from PIL import Image
from PIL.ExifTags import TAGS


class Album(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa albumu (Kategoria)")
    description = models.TextField(blank=True, null=True, verbose_name="Krótki opis")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")

    class Meta:
        verbose_name = "Album"
        verbose_name_plural = "Albumy"
        ordering = ['name']

    def __str__(self):
        return self.name


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
    
    # Parametry EXIF (uzupełniane automatycznie)
    camera = models.CharField(max_length=100, blank=True, null=True, verbose_name="Aparat")
    focal_length = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ogniskowa")
    iso = models.CharField(max_length=50, blank=True, null=True, verbose_name="ISO")

    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Zdjęcie"
        verbose_name_plural = "Zdjęcia"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['album', '-uploaded_at']),
            models.Index(fields=['-uploaded_at']),
        ]

    def __str__(self):
        return self.title if self.title else f"Zdjęcie #{self.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Ekstrakcja danych EXIF
        if self.image and not self.camera:
            try:
                img = Image.open(self.image.path)
                exif_data = img.getexif()
                if exif_data:
                    for tag_id in exif_data:
                        tag = TAGS.get(tag_id, tag_id)
                        data = exif_data.get(tag_id)
                        
                        if tag == 'Model':
                            self.camera = str(data).strip()
                        elif tag == 'ISOSpeedRatings':
                            self.iso = str(data)
                        elif tag == 'FocalLength':
                            self.focal_length = f"{int(data)}mm"
                            
                    super().save(update_fields=['camera', 'iso', 'focal_length'])
            except Exception:
                pass


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