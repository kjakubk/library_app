from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Photo, Album, Experience
from .forms import PhotoForm, AlbumForm, LoginForm


def home_view(request):
    """Strona główna witryny / powitanie (wymaga zalogowania przez middleware)."""
    return render(request, 'portfolio/home.html')


def cv_view(request):
    """Interaktywny widok CV i doświadczenia zawodowego."""
    experiences = Experience.objects.all().order_by('-start_date')
    return render(request, 'portfolio/cv.html', {'experiences': experiences})


def portfolio_gallery(request):
    """Galeria zdjęć z filtrowaniem po albumach."""
    selected_album = request.GET.get('album', '')
    albums = Album.objects.all()
    
    if selected_album:
        photos = Photo.objects.filter(album__id=selected_album).order_by('-uploaded_at')
    else:
        photos = Photo.objects.all().order_by('-uploaded_at')

    context = {
        'photos': photos,
        'albums': albums,
        'selected_album': int(selected_album) if selected_album and selected_album.isdigit() else '',
    }
    return render(request, 'portfolio/gallery.html', context)


@login_required
def add_photo(request):
    """Dodawanie nowego zdjęcia z automatycznym odczytem EXIF."""
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zdjęcie zostało pomyślnie dodane do galerii!')
            return redirect('portfolio_gallery')
    else:
        form = PhotoForm()
    
    return render(request, 'portfolio/add_photo.html', {'form': form})


@login_required
def add_album(request):
    """Tworzenie nowego albumu w galerii."""
    if request.method == 'POST':
        form = AlbumForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Album został pomyślnie utworzony!')
            return redirect('portfolio_gallery')
    else:
        form = AlbumForm()
    
    return render(request, 'portfolio/add_album.html', {'form': form})


@login_required
def delete_photo(request, pk):
    """Usuwanie zdjęcia z galerii."""
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        photo.delete()
        messages.success(request, 'Zdjęcie zostało usunięte.')
        return redirect('portfolio_gallery')
    return redirect('portfolio_gallery')


# ==========================================
# WIDOKI AUTORYZACJI Z WHITELISTĄ
# ==========================================

def login_view(request):
    """Widok logowania użytkownika z weryfikacją whitelisty."""
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # --- WERYFIKACJA WHITELISTY ---
            whitelist = getattr(settings, 'AUTH_WHITELIST', [])
            is_whitelisted = (
                user.is_superuser
                or user.is_staff
                or (user.username and user.username.lower() in whitelist)
                or (user.email and user.email.lower() in whitelist)
            )

            if not is_whitelisted:
                messages.error(
                    request, 
                    f'Odmowa dostępu: Konto "{user.username}" nie znajduje się na liście dozwolonych użytkowników (whitelist). Skontaktuj się z administratorem.'
                )
                return render(request, 'portfolio/login.html', {'form': form})

            # Pomyślne logowanie
            login(request, user)
            messages.success(request, f'Witaj w Data Hubie, {user.username}!')
            next_url = request.GET.get('next') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, 'Niepoprawna nazwa użytkownika lub hasło.')
    else:
        form = LoginForm()
        
    return render(request, 'portfolio/login.html', {'form': form})


def logout_view(request):
    """Wylogowanie użytkownika."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Zostałeś pomyślnie wylogowany.')
    return redirect('login')