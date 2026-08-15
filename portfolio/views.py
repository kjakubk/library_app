from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from .models import Photo, Album, Experience
from .forms import PhotoForm, AlbumForm, LoginForm, UserAdminCreateForm, UserAdminPasswordChangeForm


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


# ==========================================
# ZARZĄDZANIE UŻYTKOWNIKAMI Z POZIOMU PANELU
# ==========================================

@login_required
def user_list_view(request):
    """Lista wszystkich użytkowników w systemie z możliwością zarządzania."""
    users = User.objects.all().order_by('-is_superuser', '-date_joined')
    return render(request, 'portfolio/user_list.html', {'users_list': users})


@login_required
def user_create_view(request):
    """Dodawanie nowego użytkownika z poziomu panelu po zalogowaniu."""
    if request.method == 'POST':
        form = UserAdminCreateForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data.get('email', '')
            password = form.cleaned_data['password']
            is_admin = form.cleaned_data.get('is_administrator', False)

            # Tworzymy użytkownika
            new_user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            if is_admin:
                new_user.is_staff = True
                new_user.is_superuser = True
            else:
                new_user.is_staff = False
                new_user.is_superuser = False
            new_user.save()

            messages.success(request, f'Pomyślnie utworzono konto dla użytkownika „{username}”. Może się już zalogować do portalu!')
            return redirect('user_list')
    else:
        form = UserAdminCreateForm()

    return render(request, 'portfolio/user_form.html', {'form': form})


@login_required
def user_delete_view(request, pk):
    """Usuwanie użytkownika z poziomu panelu."""
    user_to_delete = get_object_or_404(User, pk=pk)
    
    # Blokada usunięcia samego siebie
    if user_to_delete.pk == request.user.pk:
        messages.error(request, 'Nie możesz usunąć swojego własnego konta!')
        return redirect('user_list')
        
    if request.method == 'POST':
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'Użytkownik „{username}” został pomyślnie usunięty z systemu.')
        return redirect('user_list')
        
    return redirect('user_list')


@login_required
def user_change_password_view(request, pk):
    """Zmiana hasła dla wskazanego użytkownika z panelu."""
    target_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserAdminPasswordChangeForm(request.POST)
        if form.is_valid():
            new_pass = form.cleaned_data['new_password']
            target_user.set_password(new_pass)
            target_user.save()
            messages.success(request, f'Pomyślnie zmieniono hasło dla użytkownika „{target_user.username}”.')
            return redirect('user_list')
    else:
        form = UserAdminPasswordChangeForm()

    return render(request, 'portfolio/user_password_form.html', {'form': form, 'target_user': target_user})