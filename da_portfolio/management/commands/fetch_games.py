# da_portfolio/management/commands/fetch_games.py

from django.core.management.base import BaseCommand
from da_portfolio.utils import run_full_etl

class Command(BaseCommand):
    help = 'Pobiera dane giełdowe wydawców oraz dane o grach z IGDB do modelu relacyjnego PostgreSQL'

    def handle(self, *args, **kwargs):
        self.stdout.write("Rozpoczynam pełny proces ETL (Finanse + Gaming)...")
        try:
            # Uruchamiamy pełny potok pobierający finanse oraz gry
            run_full_etl()
            self.stdout.write(self.style.SUCCESS("Pomyślnie zaktualizowano i zasilono bazę danych!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Wystąpił błąd podczas procesu ETL: {e}"))