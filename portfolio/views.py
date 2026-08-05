from django.shortcuts import render
from .models import Experience

def cv_view(request):
    # Pobieramy doświadczenie posortowane malejąco po dacie rozpoczęcia
    experiences = Experience.objects.all().order_by('-start_date')
    return render(request, 'portfolio/cv.html', {'experiences': experiences})

def home_view(request):
    return render(request, 'portfolio/home.html')