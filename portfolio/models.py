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
    start_date = models.DateField(default='2024-01-01', verbose_name="Data rozpoczęcia")
    end_date = models.DateField(null=True, blank=True, verbose_name="Data zakończenia")
    description = models.TextField(verbose_name="Opis obowiązków i osiągnięć")

    class Meta:
        verbose_name = "Doświadczenie zawodowe"
        verbose_name_plural = "Doświadczenia zawodowe"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['-start_date']),
        ]

    def __str__(self):
        return f"{self.job_title} w {self.company}"