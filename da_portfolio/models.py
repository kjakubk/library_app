from django.db import models


class Market(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Rynek giełdowy")

    class Meta:
        verbose_name = "Rynek giełdowy"
        verbose_name_plural = "Rynki giełdowe"
        ordering = ['name']

    def __str__(self):
        return self.name


class Publisher(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Wydawca / Spółka")
    ticker = models.CharField(max_length=20, unique=True, verbose_name="Symbol giełdowy (Ticker)")
    market = models.ForeignKey(
        'Market', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='publishers',
        verbose_name="Rynek"
    )
    
    # Dane lokalizacyjne do wizualizacji mapowych
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Adres")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="Miasto")
    country = models.CharField(max_length=100, null=True, blank=True, verbose_name="Kraj")

    class Meta:
        verbose_name = "Wydawca"
        verbose_name_plural = "Wydawcy"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['ticker']),
        ]

    def __str__(self):
        return f"{self.name} ({self.ticker})"


class Platform(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Platforma sprzętowa")

    class Meta:
        verbose_name = "Platforma sprzętowa"
        verbose_name_plural = "Platformy sprzętowe"
        ordering = ['name']

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Gatunek gry")

    class Meta:
        verbose_name = "Gatunek gry"
        verbose_name_plural = "Gatunki gier"
        ordering = ['name']

    def __str__(self):
        return self.name


class Game(models.Model):
    game_id = models.IntegerField(unique=True, verbose_name="ID gry w hurtowni")
    publisher = models.ForeignKey(
        Publisher, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='games',
        verbose_name="Wydawca"
    )
    title = models.CharField(max_length=255, verbose_name="Tytuł gry")
    release_date = models.DateField(null=True, blank=True, verbose_name="Data premiery")
    rating = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Ocena")
    
    # Relacje wiele-do-wielu
    genres = models.ManyToManyField(Genre, related_name='games', verbose_name="Gatunki")
    platforms = models.ManyToManyField(Platform, related_name='games', verbose_name="Platformy")

    class Meta:
        verbose_name = "Gra"
        verbose_name_plural = "Gry"
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['rating']),
            models.Index(fields=['release_date']),
            models.Index(fields=['publisher', '-rating']),
        ]

    def __str__(self):
        return self.title


class StockMetric(models.Model):
    publisher = models.ForeignKey(
        Publisher, 
        on_delete=models.CASCADE, 
        related_name='stock_metrics',
        verbose_name="Wydawca"
    )
    date = models.DateField(verbose_name="Data notowania")
    stock_close = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, verbose_name="Kurs zamknięcia")
    volume = models.BigIntegerField(null=True, blank=True, verbose_name="Wolumen")
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, verbose_name="Kapitalizacja rynkowa")

    class Meta:
        verbose_name = "Metryka giełdowa"
        verbose_name_plural = "Metryki giełdowe"
        unique_together = ('publisher', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['publisher', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['publisher', '-date']),
        ]

    def __str__(self):
        return f"{self.publisher.ticker} - {self.date}"