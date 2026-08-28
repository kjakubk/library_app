from django.db import models


# ==========================================
# 0. LISTA KATEGORII KSIĄŻEK
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


# ==========================================
# 1. PORCELANA
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
        default='',
        verbose_name="Sygnatura (Marka)", 
        blank=True, 
        null=True,
        help_text="Wybierz z listy podpowiedzi lub wpisz nową nazwę"
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
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji")

    class Meta:
        verbose_name = "Element porcelany"
        verbose_name_plural = "Porcelana"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['signature']),
            models.Index(fields=['style']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.name} - {self.signature or 'Bez sygnatury'} ({self.style})"


# ==========================================
# 2. PŁYTY WINYLOWE
# ==========================================

class VinylRecord(models.Model):
    GENRE_CHOICES = [
        ('Rock', 'Rock'),
        ('Pop', 'Pop'),
        ('Jazz', 'Jazz'),
        ('Blues', 'Blues'),
        ('Elektroniczna / Synth', 'Elektroniczna / Synth'),
        ('Hip-Hop / Rap', 'Hip-Hop / Rap'),
        ('Metal / Hard Rock', 'Metal / Hard Rock'),
        ('Klasyczna', 'Klasyczna'),
        ('Polski Rock / Polska Muzyka', 'Polski Rock / Polska Muzyka'),
        ('Funk / Soul / R&B', 'Funk / Soul / R&B'),
        ('Reggae / Dub', 'Reggae / Dub'),
        ('Punk / New Wave', 'Punk / New Wave'),
        ('Filmowa / Soundtrack', 'Filmowa / Soundtrack'),
        ('Folk / Country', 'Folk / Country'),
        ('Ambient / Chillout', 'Ambient / Chillout'),
        ('Inny', 'Inny'),
    ]

    CONDITION_CHOICES = [
        ('Mint (M) - Nowy / Folia', 'Mint (M) - Nowy / Fabryczna folia'),
        ('Near Mint (NM / M-)', 'Near Mint (NM / M-) - Prawie idealny'),
        ('Excellent (EX / VG++)', 'Excellent (EX / VG++) - Znakomity'),
        ('Very Good Plus (VG+)', 'Very Good Plus (VG+) - Bardzo dobry plus'),
        ('Very Good (VG)', 'Very Good (VG) - Bardzo dobry'),
        ('Good Plus (G+)', 'Good Plus (G+) - Dobry plus'),
        ('Good (G)', 'Good (G) - Dobry'),
        ('Fair / Poor (F/P)', 'Fair / Poor (F/P) - Dostateczny / Uszkodzony'),
    ]

    artist = models.CharField(max_length=200, verbose_name="Wykonawca / Zespół")
    title = models.CharField(max_length=200, verbose_name="Tytuł albumu")
    label = models.CharField(max_length=200, blank=True, null=True, verbose_name="Wytwórnia płytowa")
    
    genre = models.CharField(max_length=100, choices=GENRE_CHOICES, blank=True, null=True, verbose_name="Gatunek")
    release_year = models.IntegerField(blank=True, null=True, verbose_name="Rok wydania")
    disc_count = models.IntegerField(default=1, verbose_name="Ilość płyt w wydaniu")
    
    condition = models.CharField(max_length=100, choices=CONDITION_CHOICES, blank=True, null=True, verbose_name="Stan (Płyta / Okładka)")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cena / Wartość")
    
    front_cover = models.ImageField(upload_to='vinyls/front/', blank=True, null=True, verbose_name="Przód okładki")
    back_cover = models.ImageField(upload_to='vinyls/back/', blank=True, null=True, verbose_name="Tył okładki")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Płyta winylowa"
        verbose_name_plural = "Płyty winylowe"
        ordering = ['artist', 'title']
        indexes = [
            models.Index(fields=['artist']),
            models.Index(fields=['title']),
            models.Index(fields=['genre']),
            models.Index(fields=['release_year']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.artist} - {self.title}"


# ==========================================
# 3. KSIĄŻKI
# ==========================================

class Book(models.Model):
    """Model książki zawierający pełne metadane, statusy czytania i parametry egzemplarza."""
    
    # 1. Identyfikatory i dane podstawowe
    isbn = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True, 
        null=True, 
        verbose_name="ISBN / EAN",
        error_messages={'unique': 'Książka z takim numerem ISBN już istnieje w Twojej biblioteczce!'}
    )
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tytuł")
    subtitle = models.CharField(max_length=255, blank=True, null=True, verbose_name="Podtytuł")
    authors = models.CharField(max_length=255, blank=True, null=True, verbose_name="Autorzy")
    language = models.CharField(max_length=50, blank=True, null=True, default='PL', verbose_name="Język")
    categories = models.CharField(max_length=255, blank=True, null=True, verbose_name="Kategorie / Gatunek")
    publisher = models.CharField(max_length=255, blank=True, null=True, verbose_name="Wydawnictwo")
    page_count = models.IntegerField(blank=True, null=True, verbose_name="Liczba stron")
    published_at = models.CharField(max_length=50, blank=True, null=True, verbose_name="Data publikacji / Rok")
    description = models.TextField(blank=True, null=True, verbose_name="Opis książki")
    image = models.ImageField(upload_to='library_images/', blank=True, null=True, verbose_name="Okładka")

    # 2. Twórcy poboczni
    illustrators = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ilustratorzy")
    translators = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tłumacze")
    editors = models.CharField(max_length=255, blank=True, null=True, verbose_name="Redaktorzy")
    narrators = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lektorzy")
    photographers = models.CharField(max_length=255, blank=True, null=True, verbose_name="Fotografowie")

    # 3. Szczegóły wydania i stan
    format = models.CharField(max_length=100, blank=True, null=True, verbose_name="Format / Typ oprawy")
    edition = models.CharField(max_length=100, blank=True, null=True, verbose_name="Wydanie")
    series = models.CharField(max_length=255, blank=True, null=True, verbose_name="Seria wydawnicza")
    volume = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tom")
    signed = models.BooleanField(default=False, verbose_name="Autograf / Dedykacja")
    condition = models.CharField(max_length=100, blank=True, null=True, verbose_name="Stan zachowania")
    number_of_copies = models.IntegerField(default=1, blank=True, null=True, verbose_name="Liczba egzemplarzy")

    # 4. Status czytania, półka i oceny
    bookshelf = models.CharField(max_length=100, blank=True, null=True, verbose_name="Półka / Regał")
    tags = models.CharField(max_length=255, blank=True, null=True, verbose_name="Tagi")
    wishlist = models.BooleanField(default=False, verbose_name="Lista życzeń")
    started_reading_on = models.DateField(blank=True, null=True, verbose_name="Rozpoczęto czytanie")
    ended_reading_on = models.DateField(blank=True, null=True, verbose_name="Zakończono czytanie")
    pages_read = models.IntegerField(blank=True, null=True, default=0, verbose_name="Przeczytane strony")
    read = models.BooleanField(default=False, verbose_name="Przeczytana")
    my_rating = models.IntegerField(blank=True, null=True, verbose_name="Moja ocena (1-5)")

    # 5. Dane systemowe
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania do biblioteki")

    class Meta:
        verbose_name = "Książka"
        verbose_name_plural = "Książki"
        ordering = ['title', 'authors']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['isbn']),
            models.Index(fields=['read']),
            models.Index(fields=['wishlist']),
            models.Index(fields=['categories']),
            models.Index(fields=['bookshelf']),
            models.Index(fields=['-date_added']),
        ]
    
    def __str__(self):
        return f"{self.title or 'Bez tytułu'} - {self.authors or 'Nieznany autor'}"


# ==========================================
# 4. GRY WIDEO
# ==========================================

class VideoGame(models.Model):
    GENRE_CHOICES = [
        ('Akcja', 'Akcja (Action)'),
        ('RPG', 'RPG (Role-Playing Game)'),
        ('Strzelanka', 'Strzelanka (Shooter)'),
        ('Przygodowa', 'Przygodowa (Adventure)'),
        ('Strategia', 'Strategia (Strategy)'),
        ('Sportowa', 'Sportowa (Sports)'),
        ('Wyścigi', 'Wyścigi (Racing)'),
        ('Bijatyka', 'Bijatyka (Fighting)'),
        ('Platformówka', 'Platformówka (Platformer)'),
        ('Symulacja', 'Symulacja (Simulation)'),
        ('Zręcznościowa', 'Zręcznościowa (Arcade)'),
        ('Logiczna', 'Logiczna (Puzzle)'),
        ('Horror', 'Horror (Survival Horror)'),
        ('MMO / Sieciowa', 'MMO / Sieciowa'),
        ('Inny', 'Inny'),
    ]

    CONDITION_CHOICES = [
        ('Nowy (Folia)', 'Nowy (Folia)'),
        ('Idealny', 'Idealny'),
        ('Bardzo dobry', 'Bardzo dobry'),
        ('Dobry', 'Dobry'),
        ('Dostateczny', 'Dostateczny'),
        ('Zły / Uszkodzony', 'Zły / Uszkodzony'),
        ('Tylko nośnik', 'Tylko nośnik (brak pudełka)'),
        ('Tylko pudełko', 'Tylko pudełko (brak gry)'),
    ]

    title = models.CharField(max_length=200, verbose_name="Tytuł gry")
    platform = models.CharField(max_length=100, verbose_name="Platforma (np. PC, PS5, Switch)")
    genre = models.CharField(max_length=100, choices=GENRE_CHOICES, blank=True, null=True, verbose_name="Gatunek")
    release_year = models.IntegerField(blank=True, null=True, verbose_name="Rok wydania")
    
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES, blank=True, null=True, verbose_name="Stan")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cena / Wartość")
    
    cover_image = models.ImageField(upload_to='videogames/covers/', blank=True, null=True, verbose_name="Okładka gry")
    back_cover_image = models.ImageField(upload_to='videogames/back_covers/', blank=True, null=True, verbose_name="Tył pudełka")
    media_image = models.ImageField(upload_to='videogames/media/', blank=True, null=True, verbose_name="Płyta / Kartridż")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Gra wideo"
        verbose_name_plural = "Gry wideo"
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['platform']),
            models.Index(fields=['genre']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.platform})"


# ==========================================
# 5. GRY PLANSZOWE
# ==========================================

class BoardGame(models.Model):
    title = models.CharField(max_length=200, verbose_name="Tytuł gry")
    publisher = models.CharField(max_length=200, blank=True, null=True, verbose_name="Wydawca")
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kategoria (np. Strategiczna, Rodzinna)")
    release_year = models.IntegerField(blank=True, null=True, verbose_name="Rok wydania")
    
    min_players = models.IntegerField(default=1, verbose_name="Min. liczba graczy")
    max_players = models.IntegerField(default=4, verbose_name="Max. liczba graczy")
    playtime = models.CharField(max_length=50, blank=True, null=True, verbose_name="Czas gry (np. 60-90 min)")
    
    condition = models.CharField(max_length=50, blank=True, null=True, verbose_name="Stan")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cena / Wartość")
    
    box_image = models.ImageField(upload_to='boardgames/box/', blank=True, null=True, verbose_name="Zdjęcie pudełka")
    board_image = models.ImageField(upload_to='boardgames/board/', blank=True, null=True, verbose_name="Zdjęcie komponentów")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Gra planszowa"
        verbose_name_plural = "Gry planszowe"
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['publisher']),
            models.Index(fields=['category']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title

# ==========================================
# 6. KONSOLE I AKCESORIA
# ==========================================

class ConsoleHardware(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa konsoli / akcesorium")
    manufacturer = models.CharField(max_length=200, blank=True, null=True, verbose_name="Producent (np. Sony, Nintendo)")
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kategoria (np. Konsola, Pad, Karta pamięci)")
    release_year = models.IntegerField(blank=True, null=True, verbose_name="Rok wydania")
    
    condition = models.CharField(max_length=50, blank=True, null=True, verbose_name="Stan zachowania")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Wartość / Cena")
    
    image = models.ImageField(upload_to='consoles/', blank=True, null=True, verbose_name="Zdjęcie główne")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Konsola / Akcesorium"
        verbose_name_plural = "Konsole i Akcesoria"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['category']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.manufacturer})"


# ==========================================
# 7. INNE ANTYKI
# ==========================================

class Antique(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa przedmiotu (np. Lampa, Obraz, Ramka)")
    material = models.CharField(max_length=100, blank=True, null=True, verbose_name="Materiał (np. Mosiądz, Szkło, Drewno)")
    style = models.CharField(max_length=100, blank=True, null=True, verbose_name="Styl / Epoka")
    year_of_origin = models.CharField(max_length=100, blank=True, null=True, verbose_name="Orientacyjny rok pochodzenia")
    
    condition = models.CharField(max_length=50, blank=True, null=True, verbose_name="Stan zachowania")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Wartość / Cena")
    
    image = models.ImageField(upload_to='antiques/', blank=True, null=True, verbose_name="Zdjęcie główne")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Inny Antyk"
        verbose_name_plural = "Inne Antyki"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['material']),
            models.Index(fields=['style']),
            models.Index(fields=['-created_at']),
        ]

# ==========================================
# 8. GRY CYFROWE
# ==========================================

class DigitalGame(models.Model):
    PLATFORM_CHOICES = [
        ('Steam', 'Steam'),
        ('Epic Games', 'Epic Games'),
        ('GOG', 'GOG.com'),
        ('PlayStation Network', 'PlayStation Network (PSN)'),
        ('Xbox Live', 'Xbox Live'),
        ('Nintendo eShop', 'Nintendo eShop'),
        ('Battle.net', 'Battle.net'),
        ('EA App', 'EA App / Origin'),
        ('Ubisoft Connect', 'Ubisoft Connect'),
        ('Amazon Games', 'Amazon Games'),
        ('Inna', 'Inna platforma'),
    ]

    title = models.CharField(max_length=200, verbose_name="Tytuł gry")
    platform = models.CharField(max_length=100, choices=PLATFORM_CHOICES, verbose_name="Platforma / Sklep")
    genre = models.CharField(max_length=100, choices=VideoGame.GENRE_CHOICES, blank=True, null=True, verbose_name="Gatunek")
    release_year = models.IntegerField(blank=True, null=True, verbose_name="Rok wydania")
    
    is_finished = models.BooleanField(default=False, verbose_name="Ukończona")
    notes = models.TextField(blank=True, null=True, verbose_name="Notatki (np. Edycja GOTY, DLC)")
    
    cover_image = models.ImageField(upload_to='digital_games/covers/', blank=True, null=True, verbose_name="Okładka gry")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")

    class Meta:
        verbose_name = "Gra cyfrowa"
        verbose_name_plural = "Gry cyfrowe"
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['platform']),
            models.Index(fields=['genre']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.platform})"