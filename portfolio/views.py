import os
import io
import json
import zipfile
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Photo, Album, Experience, CVProfile
from .forms import PhotoForm, PhotoEditForm, AlbumForm, LoginForm, UserAdminCreateForm, UserAdminPasswordChangeForm

from library.models import Book, Porcelain, VinylRecord, VideoGame, BoardGame, ConsoleHardware, Antique, DigitalGame

def home_view(request):
    """Strona główna witryny / powitanie (wymaga zalogowania przez middleware)."""
    profile = CVProfile.objects.first()
    
    book_count = Book.objects.count()
    porcelain_count = Porcelain.objects.count()
    vinyl_count = VinylRecord.objects.count()
    video_game_count = VideoGame.objects.count()
    digital_games_count = DigitalGame.objects.count()
    board_game_count = BoardGame.objects.count()
    console_count = ConsoleHardware.objects.count()
    antique_count = Antique.objects.count()
    
    total_items = (
        book_count + porcelain_count + vinyl_count + video_game_count +
        digital_games_count + board_game_count + console_count + antique_count
    )

    # Zbieranie ostatnio dodanych elementów ze wszystkich kolekcji
    recent_items = []

    for b in Book.objects.order_by('-date_added')[:5]:
        recent_items.append({
            'title': b.title or 'Bez tytułu',
            'subtitle': b.authors or 'Nieznany autor',
            'category': 'Książki',
            'category_icon': '📖',
            'category_url': 'book_list',
            'badge_class': 'bg-primary',
            'image_url': b.image.url if b.image else None,
            'date': b.date_added,
        })

    for p in Porcelain.objects.order_by('-created_at')[:5]:
        img = p.image_1.url if p.image_1 else (p.signature_image.url if p.signature_image else None)
        recent_items.append({
            'title': p.name,
            'subtitle': p.signature or p.style or 'Porcelana',
            'category': 'Porcelana',
            'category_icon': '☕',
            'category_url': 'porcelain_list',
            'badge_class': 'bg-info',
            'image_url': img,
            'date': p.created_at,
        })

    for v in VinylRecord.objects.order_by('-created_at')[:5]:
        img = v.front_cover.url if v.front_cover else (v.back_cover.url if v.back_cover else None)
        recent_items.append({
            'title': v.title,
            'subtitle': v.artist,
            'category': 'Płyty winylowe',
            'category_icon': '🎵',
            'category_url': 'vinyl_list',
            'badge_class': 'bg-success',
            'image_url': img,
            'date': v.created_at,
        })

    for vg in VideoGame.objects.order_by('-created_at')[:5]:
        recent_items.append({
            'title': vg.title,
            'subtitle': vg.platform or 'Gra wideo',
            'category': 'Gry wideo',
            'category_icon': '🎮',
            'category_url': 'video_game_list',
            'badge_class': 'bg-warning text-dark',
            'image_url': vg.cover_image.url if vg.cover_image else None,
            'date': vg.created_at,
        })

    for dg in DigitalGame.objects.order_by('-created_at')[:5]:
        img = dg.cover_image.url if dg.cover_image else None
        recent_items.append({
            'title': dg.title,
            'subtitle': dg.platform or 'Gra cyfrowa',
            'category': 'Gry cyfrowe',
            'category_icon': '☁️',
            'category_url': 'digital_game_list',
            'badge_class': 'bg-primary',
            'image_url': img,
            'date': dg.created_at,
        })

    for bg in BoardGame.objects.order_by('-created_at')[:5]:
        img = bg.box_image.url if bg.box_image else (bg.board_image.url if bg.board_image else None)
        recent_items.append({
            'title': bg.title,
            'subtitle': bg.publisher or bg.category or 'Gra planszowa',
            'category': 'Gry planszowe',
            'category_icon': '🎲',
            'category_url': 'board_game_list',
            'badge_class': 'bg-danger',
            'image_url': img,
            'date': bg.created_at,
        })

    for c in ConsoleHardware.objects.order_by('-created_at')[:5]:
        recent_items.append({
            'title': c.name,
            'subtitle': c.manufacturer or c.category or 'Sprzęt',
            'category': 'Konsole',
            'category_icon': '🕹️',
            'category_url': 'console_list',
            'badge_class': 'bg-secondary',
            'image_url': c.image.url if c.image else None,
            'date': c.created_at,
        })

    for a in Antique.objects.order_by('-created_at')[:5]:
        recent_items.append({
            'title': a.name,
            'subtitle': a.material or a.style or 'Antyk',
            'category': 'Inne Antyki',
            'category_icon': '🕰️',
            'category_url': 'antique_list',
            'badge_class': 'bg-secondary',
            'image_url': a.image.url if a.image else None,
            'date': a.created_at,
        })

    # Sortowanie po dacie malejąco i wybór 8 najnowszych
    recent_items.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
    recent_items = recent_items[:8]

    context = {
        'profile': profile,
        'total_items': total_items,
        'recent_items': recent_items,
        'book_count': book_count,
        'porcelain_count': porcelain_count,
        'vinyl_count': vinyl_count,
        'video_game_count': video_game_count,
        'digital_games_count': digital_games_count,
        'board_game_count': board_game_count,
        'console_count': console_count,
        'antique_count': antique_count,
    }
    return render(request, 'portfolio/home.html', context)

def portfolio_gallery(request):
    """Galeria zdjęć z filtrowaniem, tagami i sekcją wyróżnionych."""
    selected_album = request.GET.get('album', '')
    selected_tag = request.GET.get('tag', '')
    sort_by = request.GET.get('sort', 'order')  # order | newest | oldest | title

    albums = Album.objects.all()

    photos_qs = Photo.objects.select_related('album')
    if selected_album:
        photos_qs = photos_qs.filter(album__id=selected_album)
    if selected_tag:
        photos_qs = photos_qs.filter(tags__icontains=selected_tag)

    if sort_by == 'newest':
        photos_qs = photos_qs.order_by('-uploaded_at')
    elif sort_by == 'oldest':
        photos_qs = photos_qs.order_by('uploaded_at')
    elif sort_by == 'title':
        photos_qs = photos_qs.order_by('title')
    else:  # order (default)
        photos_qs = photos_qs.order_by('sort_order', '-uploaded_at')

    photos = list(photos_qs)
    featured_photos = Photo.objects.filter(is_featured=True).order_by('sort_order', '-uploaded_at') if not selected_album and not selected_tag else []

    # Zbierz wszystkie tagi ze wszystkich zdjęć
    all_tags = set()
    for p in Photo.objects.exclude(tags__isnull=True).exclude(tags='').values_list('tags', flat=True):
        for t in p.split(','):
            t = t.strip()
            if t:
                all_tags.add(t)
    all_tags = sorted(all_tags)

    # Statystyki
    total_photos = Photo.objects.count()
    total_albums = albums.count()
    featured_count = Photo.objects.filter(is_featured=True).count()
    with_location = Photo.objects.exclude(location__isnull=True).exclude(location='').count()

    context = {
        'photos': photos,
        'albums': albums,
        'selected_album': int(selected_album) if selected_album and selected_album.isdigit() else '',
        'selected_tag': selected_tag,
        'sort_by': sort_by,
        'all_tags': all_tags,
        'featured_photos': featured_photos,
        'total_photos': total_photos,
        'total_albums': total_albums,
        'featured_count': featured_count,
        'with_location': with_location,
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
def edit_photo(request, pk):
    """Edycja istniejącego zdjęcia."""
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        form = PhotoEditForm(request.POST, instance=photo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zdjęcie zostało zaktualizowane.')
            return redirect('portfolio_gallery')
    else:
        form = PhotoEditForm(instance=photo)

    return render(request, 'portfolio/edit_photo.html', {'form': form, 'photo': photo})


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
def edit_album(request, pk):
    """Edycja albumu."""
    album = get_object_or_404(Album, pk=pk)
    if request.method == 'POST':
        form = AlbumForm(request.POST, instance=album)
        if form.is_valid():
            form.save()
            messages.success(request, f'Album „{album.name}" zaktualizowany.')
            return redirect('portfolio_gallery')
    else:
        form = AlbumForm(instance=album)
    return render(request, 'portfolio/add_album.html', {'form': form, 'album': album})


@login_required
def delete_album(request, pk):
    """Usuwanie albumu (zdjęcia pozostają, album = NULL)."""
    album = get_object_or_404(Album, pk=pk)
    if request.method == 'POST':
        name = album.name
        album.delete()
        messages.success(request, f'Album „{name}" został usunięty.')
        return redirect('portfolio_gallery')
    return redirect('portfolio_gallery')


@login_required
def delete_photo(request, pk):
    """Usuwanie zdjęcia z galerii."""
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        photo.delete()
        messages.success(request, 'Zdjęcie zostało usunięte.')
        return redirect('portfolio_gallery')
    return redirect('portfolio_gallery')


@login_required
@require_POST
def update_photo_order(request):
    """AJAX: aktualizacja sort_order zdjęć po przeciągnięciu."""
    try:
        data = json.loads(request.body)
        order_list = data.get('order', [])  # [{id: 5, order: 0}, ...]
        for item in order_list:
            Photo.objects.filter(pk=item['id']).update(sort_order=item['order'])
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)




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


@login_required
def download_backup_zip(request):
    """Generuje i pobiera pełne archiwum ZIP zawierające bazę danych SQLite, zrzut JSON oraz folder ze zdjęciami (media/)."""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'Tylko administrator może pobrać kopię zapasową bazy danych!')
        return redirect('home')

    zip_buffer = io.BytesIO()
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Plik bazy SQLite
        sqlite_path = settings.BASE_DIR / 'db.sqlite3'
        if os.path.exists(sqlite_path):
            zip_file.write(sqlite_path, arcname='db.sqlite3')

        # 2. Zrzut JSON modeli kolekcji i użytkowników (uniwersalny do Postgresa, SQLite, MySQL)
        try:
            json_dump_buffer = io.StringIO()
            call_command(
                'dumpdata',
                'library', 'portfolio', 'auth.User',
                '--natural-foreign',
                '--natural-primary',
                stdout=json_dump_buffer
            )
            zip_file.writestr('database_dump.json', json_dump_buffer.getvalue().encode('utf-8'))
        except Exception as e:
            zip_file.writestr('dump_error.txt', f'Błąd podczas generowania dumpdata: {e}')

        # 3. Cały katalog media/ (wszystkie zdjęcia)
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            for root, dirs, files in os.walk(media_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, settings.BASE_DIR)
                    zip_file.write(file_path, arcname=arc_name)

        # 4. Plik informacyjny manifest
        manifest_content = f"""KOPIA ZAPASOWA APLIKACJI KOLEKCJI
Data utworzenia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Wygenerowano przez: {request.user.username}

Zawartość archiwum:
1. db.sqlite3 - bezpośredni plik bazy danych SQLite
2. database_dump.json - uniwersalny zrzut wszystkich tabel i relacji
3. media/ - wszystkie wgrane zdjęcia porcelany, książek, okładek, galerii

Jak przywrócić w razie potrzeby:
- Wypakuj plik db.sqlite3 oraz katalog media/ do głównego folderu aplikacji na nowym serwerze.
"""
        zip_file.writestr('MANIFEST_BACKUP.txt', manifest_content.encode('utf-8'))

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="kolekcja_backup_{now_str}.zip"'
    return response


# ==========================================
# MODUŁ MOJE CV (INTERAKTYWNE & EDYTOWALNE)
# ==========================================

from .models import CVProfile, Education, Skill, Language, Certificate, Project, Hobby
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def cv_view(request):
    """Widok profesjonalnego CV z możliwością bezpośredniej edycji na stronie."""
    profile = CVProfile.objects.first()
    if not profile:
        profile = CVProfile.objects.create(
            full_name="Jakub",
            title="Specjalista ds. Danych / Programista",
            summary="Doświadczony specjalista z pasją do automatyzacji procesów, tworzenia skalowalnych aplikacji internetowych oraz kompleksowej analizy danych.",
            location="Polska"
        )

    experiences = Experience.objects.all().order_by('-is_current', '-start_date', '-id')
    educations = Education.objects.all().order_by('order', '-id')
    skills = Skill.objects.all().order_by('order', 'category', 'name')
    languages = Language.objects.all().order_by('order', 'name')
    certificates = Certificate.objects.all().order_by('order', '-id')
    projects = Project.objects.all().order_by('order', '-id')
    hobbies = Hobby.objects.all().order_by('order', 'name')

    # Grupowanie umiejętności po kategoriach
    skills_by_category = {}
    for skill in skills:
        cat = skill.category or 'Inne'
        if cat not in skills_by_category:
            skills_by_category[cat] = []
        skills_by_category[cat].append(skill)

    context = {
        'profile': profile,
        'experiences': experiences,
        'educations': educations,
        'skills_by_category': skills_by_category,
        'skills': skills,
        'languages': languages,
        'certificates': certificates,
        'projects': projects,
        'hobbies': hobbies,
        'active_cv': True
    }
    return render(request, 'portfolio/cv.html', context)


@login_required
def cv_profile_update(request):
    """Aktualizacja danych profilowych i nagłówka CV."""
    if request.method != 'POST':
        return redirect('cv_view')
    
    profile = CVProfile.objects.first()
    if not profile:
        profile = CVProfile()

    profile.full_name = request.POST.get('full_name', profile.full_name).strip()
    profile.title = request.POST.get('title', profile.title).strip()
    profile.summary = request.POST.get('summary', profile.summary).strip()
    profile.email = request.POST.get('email', '').strip()
    profile.phone = request.POST.get('phone', '').strip()
    profile.location = request.POST.get('location', '').strip()
    profile.linkedin = request.POST.get('linkedin', '').strip()
    profile.github = request.POST.get('github', '').strip()
    profile.website = request.POST.get('website', '').strip()

    if 'avatar' in request.FILES:
        profile.avatar = request.FILES['avatar']

    profile.save()
    messages.success(request, 'Dane profilowe CV zostały pomyślnie zaktualizowane!')
    return redirect('cv_view')


@login_required
def cv_experience_save(request, pk=None):
    """Dodawanie lub edycja pozycji doświadczenia zawodowego."""
    if request.method != 'POST':
        return redirect('cv_view')
    
    if pk:
        exp = get_object_or_404(Experience, pk=pk)
    else:
        exp = Experience()

    exp.job_title = request.POST.get('job_title', '').strip()
    exp.company = request.POST.get('company', '').strip()
    exp.location = request.POST.get('location', '').strip()
    
    start_date_raw = request.POST.get('start_date', '').strip()
    end_date_raw = request.POST.get('end_date', '').strip()
    is_current = bool(request.POST.get('is_current'))

    exp.is_current = is_current
    exp.start_date = start_date_raw if start_date_raw else None
    exp.end_date = None if (is_current or not end_date_raw) else end_date_raw
    exp.description = request.POST.get('description', '').strip()

    if exp.job_title and exp.company:
        exp.save()
        messages.success(request, 'Doświadczenie zawodowe zostało zapisane!')
    else:
        messages.error(request, 'Podaj przynajmniej stanowisko i nazwę firmy.')

    return redirect('cv_view')


@login_required
def cv_experience_delete(request, pk):
    """Usunięcie pozycji doświadczenia zawodowego."""
    if request.method == 'POST':
        exp = get_object_or_404(Experience, pk=pk)
        exp.delete()
        messages.success(request, 'Pozycja doświadczenia została usunięta.')
    return redirect('cv_view')


@login_required
def cv_education_save(request, pk=None):
    """Dodawanie lub edycja edukacji."""
    if request.method != 'POST':
        return redirect('cv_view')

    if pk:
        edu = get_object_or_404(Education, pk=pk)
    else:
        edu = Education()

    edu.school = request.POST.get('school', '').strip()
    edu.degree = request.POST.get('degree', '').strip()
    edu.field_of_study = request.POST.get('field_of_study', '').strip()
    edu.years = request.POST.get('years', '').strip()
    edu.description = request.POST.get('description', '').strip()

    if edu.school and edu.degree:
        edu.save()
        messages.success(request, 'Informacje o edukacji zostały zapisane!')
    else:
        messages.error(request, 'Podaj nazwę uczelni/szkoły i uzyskany stopień.')

    return redirect('cv_view')


@login_required
def cv_education_delete(request, pk):
    """Usunięcie pozycji edukacji."""
    if request.method == 'POST':
        edu = get_object_or_404(Education, pk=pk)
        edu.delete()
        messages.success(request, 'Wpis edukacji został usunięty.')
    return redirect('cv_view')


@login_required
def cv_skill_add(request):
    """Dodanie nowej umiejętności."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'Umiejętności techniczne').strip()
        try:
            level = int(request.POST.get('level', 5))
        except (ValueError, TypeError):
            level = 5

        if name:
            Skill.objects.create(name=name, category=category, level=level)
            messages.success(request, f'Dodano umiejętność: {name}')
    return redirect('cv_view')


@login_required
def cv_skill_delete(request, pk):
    """Usunięcie umiejętności."""
    if request.method == 'POST':
        skill = get_object_or_404(Skill, pk=pk)
        skill.delete()
        messages.success(request, 'Umiejętność została usunięta.')
    return redirect('cv_view')


@login_required
def cv_language_add(request):
    """Dodanie języka obcego."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        level = request.POST.get('level', 'B2').strip()
        if name:
            Language.objects.create(name=name, level=level)
            messages.success(request, f'Dodano język: {name}')
    return redirect('cv_view')


@login_required
def cv_language_delete(request, pk):
    """Usunięcie języka."""
    if request.method == 'POST':
        lang = get_object_or_404(Language, pk=pk)
        lang.delete()
        messages.success(request, 'Język został usunięty.')
    return redirect('cv_view')


@login_required
def cv_certificate_add(request):
    """Dodanie certyfikatu / kursu."""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        issuer = request.POST.get('issuer', '').strip()
        year = request.POST.get('year', '').strip()
        if title:
            Certificate.objects.create(title=title, issuer=issuer, year=year)
            messages.success(request, f'Dodano certyfikat: {title}')
    return redirect('cv_view')


@login_required
def cv_certificate_delete(request, pk):
    """Usunięcie certyfikatu."""
    if request.method == 'POST':
        cert = get_object_or_404(Certificate, pk=pk)
        cert.delete()
        messages.success(request, 'Certyfikat został usunięty.')
    return redirect('cv_view')


@login_required
def cv_project_save(request, pk=None):
    """Dodawanie lub edycja projektu."""
    if request.method != 'POST':
        return redirect('cv_view')

    if pk:
        project = get_object_or_404(Project, pk=pk)
    else:
        project = Project()

    project.title = request.POST.get('title', '').strip()
    project.role = request.POST.get('role', '').strip()
    project.technologies = request.POST.get('technologies', '').strip()
    project.url = request.POST.get('url', '').strip()
    project.description = request.POST.get('description', '').strip()

    if project.title:
        project.save()
        messages.success(request, f'Projekt "{project.title}" został zapisany!')
    else:
        messages.error(request, 'Podaj nazwę projektu.')

    return redirect('cv_view')


@login_required
def cv_project_delete(request, pk):
    """Usunięcie projektu."""
    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk)
        project.delete()
        messages.success(request, 'Projekt został usunięty.')
    return redirect('cv_view')


@login_required
def cv_hobby_add(request):
    """Dodanie nowego hobby / zainteresowania."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        icon = request.POST.get('icon', '🎮').strip()
        if name:
            Hobby.objects.create(name=name, icon=icon)
            messages.success(request, f'Dodano hobby: {name}')
    return redirect('cv_view')


@login_required
def cv_hobby_delete(request, pk):
    """Usunięcie hobby."""
    if request.method == 'POST':
        hobby = get_object_or_404(Hobby, pk=pk)
        hobby.delete()
        messages.success(request, 'Hobby zostało usunięte.')
    return redirect('cv_view')