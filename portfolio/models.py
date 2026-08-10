from django.db import models

from django.db import models
from PIL import Image
from PIL.ExifTags import TAGS

class Album(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa albumu (Kategoria)")
    description = models.TextField(blank=True, null=True, verbose_name="Krótki opis")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Photo(models.Model):
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    image = models.ImageField(upload_to='portfolio/photos/', verbose_name="Zdjęcie")
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name="Tytuł / Podpis")
    
    # Parametry EXIF (Pola, które system wypełni sam!)
    camera = models.CharField(max_length=100, blank=True, null=True, verbose_name="Aparat")
    focal_length = models.CharField(max_length=50, blank=True, null=True, verbose_name="Ogniskowa")
    iso = models.CharField(max_length=50, blank=True, null=True, verbose_name="ISO")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title if self.title else f"Zdjęcie #{self.id}"

    def save(self, *args, **kwargs):
        # Najpierw zapisujemy zdjęcie na serwerze
        super().save(*args, **kwargs)
        
        # Następnie próbujemy z niego wyciągnąć EXIF
        if self.image and not self.camera: # tylko jeśli nie ma jeszcze przypisanego aparatu
            try:
                img = Image.open(self.image.path)
                exif_data = img.getexif()
                if exif_data:
                    for tag_id in exif_data:
                        tag = TAGS.get(tag_id, tag_id)
                        data = exif_data.get(tag_id)
                        
                        # Odczyt modelu aparatu
                        if tag == 'Model':
                            self.camera = str(data).strip()
                        # Odczyt ISO
                        elif tag == 'ISOSpeedRatings':
                            self.iso = str(data)
                        # Odczyt Ogniskowej
                        elif tag == 'FocalLength':
                            self.focal_length = f"{int(data)}mm"
                            
                    # Zapisujemy wyciągnięte dane (bez wywoływania pętli)
                    super().save(update_fields=['camera', 'iso', 'focal_length'])
            except Exception:
                pass # Jeśli się nie uda (np. to PNG bez EXIF), po prostu to pomiń

class Experience(models.Model):
    job_title = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    # Poniżej brakujące pola dat:
    start_date = models.DateField(default='2024-01-01') # Ustawiamy tymczasowy default, by ułatwić migrację
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return f"{self.job_title} w {self.company}"