from django.db import models


# ==========================================
# 0. LISTA KATEGORII
# ==========================================

CATEGORY_CHOICES = [
    ('Legendy, religia, etnologia', 'Legendy, religia, etnologia'),
    ('Horror', 'Horror'),
    ('Na wagę', 'Na wagę'),
    ('Fantastyka', 'Fantastyka'),
    ('Zioła', 'Zioła'),
    ('Komiks', 'Komiks'),
    ('Do przeniesienia', 'Do przeniesienia'),
    ('Reportaż', 'Reportaż'),
    ('Historyczne', 'Historyczne'),
    ('IT', 'IT'),
    ('Poradniki', 'Poradniki'),
    ('Kryminał', 'Kryminał'),
    ('Słowniki', 'Słowniki'),
    ('Obcojęzyczne', 'Obcojęzyczne'),
    ('Literatura piękna polska', 'Literatura piękna polska'),
    ('Naukowe', 'Naukowe'),
    ('Magia', 'Magia'),
    ('Kulinarne', 'Kulinarne'),
    ('Albumy', 'Albumy'),
    ('Thriller', 'Thriller'),
    ('Postapo', 'Postapo'),
    ('Zdrowie', 'Zdrowie'),
    ('Sci-fi', 'Sci-fi'),
    ('Literatura dziecięca', 'Literatura dziecięca'),
]



from django.db import models

# ==========================================
# 0. Porcelana
# ==========================================

class Porcelain(models.Model):
    CONDITION_CHOICES = [
        ('Idealny', 'Idealny (Witrynowy)'),
        ('Bardzo dobry', 'Bardzo dobry'),
        ('Dobry', 'Dobry (lekkie przetarcia złocenia)'),
        ('Średni', 'Średni (pajęczynki, wady fabryczne)'),
        ('Zły', 'Zły (uszczerbki, pęknięcia)'),
    ]

    SIGNATURE_CHOICES = [
        ('', '--- Wybierz sygnaturę ---'),
        ('Bavaria Schuman Arzberg', 'Bavaria Schuman Arzberg'),
        ('G. H. O. Bavaria China Blau', 'G. H. O. Bavaria China Blau'),
        ('"Echt" Tuppack China Blau Tiefenfurt', '"Echt" Tuppack China Blau Tiefenfurt'),
        ('Tuppack China Blau Tiefenfurt', 'Tuppack China Blau Tiefenfurt'),
        ('China Blau', 'China Blau'),
        ('China Blau Bavaria', 'China Blau Bavaria'),
        ('E Bavaria', 'E Bavaria'),
        ('Korona China blau do identyfikacji', 'Korona China blau do identyfikacji'),
        ('RS Germany Tułowice', 'RS Germany Tułowice'),
        ('Seltmann Weiden Bavaria China Blau', 'Seltmann Weiden Bavaria China Blau'),
        ('China Blau Erbendorf Bavaria', 'China Blau Erbendorf Bavaria'),
        ('Seltmann Weiden US Zone', 'Seltmann Weiden US Zone'),
        ('Seltmann Weiden Bavaria', 'Seltmann Weiden Bavaria'),
        ('Seltmann Weiden Bavaria Thersia', 'Seltmann Weiden Bavaria Thersia'),
        ('Seltmann Weiden Bavaria W. Germany', 'Seltmann Weiden Bavaria W. Germany'),
        ('Seltmann Erbendorf', 'Seltmann Erbendorf'),
        ('Seltmann Weiden Bavaria W Germany Qualitatas Porzellan', 'Seltmann Weiden Bavaria W Germany Qualitatas Porzellan'),
        ('Seltmann Weiden Germany', 'Seltmann Weiden Germany'),
        ('Bavaria', 'Bavaria'),
        ('China Blau Ascania', 'China Blau Ascania'),
        ('Brak sygnatury', 'Brak sygnatury'),
    ]

    name = models.CharField(
        max_length=200, 
        verbose_name="Nazwa elementu",
        help_text="Np. Filiżanka, Półmisek, Jajcarka"
    )
    signature = models.CharField(
        max_length=250, 
        choices=SIGNATURE_CHOICES,
        default='',
        verbose_name="Sygnatura (Marka)", 
        blank=True, 
        null=True
    )
    year_of_origin = models.CharField(
        max_length=100, 
        verbose_name="Orientacyjny rok pochodzenia", 
        blank=True, 
        null=True,
        help_text="Np. 1945 lub 1900 - 1924"
    )
    price = models.CharField(
        max_length=100, 
        verbose_name="Cena (PLN)", 
        blank=True, 
        null=True,
        help_text="Np. 8 lub 40 - 60 zł"
    )
    
    signature_image = models.ImageField(
        upload_to='porcelain_images/signatures/', 
        verbose_name="Zdjęcie sygnatury", 
        blank=True, 
        null=True
    )
    image_1 = models.ImageField(
        upload_to='porcelain_images/products/', 
        verbose_name="Zdjęcie produktu (Główne)", 
        blank=True, 
        null=True
    )
    image_2 = models.ImageField(
        upload_to='porcelain_images/products/', 
        verbose_name="Zdjęcie produktu (Dodatkowe 1)", 
        blank=True, 
        null=True
    )
    image_3 = models.ImageField(
        upload_to='porcelain_images/products/', 
        verbose_name="Zdjęcie produktu (Dodatkowe 2)", 
        blank=True, 
        null=True
    )

    condition = models.CharField(
        max_length=50, 
        choices=CONDITION_CHOICES, 
        default='Bardzo dobry', 
        verbose_name="Stan Zachowania"
    )
    style = models.CharField(
        max_length=150, 
        default="China Blau", 
        verbose_name="Styl"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Element porcelany"
        verbose_name_plural = "Porcelana"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.signature} ({self.style})"

from django.db import models


# ==========================================
# 0. VINYLE
# ==========================================

class VinylRecord(models.Model):
    # Podstawowe dane
    artist = models.CharField(max_length=200, verbose_name="Wykonawca / Zespół")
    title = models.CharField(max_length=200, verbose_name="Tytuł albumu")
    label = models.CharField(max_length=200, blank=True, null=True, verbose_name="Wytwórnia płytowa")
    
    # Kategoryzacja i wydanie
    genre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Gatunek")
    release_year = models.IntegerField(blank=True, null=True, verbose_name="Rok wydania")
    disc_count = models.IntegerField(default=1, verbose_name="Ilość płyt w wydaniu") # <--- NOWE POLE
    
    # Stan i wartość
    condition = models.CharField(max_length=50, blank=True, null=True, verbose_name="Stan (Płyta / Okładka)")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cena / Wartość")
    
    # Zdjęcia
    front_cover = models.ImageField(upload_to='vinyls/front/', blank=True, null=True, verbose_name="Przód okładki")
    back_cover = models.ImageField(upload_to='vinyls/back/', blank=True, null=True, verbose_name="Tył okładki")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.artist} - {self.title}"

# ==========================================
# 0. Książki
# ==========================================

class Book(models.Model):
    """Rozbudowany model książki zawierający pełne metadane, informacje o czytaniu i transakcjach."""
    
    # 1. Identyfikatory i dane podstawowe z API
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True, error_messages={'unique': 'Książka z takim numerem ISBN już istnieje w Twojej biblioteczce!'})
    title = models.CharField(max_length=255, blank=True, null=True)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    authors = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=50, blank=True, null=True)
    categories = models.CharField(max_length=255, blank=True, null=True)
    publisher = models.CharField(max_length=255, blank=True, null=True)
    page_count = models.IntegerField(blank=True, null=True)
    published_at = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='library_images/', blank=True, null=True)

    # 2. Twórcy poboczni
    illustrators = models.CharField(max_length=255, blank=True, null=True)
    translators = models.CharField(max_length=255, blank=True, null=True)
    editors = models.CharField(max_length=255, blank=True, null=True)
    narrators = models.CharField(max_length=255, blank=True, null=True)
    photographers = models.CharField(max_length=255, blank=True, null=True)

    # 3. Szczegóły wydania
    format = models.CharField(max_length=100, blank=True, null=True)
    edition = models.CharField(max_length=100, blank=True, null=True)
    series = models.CharField(max_length=255, blank=True, null=True)
    volume = models.CharField(max_length=50, blank=True, null=True)
    signed = models.BooleanField(default=False)
    condition = models.CharField(max_length=100, blank=True, null=True)
    number_of_copies = models.IntegerField(default=1, blank=True, null=True)

    # 4. Status czytania, oceny i notatki
    bookshelf = models.CharField(max_length=100, blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    wishlist = models.BooleanField(default=False)
    started_reading_on = models.DateField(blank=True, null=True)
    ended_reading_on = models.DateField(blank=True, null=True)
    pages_read = models.IntegerField(blank=True, null=True)
    read = models.BooleanField(default=False)
    my_rating = models.IntegerField(blank=True, null=True)


    # 6. Dane systemowe
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.authors}"


class VideoGame(models.Model):
    # Podstawowe dane
    title = models.CharField(max_length=200, verbose_name="Tytuł gry")
    platform = models.CharField(max_length=100, verbose_name="Platforma (np. PC, PS5, Switch)")
    genre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Gatunek (np. RPG, Shooter)")
    release_year = models.IntegerField(blank=True, null=True, verbose_name="Rok wydania")
    
    # Stan i wartość
    condition = models.CharField(max_length=50, blank=True, null=True, verbose_name="Stan (Pudełko / Nośnik)")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cena / Wartość")
    
    # Zdjęcia
    cover_image = models.ImageField(upload_to='videogames/covers/', blank=True, null=True, verbose_name="Okładka gry")
    media_image = models.ImageField(upload_to='videogames/media/', blank=True, null=True, verbose_name="Płyta / Kartridż")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.platform})"


class BoardGame(models.Model):
    # Podstawowe dane
    title = models.CharField(max_length=200, verbose_name="Tytuł gry")
    publisher = models.CharField(max_length=200, blank=True, null=True, verbose_name="Wydawca")
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kategoria (np. Strategiczna, Rodzinna)")
    release_year = models.IntegerField(blank=True, null=True, verbose_name="Rok wydania")
    
    # Specyfika planszówek
    min_players = models.IntegerField(default=1, verbose_name="Min. liczba graczy")
    max_players = models.IntegerField(default=4, verbose_name="Max. liczba graczy")
    playtime = models.CharField(max_length=50, blank=True, null=True, verbose_name="Czas gry (np. 60-90 min)")
    
    # Stan i wartość
    condition = models.CharField(max_length=50, blank=True, null=True, verbose_name="Stan")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cena / Wartość")
    
    # Zdjęcia
    box_image = models.ImageField(upload_to='boardgames/box/', blank=True, null=True, verbose_name="Zdjęcie pudełka")
    board_image = models.ImageField(upload_to='boardgames/board/', blank=True, null=True, verbose_name="Zdjęcie komponentów")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title