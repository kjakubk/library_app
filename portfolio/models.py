from django.db import models

class Experience(models.Model):
    job_title = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    # Poniżej brakujące pola dat:
    start_date = models.DateField(default='2024-01-01') # Ustawiamy tymczasowy default, by ułatwić migrację
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return f"{self.job_title} w {self.company}"