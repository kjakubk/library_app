import csv
import json
import ssl
import io
import re
import urllib.request
import requests

from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import BookForm, CSVImportForm, VinylRecordForm, PorcelainForm, BoardGameForm, VideoGameForm, ConsoleHardwareForm, AntiqueForm, DigitalGameForm
from .models import BoardGame, Book, Porcelain, VideoGame, VinylRecord, ConsoleHardware, Antique, DigitalGame, CATEGORY_CHOICES
from .book_services import (
    get_unified_book_data, 
    download_and_save_book_cover, 
    find_best_cover_for_book,
    find_cover_in_google_books,
    find_cover_in_openlibrary_cdn,
    find_cover_in_openlibrary_search,
    find_cover_in_wolne_lektury,
    get_all_isbn_variants
)


# ==========================================
# 1. PORCELANA
# ==========================================

@login_required
def porcelain_list(request):
    """Lista elementów porcelany z wyszukiwarką, filtrami i sortowaniem."""
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'name')
    selected_style = request.GET.get('style', '').strip()
    selected_signature = request.GET.get('signature', '').strip()
    
    items = Porcelain.objects.all()

    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(signature__icontains=query) |
            Q(style__icontains=query)
        )

    if selected_style:
        items = items.filter(style=selected_style)

    if selected_signature:
        items = items.filter(signature=selected_signature)

    sort_mapping = {
        'name': 'name',
        '-name': '-name',
        'signature': 'signature',
        '-signature': '-signature',
        'condition': 'condition',
        '-condition': '-condition',
    }
    
    if sort_by in sort_mapping:
        items = items.order_by(sort_mapping[sort_by])

    # Optymalizacja: jedno zapytanie agregujące zamiast wielu `.count()`
    aggregates = Porcelain.objects.aggregate(
        total_collection_count=Count('id'),
        items_with_sig_photos=Count('id', filter=~Q(signature_image__isnull=True) & ~Q(signature_image__exact='')),
        cups_count=Count('id', filter=Q(name__icontains='filiżan') | Q(name__icontains='kubek')),
        saucers_count=Count('id', filter=Q(name__icontains='spodek') | Q(name__icontains='podstawek')),
        plates_count=Count('id', filter=Q(name__icontains='talerz'))
    )

    total_collection_count = aggregates['total_collection_count']
    items_with_sig_photos = aggregates['items_with_sig_photos']
    cups_count = aggregates['cups_count']
    saucers_count = aggregates['saucers_count']
    plates_count = aggregates['plates_count']

    available_styles = list(Porcelain.objects.exclude(style__isnull=True).exclude(style__exact='').values_list('style', flat=True).distinct().order_by('style'))
    available_signatures = list(Porcelain.objects.exclude(signature__isnull=True).exclude(signature__exact='').values_list('signature', flat=True).distinct().order_by('signature'))

    total_signatures_count = len(available_signatures)
    total_styles_count = len(available_styles)
    
    photo_coverage_pct = round((items_with_sig_photos / total_collection_count) * 100, 1) if total_collection_count else 0

    raw_name_stats = Porcelain.objects.values('name').annotate(count=Count('id')).order_by('-count')[:6]
    name_stats = [{'name': s['name'], 'count': s['count'], 'pct': round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0} for s in raw_name_stats]

    raw_sig_stats = Porcelain.objects.exclude(signature__isnull=True).exclude(signature__exact='').values('signature').annotate(count=Count('id')).order_by('-count')[:6]
    signature_stats = [{'signature': s['signature'], 'count': s['count'], 'pct': round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0} for s in raw_sig_stats]

    top_signature = signature_stats[0]['signature'] if signature_stats else '—'
    top_style = available_styles[0] if available_styles else '—'

    sets_count = min(cups_count, saucers_count)

    condition_stats = Porcelain.objects.exclude(condition__isnull=True).exclude(condition__exact='').values('condition').annotate(count=Count('id')).order_by('-count')
    
    total_count = items.count()

    context = {
        'items': items,
        'name_stats': name_stats,
        'signature_stats': signature_stats,
        'condition_stats': condition_stats,
        'total_collection_count': total_collection_count,
        'total_signatures_count': total_signatures_count,
        'total_styles_count': total_styles_count,
        'items_with_sig_photos': items_with_sig_photos,
        'photo_coverage_pct': photo_coverage_pct,
        'top_signature': top_signature,
        'top_style': top_style,
        'cups_count': cups_count,
        'saucers_count': saucers_count,
        'plates_count': plates_count,
        'sets_count': sets_count,
        'total_count': total_count,
        'current_sort': sort_by,
        'available_styles': available_styles,
        'available_signatures': available_signatures,
        'selected_style': selected_style,
        'selected_signature': selected_signature,
    }
    return render(request, 'library/porcelain_list.html', context)


@login_required
def porcelain_create(request):
    """Dodawanie nowego elementu porcelany (z opcją szybkiego kopiowania ze wzorca)."""
    copy_from_id = request.GET.get('copy_from') or request.POST.get('copy_from')
    template_item = None

    if copy_from_id:
        try:
            template_item = Porcelain.objects.get(pk=copy_from_id)
        except Porcelain.DoesNotExist:
            pass

    if request.method == 'POST':
        form = PorcelainForm(request.POST, request.FILES)
        if form.is_valid():
            saved_item = form.save(commit=False)

            # Jeśli kopiowano ze wzorca i użytkownik nie wgrał nowych plików, przenosimy zdjęcia ze wzorca
            if template_item:
                if not saved_item.signature_image and template_item.signature_image:
                    saved_item.signature_image = template_item.signature_image
                if not saved_item.image_1 and template_item.image_1:
                    saved_item.image_1 = template_item.image_1
                if not saved_item.image_2 and template_item.image_2:
                    saved_item.image_2 = template_item.image_2
                if not saved_item.image_3 and template_item.image_3:
                    saved_item.image_3 = template_item.image_3

            saved_item.save()
            action = request.POST.get('action', '')

            if action == 'save_and_clone':
                messages.success(request, f'Pomyślnie zapisano „{saved_item.name}”. Formularz przygotowany do dodania kolejnego elementu z tej serii!')
                return redirect(f"{reverse('porcelain_create')}?copy_from={saved_item.pk}")
            else:
                messages.success(request, 'Pomyślnie dodano nowy element porcelany!')
                return redirect('porcelain_list')
    else:
        if template_item:
            initial_data = {
                'name': template_item.name,
                'style': template_item.style,
                'year_of_origin': template_item.year_of_origin,
                'condition': template_item.condition,
                'price': template_item.price,
            }
            form = PorcelainForm(initial=initial_data, instance=Porcelain(signature=template_item.signature))
        else:
            form = PorcelainForm()
        
    return render(request, 'library/porcelain_form.html', {
        'form': form, 
        'is_copied': bool(template_item),
        'template_item': template_item
    })


@login_required
def porcelain_duplicate(request, pk):
    """Szybkie powielenie (klonowanie) istniejącego elementu porcelany N razy ze wszystkimi zdjęciami i bez numerowania."""
    item = get_object_or_404(Porcelain, pk=pk)

    if request.method == 'POST':
        try:
            copies = int(request.POST.get('copies_count', 1))
        except (ValueError, TypeError):
            copies = 1

        copies = max(1, min(copies, 50)) # Limit od 1 do 50 kopii naraz

        for _ in range(copies):
            Porcelain.objects.create(
                name=item.name, # Dokładnie ta sama nazwa bez dodatkowego numerowania
                style=item.style,
                signature=item.signature,
                year_of_origin=item.year_of_origin,
                condition=item.condition,
                price=item.price,
                signature_image=item.signature_image,
                image_1=item.image_1,
                image_2=item.image_2,
                image_3=item.image_3
            )

        if copies == 1:
            messages.success(request, f'Pomyślnie skopiowano element „{item.name}” (wraz ze wszystkimi zdjęciami).')
        else:
            messages.success(request, f'Pomyślnie utworzono {copies} identycznych sztuk elementu „{item.name}” (wraz ze wszystkimi zdjęciami)!')

        return redirect('porcelain_list')

    # W przypadku GET przekierowujemy do formularza z pre-filled danymi
    return redirect(f"{reverse('porcelain_create')}?copy_from={item.pk}")


@login_required
def porcelain_edit(request, pk):
    """Edycja elementu porcelany z opcją usuwania pojedynczych zdjęć i szybkiego powielania."""
    item = get_object_or_404(Porcelain, pk=pk)
    
    delete_img_field = request.GET.get('delete_img')
    if delete_img_field in ['signature_image', 'image_1', 'image_2', 'image_3']:
        image_field = getattr(item, delete_img_field, None)
        if image_field:
            image_field.delete(save=False)
            setattr(item, delete_img_field, None)
            item.save()
            messages.success(request, 'Zdjęcie zostało pomyślnie usunięte.')
            return redirect('porcelain_edit', pk=item.pk)

    if request.method == 'POST':
        form = PorcelainForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            saved_item = form.save()
            action = request.POST.get('action', '')

            if action == 'save_and_clone':
                messages.success(request, f'Zapisano zmiany w „{saved_item.name}”. Formularz przygotowany do dodania kolejnego elementu z tej serii!')
                return redirect(f"{reverse('porcelain_create')}?copy_from={saved_item.pk}")
            else:
                messages.success(request, 'Zmiany w elemencie porcelany zostały pomyślnie zapisane.')
                return redirect('porcelain_list')
    else:
        form = PorcelainForm(instance=item)
    
    return render(request, 'library/porcelain_form.html', {'form': form, 'item': item})


@login_required
def porcelain_delete(request, pk):
    """Usuwanie elementu porcelany."""
    item = get_object_or_404(Porcelain, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Element porcelany został pomyślnie usunięty z kolekcji.')
        return redirect('porcelain_list')
    
    return render(request, 'library/porcelain_confirm_delete.html', {'item': item})


# ==========================================
# 2. PŁYTY WINYLOWE
# ==========================================

@login_required
def vinyl_list(request):
    """Lista płyt winylowych z wyszukiwaniem, filtrowaniem i bogatymi statystykami."""
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'artist')
    selected_genre = request.GET.get('genre', '').strip()
    
    all_items = VinylRecord.objects.all()
    items = all_items

    if query:
        items = items.filter(
            Q(artist__icontains=query) |
            Q(title__icontains=query) |
            Q(label__icontains=query)
        )

    if selected_genre:
        items = items.filter(genre=selected_genre)

    sort_mapping = {
        'artist': 'artist',
        '-artist': '-artist',
        'title': 'title',
        '-title': '-title',
        'release_year': 'release_year',
        '-release_year': '-release_year',
        'condition': 'condition',
        '-condition': '-condition',
    }
    
    if sort_by in sort_mapping:
        items = items.order_by(sort_mapping[sort_by])

    total_collection_count = all_items.count()
    available_genres = VinylRecord.objects.exclude(genre__isnull=True).exclude(genre__exact='').values_list('genre', flat=True).distinct().order_by('genre')
    available_artists = VinylRecord.objects.exclude(artist__isnull=True).exclude(artist__exact='').values_list('artist', flat=True).distinct().order_by('artist')

    total_genres_count = available_genres.count()
    total_artists_count = available_artists.count()
    items_with_covers = all_items.filter(
        (Q(front_cover__isnull=False) & ~Q(front_cover='')) |
        (Q(back_cover__isnull=False) & ~Q(back_cover=''))
    ).count()
    photo_coverage_pct = round((items_with_covers / total_collection_count) * 100, 1) if total_collection_count else 0

    raw_genre_stats = VinylRecord.objects.exclude(genre__isnull=True).exclude(genre__exact='').values('genre').annotate(count=Count('id')).order_by('-count')[:6]
    genre_stats = []
    for s in raw_genre_stats:
        pct = round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0
        genre_stats.append({'genre': s['genre'], 'count': s['count'], 'pct': pct})

    raw_artist_stats = VinylRecord.objects.exclude(artist__isnull=True).exclude(artist__exact='').values('artist').annotate(count=Count('id')).order_by('-count')[:6]
    artist_stats = []
    for s in raw_artist_stats:
        pct = round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0
        artist_stats.append({'artist': s['artist'], 'count': s['count'], 'pct': pct})

    top_genre = genre_stats[0]['genre'] if genre_stats else '—'
    top_artist = artist_stats[0]['artist'] if artist_stats else '—'

    total_count = items.count()

    context = {
        'items': items,
        'artist_stats': artist_stats,
        'genre_stats': genre_stats,
        'total_collection_count': total_collection_count,
        'total_artists_count': total_artists_count,
        'total_genres_count': total_genres_count,
        'items_with_covers': items_with_covers,
        'photo_coverage_pct': photo_coverage_pct,
        'top_artist': top_artist,
        'top_genre': top_genre,
        'total_count': total_count,
        'current_sort': sort_by,
        'available_genres': available_genres,
        'selected_genre': selected_genre,
    }
    return render(request, 'library/vinyl_list.html', context)


@login_required
def vinyl_create(request):
    """Dodawanie nowej płyty winylowej."""
    if request.method == 'POST':
        form = VinylRecordForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Płyta winylowa została pomyślnie dodana!')
            return redirect('vinyl_list')
    else:
        form = VinylRecordForm()
    
    return render(request, 'library/vinyl_form.html', {'form': form, 'is_edit': False})


@login_required
def vinyl_edit(request, pk):
    """Edycja płyty winylowej."""
    item = get_object_or_404(VinylRecord, pk=pk)
    if request.method == 'POST':
        form = VinylRecordForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zaktualizowano dane płyty winylowej.')
            return redirect('vinyl_list')
    else:
        form = VinylRecordForm(instance=item)
    
    return render(request, 'library/vinyl_form.html', {'form': form, 'item': item, 'is_edit': True})


@login_required
def vinyl_delete(request, pk):
    """Usuwanie płyty winylowej."""
    item = get_object_or_404(VinylRecord, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Płyta winylowa została usunięta.')
        return redirect('vinyl_list')
    return redirect('vinyl_list')


# ==========================================
# 3. GRY WIDEO
# ==========================================

@login_required
def video_game_list(request):
    """Lista gier wideo z filtrowaniem i bogatymi statystykami."""
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'title')
    selected_platform = request.GET.get('platform', '').strip()
    selected_genre = request.GET.get('genre', '').strip()
    
    all_items = VideoGame.objects.all()
    items = all_items

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(developer__icontains=query) |
            Q(publisher__icontains=query) |
            Q(genre__icontains=query)
        )

    if selected_platform:
        items = items.filter(platform=selected_platform)

    if selected_genre:
        items = items.filter(genre=selected_genre)

    sort_mapping = {
        'title': 'title', '-title': '-title',
        'platform': 'platform', '-platform': '-platform',
        'release_year': 'release_year', '-release_year': '-release_year',
        'condition': 'condition', '-condition': '-condition',
    }
    
    if sort_by in sort_mapping:
        items = items.order_by(sort_mapping[sort_by])

    total_collection_count = all_items.count()
    available_platforms = VideoGame.objects.exclude(platform__isnull=True).exclude(platform__exact='').values_list('platform', flat=True).distinct().order_by('platform')
    available_genres = VideoGame.objects.exclude(genre__isnull=True).exclude(genre__exact='').values_list('genre', flat=True).distinct().order_by('genre')

    total_platforms_count = available_platforms.count()
    total_genres_count = available_genres.count()
    items_with_covers = all_items.filter(
        (Q(cover_image__isnull=False) & ~Q(cover_image='')) |
        (Q(media_image__isnull=False) & ~Q(media_image=''))
    ).count()
    photo_coverage_pct = round((items_with_covers / total_collection_count) * 100, 1) if total_collection_count else 0

    raw_platform_stats = VideoGame.objects.exclude(platform__isnull=True).exclude(platform__exact='').values('platform').annotate(count=Count('id')).order_by('-count')[:6]
    platform_stats = []
    for s in raw_platform_stats:
        pct = round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0
        platform_stats.append({'platform': s['platform'], 'count': s['count'], 'pct': pct})

    raw_genre_stats = VideoGame.objects.exclude(genre__isnull=True).exclude(genre__exact='').values('genre').annotate(count=Count('id')).order_by('-count')[:6]
    genre_stats = []
    for s in raw_genre_stats:
        pct = round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0
        genre_stats.append({'genre': s['genre'], 'count': s['count'], 'pct': pct})

    top_platform = platform_stats[0]['platform'] if platform_stats else '—'
    top_genre = genre_stats[0]['genre'] if genre_stats else '—'

    total_count = items.count()

    context = {
        'items': items,
        'platform_stats': platform_stats,
        'genre_stats': genre_stats,
        'total_collection_count': total_collection_count,
        'total_platforms_count': total_platforms_count,
        'total_genres_count': total_genres_count,
        'items_with_covers': items_with_covers,
        'photo_coverage_pct': photo_coverage_pct,
        'top_platform': top_platform,
        'top_genre': top_genre,
        'total_count': total_count,
        'current_sort': sort_by,
        'available_platforms': available_platforms,
        'available_genres': available_genres,
        'selected_platform': selected_platform,
        'selected_genre': selected_genre,
    }
    return render(request, 'library/video_game_list.html', context)


@login_required
def video_game_create(request):
    """Dodawanie nowej gry wideo."""
    if request.method == 'POST':
        form = VideoGameForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gra wideo została dodana do kolekcji!')
            return redirect('video_game_list')
    else:
        form = VideoGameForm()
    
    return render(request, 'library/video_game_form.html', {'form': form, 'is_edit': False})


@login_required
def video_game_edit(request, pk):
    """Edycja gry wideo."""
    item = get_object_or_404(VideoGame, pk=pk)
    if request.method == 'POST':
        form = VideoGameForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zaktualizowano dane gry.')
            return redirect('video_game_list')
    else:
        form = VideoGameForm(instance=item)
    
    return render(request, 'library/video_game_form.html', {'form': form, 'item': item, 'is_edit': True})


@login_required
def video_game_delete(request, pk):
    """Usuwanie gry wideo."""
    item = get_object_or_404(VideoGame, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Gra została usunięta z kolekcji.')
        return redirect('video_game_list')
    return redirect('video_game_list')


# ==========================================
# 4. GRY PLANSZOWE
# ==========================================

@login_required
def board_game_list(request):
    """Lista gier planszowych z filtrowaniem i bogatymi statystykami."""
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'title')
    selected_category = request.GET.get('category', '').strip()
    selected_publisher = request.GET.get('publisher', '').strip()
    
    all_items = BoardGame.objects.all()
    items = all_items

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(publisher__icontains=query) |
            Q(category__icontains=query)
        )

    if selected_category:
        items = items.filter(category=selected_category)

    if selected_publisher:
        items = items.filter(publisher=selected_publisher)

    sort_mapping = {
        'title': 'title', '-title': '-title',
        'publisher': 'publisher', '-publisher': '-publisher',
        'release_year': 'release_year', '-release_year': '-release_year',
        'condition': 'condition', '-condition': '-condition',
    }
    
    if sort_by in sort_mapping:
        items = items.order_by(sort_mapping[sort_by])

    total_collection_count = all_items.count()
    available_categories = BoardGame.objects.exclude(category__isnull=True).exclude(category__exact='').values_list('category', flat=True).distinct().order_by('category')
    available_publishers = BoardGame.objects.exclude(publisher__isnull=True).exclude(publisher__exact='').values_list('publisher', flat=True).distinct().order_by('publisher')

    total_categories_count = available_categories.count()
    total_publishers_count = available_publishers.count()
    items_with_covers = all_items.filter(
        (Q(box_image__isnull=False) & ~Q(box_image='')) |
        (Q(board_image__isnull=False) & ~Q(board_image=''))
    ).count()
    photo_coverage_pct = round((items_with_covers / total_collection_count) * 100, 1) if total_collection_count else 0

    raw_category_stats = BoardGame.objects.exclude(category__isnull=True).exclude(category__exact='').values('category').annotate(count=Count('id')).order_by('-count')[:6]
    category_stats = []
    for s in raw_category_stats:
        pct = round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0
        category_stats.append({'category': s['category'], 'count': s['count'], 'pct': pct})

    raw_pub_stats = BoardGame.objects.exclude(publisher__isnull=True).exclude(publisher__exact='').values('publisher').annotate(count=Count('id')).order_by('-count')[:6]
    publisher_stats = []
    for s in raw_pub_stats:
        pct = round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0
        publisher_stats.append({'publisher': s['publisher'], 'count': s['count'], 'pct': pct})

    top_category = category_stats[0]['category'] if category_stats else '—'
    top_publisher = publisher_stats[0]['publisher'] if publisher_stats else '—'

    total_count = items.count()

    context = {
        'items': items,
        'category_stats': category_stats,
        'publisher_stats': publisher_stats,
        'total_collection_count': total_collection_count,
        'total_categories_count': total_categories_count,
        'total_publishers_count': total_publishers_count,
        'items_with_covers': items_with_covers,
        'photo_coverage_pct': photo_coverage_pct,
        'top_category': top_category,
        'top_publisher': top_publisher,
        'total_count': total_count,
        'current_sort': sort_by,
        'available_categories': available_categories,
        'available_publishers': available_publishers,
        'selected_category': selected_category,
        'selected_publisher': selected_publisher,
    }
    return render(request, 'library/board_game_list.html', context)


@login_required
def board_game_create(request):
    """Dodawanie nowej gry planszowej."""
    if request.method == 'POST':
        form = BoardGameForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gra planszowa została dodana do kolekcji!')
            return redirect('board_game_list')
    else:
        form = BoardGameForm()
    
    return render(request, 'library/board_game_form.html', {'form': form, 'is_edit': False})


@login_required
def board_game_edit(request, pk):
    """Edycja gry planszowej."""
    item = get_object_or_404(BoardGame, pk=pk)
    if request.method == 'POST':
        form = BoardGameForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zaktualizowano dane gry planszowej.')
            return redirect('board_game_list')
    else:
        form = BoardGameForm(instance=item)
    
    return render(request, 'library/board_game_form.html', {'form': form, 'item': item, 'is_edit': True})


@login_required
def board_game_delete(request, pk):
    """Usuwanie gry planszowej."""
    item = get_object_or_404(BoardGame, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Gra planszowa została usunięta.')
        return redirect('board_game_list')
    return redirect('board_game_list')


# ==========================================
# 5. KSIĄŻKI & SMART ENGINE
# ==========================================

@login_required
def book_list(request):
    """Lista książek z grupowaniem alfabetycznym, wyszukiwaniem i zaawansowanymi statystykami."""
    query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()
    selected_status = request.GET.get('status', '').strip()
    
    all_books = Book.objects.all()
    books = all_books.order_by('title')
    
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(authors__icontains=query) |
            Q(publisher__icontains=query) |
            Q(isbn__icontains=query)
        )
        
    if selected_category:
        books = books.filter(categories=selected_category)
        
    if selected_status == 'read':
        books = books.filter(read=True)
    elif selected_status == 'unread':
        books = books.filter(read=False)

    categories_list = [choice[0] for choice in CATEGORY_CHOICES]
    
    # Optymalizacja zapytań o KPI
    aggregates = Book.objects.aggregate(
        total_collection=Count('id'),
        read_books=Count('id', filter=Q(read=True)),
        with_covers=Count('id', filter=~Q(image__isnull=True) & ~Q(image__exact=''))
    )
    
    total_collection_count = aggregates['total_collection']
    read_books_count = aggregates['read_books']
    items_with_covers = aggregates['with_covers']

    total_authors_count = all_books.exclude(authors__isnull=True).exclude(authors__exact='').values('authors').distinct().count()
    total_categories_count = all_books.exclude(categories__isnull=True).exclude(categories__exact='').values('categories').distinct().count()

    read_pct = round((read_books_count / total_collection_count) * 100, 1) if total_collection_count else 0
    photo_coverage_pct = round((items_with_covers / total_collection_count) * 100, 1) if total_collection_count else 0

    raw_cat_stats = all_books.exclude(categories__isnull=True).exclude(categories__exact='').values('categories').annotate(count=Count('id')).order_by('-count')[:6]
    category_stats = [{'category': s['categories'], 'count': s['count'], 'pct': round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0} for s in raw_cat_stats]

    raw_author_stats = all_books.exclude(authors__isnull=True).exclude(authors__exact='').values('authors').annotate(count=Count('id')).order_by('-count')[:6]
    author_stats = [{'author': s['authors'], 'count': s['count'], 'pct': round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0} for s in raw_author_stats]

    top_category = category_stats[0]['category'] if category_stats else '—'
    top_author = author_stats[0]['author'] if author_stats else '—'
    total_count = books.count()
    
    alphabet_groups = {}
    for book in books:
        first_letter = book.title[0].upper() if book.title else '#'
        if first_letter not in alphabet_groups:
            alphabet_groups[first_letter] = []
        alphabet_groups[first_letter].append(book)
    
    grouped_books = [(letter, alphabet_groups[letter]) for letter in sorted(alphabet_groups.keys())]

    context = {
        'grouped_books': grouped_books,
        'books': books,
        'total_count': total_count,
        'total_collection_count': total_collection_count,
        'total_authors_count': total_authors_count,
        'total_categories_count': total_categories_count,
        'read_books_count': read_books_count,
        'read_pct': read_pct,
        'items_with_covers': items_with_covers,
        'photo_coverage_pct': photo_coverage_pct,
        'category_stats': category_stats,
        'author_stats': author_stats,
        'top_category': top_category,
        'top_author': top_author,
        'categories_list': categories_list,
        'selected_category': selected_category,
        'selected_status': selected_status,
    }
    return render(request, 'library/book_list.html', context)


@login_required
def book_detail(request, pk):
    """Szczegółowe informacje o książce."""
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'library/book_detail.html', {'book': book})


@login_required
def book_create(request):
    """Dodawanie nowej książki z inteligentnym pobieraniem okładki."""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        image_url = request.POST.get('cover_url', '').strip()
        
        if form.is_valid():
            isbn_val = form.cleaned_data.get('isbn')
            
            existing_book = Book.objects.filter(isbn=isbn_val).first() if isbn_val else None
                
            if existing_book:
                existing_book.number_of_copies = (existing_book.number_of_copies or 1) + 1
                existing_book.save()
                messages.success(request, f"Książka '{existing_book.title}' już była w bazie. Zwiększono liczbę egzemplarzy do {existing_book.number_of_copies}!")
                return redirect('book_list')
            else:
                book = form.save()
                
                # Jeśli użytkownik nie wgrał ręcznie pliku, a mamy link do okładki -> pobierz ją
                if image_url and not request.FILES.get('image'):
                    download_and_save_book_cover(book, image_url)
                
                messages.success(request, f"Książka '{book.title}' została pomyślnie dodana!")
                return redirect('book_list')
    else:
        form = BookForm()
        image_url = ''
        
    return render(request, 'library/book_form.html', {'form': form, 'cover_url': image_url})


@login_required
def book_edit(request, pk):
    """Edycja książki z możliwością aktualizacji okładki po linku."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        image_url = request.POST.get('cover_url', '').strip()
        
        if form.is_valid():
            book = form.save()
            
            if image_url and not request.FILES.get('image'):
                download_and_save_book_cover(book, image_url)
            
            messages.success(request, 'Zaktualizowano dane książki.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
        image_url = book.image.url if book.image else ''
    
    return render(request, 'library/book_form.html', {'form': form, 'cover_url': image_url, 'book': book})


@login_required
def book_delete(request, pk):
    """Usuwanie książki."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'Książka „{title}” została pomyślnie usunięta z bazy.')
        return redirect('book_list')
    return redirect('book_detail', pk=pk)


@login_required
def book_import_csv(request):
    """
    Import książek z pliku CSV.
    Logika wydzielona do library/import_services.py.
    """
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Nie wybrano pliku CSV.')
            return redirect('book_list')
            
        csv_file = request.FILES['csv_file']
        
        from .import_services import process_csv_import
        imported_count, covers_count, error = process_csv_import(csv_file)
        
        if error:
            if "pusty" in error:
                messages.warning(request, error)
            else:
                messages.error(request, f"Błąd podczas importu CSV: {error}")
        else:
            messages.success(request, f"Sukces! Zaimportowano {imported_count} pozycji (pomyślnie pobrano {covers_count} okładek).")
            
        return redirect('book_list')

    return render(request, 'library/book_import.html')


@login_required
def fetch_book_data(request, isbn):
    """Nowy, zunifikowany endpoint pobierania metadanych i okładek z wielu źródeł."""
    data = get_unified_book_data(isbn)
    if data and (data.get('title') or data.get('cover_url')):
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Nie znaleziono książki w bazach zewnętrznych.'}, status=404)


@login_required
def fix_missing_covers(request):
    """
    Automatycznie skanuje wszystkie książki w bazie bez okładki
    i pobiera je kaskadowo z Open Library CDN, Open Library Search, Google Books Hi-Res oraz Wolnych Lektur.
    """
    books_without_covers = Book.objects.filter(Q(image='') | Q(image__isnull=True))
    fixed_count = 0
    
    for book in books_without_covers:
        cover_url = find_best_cover_for_book(
            isbn=book.isbn, 
            title=book.title, 
            authors=book.authors
        )
        if cover_url:
            saved = download_and_save_book_cover(book, cover_url)
            if saved:
                fixed_count += 1

    messages.success(request, f"Proces zakończony! Zaktualizowano okładki dla {fixed_count} książek.")
    return redirect('book_list')


@login_required
def fix_all_covers(request):
    """Alias do fix_missing_covers."""
    return fix_missing_covers(request)


@login_required
def book_update_progress(request, pk):
    """Aktualizacja liczby przeczytanych stron z poziomu karty szczegółów."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        pages_read_str = request.POST.get('pages_read')
        
        if pages_read_str and pages_read_str.isdigit():
            try:
                pages_read = int(pages_read_str)
                if book.page_count and pages_read > book.page_count:
                    pages_read = book.page_count
                if pages_read < 0:
                    pages_read = 0
                
                book.pages_read = pages_read
                book.read = bool(book.page_count and pages_read >= book.page_count)
                book.save()
                messages.success(request, 'Postęp czytania został zaktualizowany.')
            except ValueError:
                pass
                
    return redirect('book_detail', pk=book.pk)


@login_required
def book_bulk_update(request):
    """Masowa aktualizacja kategorii lub statusu przeczytania dla zaznaczonych książek."""
    if request.method == 'POST':
        selected_ids = request.POST.get('selected_books', '')
        new_category = request.POST.get('new_category', '').strip()
        action_type = request.POST.get('action_type', '')
        
        if not selected_ids:
            messages.warning(request, "Nie wybrano żadnych książek.")
            return redirect('book_list')
            
        id_list = [int(pk) for pk in selected_ids.split(',') if pk.isdigit()]
        books = Book.objects.filter(pk__in=id_list)
        
        if action_type == 'category':
            for book in books:
                if new_category:
                    current_cats = [c.strip() for c in book.categories.split(',')] if book.categories else []
                    if new_category not in current_cats:
                        current_cats.append(new_category)
                        book.categories = ", ".join(current_cats)
                        book.save()
            messages.success(request, f"Pomyślnie zaktualizowano kategorię dla {books.count()} książek!")
            
        elif action_type == 'read_status':
            status_val = request.POST.get('status_val') == 'true'
            books.update(read=status_val)
            messages.success(request, f"Zmieniono status przeczytania dla {books.count()} książek!")
            
    return redirect('book_list')


@login_required
def toggle_book_read(request, pk):
    """Szybka zmiana statusu przeczytania przez AJAX."""
    if request.method == 'POST':
        try:
            book = Book.objects.get(pk=pk)
            book.read = not book.read
            book.save()
            return JsonResponse({'success': True, 'is_read': book.read})
        except Book.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Książka nie istnieje'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


# ==========================================
# 6. KONSOLE I AKCESORIA
# ==========================================

@login_required
def console_list(request):
    query = request.GET.get('q', '').strip()
    items = ConsoleHardware.objects.all()
    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(manufacturer__icontains=query) |
            Q(category__icontains=query)
        )
    items = items.order_by('name')

    aggregates = ConsoleHardware.objects.aggregate(
        total_count=Count('id'),
        with_image=Count('id', filter=~Q(image__isnull=True) & ~Q(image__exact=''))
    )
    
    context = {
        'items': items,
        'query': query,
        'total_count': aggregates['total_count'],
        'with_image': aggregates['with_image'],
    }
    return render(request, 'library/console_list.html', context)

@login_required
def console_create(request):
    if request.method == 'POST':
        form = ConsoleHardwareForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pomyślnie dodano element.')
            return redirect('console_list')
    else:
        form = ConsoleHardwareForm()
    return render(request, 'library/console_form.html', {'form': form, 'title': 'Dodaj konsolę lub akcesorium'})

@login_required
def console_update(request, pk):
    item = get_object_or_404(ConsoleHardware, pk=pk)
    if request.method == 'POST':
        form = ConsoleHardwareForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zaktualizowano pomyślnie.')
            return redirect('console_list')
    else:
        form = ConsoleHardwareForm(instance=item)
    return render(request, 'library/console_form.html', {'form': form, 'title': 'Edytuj konsolę lub akcesorium', 'item': item})

@login_required
def console_delete(request, pk):
    item = get_object_or_404(ConsoleHardware, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Usunięto pomyślnie.')
        return redirect('console_list')
    return redirect('console_list')


# ==========================================
# 7. INNE ANTYKI
# ==========================================

@login_required
def antique_list(request):
    query = request.GET.get('q', '').strip()
    items = Antique.objects.all()
    if query:
        items = items.filter(
            Q(name__icontains=query) |
            Q(material__icontains=query) |
            Q(style__icontains=query)
        )
    items = items.order_by('name')

    aggregates = Antique.objects.aggregate(
        total_count=Count('id'),
        with_image=Count('id', filter=~Q(image__isnull=True) & ~Q(image__exact=''))
    )

    context = {
        'items': items,
        'query': query,
        'total_count': aggregates['total_count'],
        'with_image': aggregates['with_image'],
    }
    return render(request, 'library/antique_list.html', context)

@login_required
def antique_create(request):
    if request.method == 'POST':
        form = AntiqueForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pomyślnie dodano antyk.')
            return redirect('antique_list')
    else:
        form = AntiqueForm()
    return render(request, 'library/antique_form.html', {'form': form, 'title': 'Dodaj antyk'})

@login_required
def antique_update(request, pk):
    item = get_object_or_404(Antique, pk=pk)
    if request.method == 'POST':
        form = AntiqueForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zaktualizowano antyk.')
            return redirect('antique_list')
    else:
        form = AntiqueForm(instance=item)
    return render(request, 'library/antique_form.html', {'form': form, 'title': 'Edytuj antyk', 'item': item})

@login_required
def antique_delete(request, pk):
    item = get_object_or_404(Antique, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Usunięto pomyślnie.')
        return redirect('antique_list')
    return redirect('antique_list')


# ==========================================
# 8. GRY CYFROWE
# ==========================================

def digital_game_list(request):
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'title')
    selected_platform = request.GET.get('platform', '').strip()
    selected_genre = request.GET.get('genre', '').strip()
    
    all_items = DigitalGame.objects.all()
    items = all_items

    if query:
        items = items.filter(
            Q(title__icontains=query) | 
            Q(platform__icontains=query) |
            Q(genre__icontains=query)
        )
    if selected_platform:
        items = items.filter(platform=selected_platform)
    if selected_genre:
        items = items.filter(genre=selected_genre)

    sort_mapping = {
        'title': 'title', '-title': '-title',
        'platform': 'platform', '-platform': '-platform',
        'release_year': 'release_year', '-release_year': '-release_year'
    }
    
    if sort_by in sort_mapping:
        items = items.order_by(sort_mapping[sort_by])
    else:
        items = items.order_by('title')

    # Statistics
    total_collection_count = all_items.count()
    available_platforms = DigitalGame.objects.exclude(platform__isnull=True).exclude(platform__exact='').values_list('platform', flat=True).distinct().order_by('platform')
    available_genres = DigitalGame.objects.exclude(genre__isnull=True).exclude(genre__exact='').values_list('genre', flat=True).distinct().order_by('genre')
    
    total_platforms_count = available_platforms.count()
    total_genres_count = available_genres.count()
    
    items_with_covers = all_items.filter(
        Q(cover_image__isnull=False) & ~Q(cover_image='')
    ).count()
    photo_coverage_pct = round((items_with_covers / total_collection_count) * 100, 1) if total_collection_count else 0
    
    raw_platform_stats = DigitalGame.objects.exclude(platform__isnull=True).exclude(platform__exact='').values('platform').annotate(count=Count('id')).order_by('-count')[:6]
    platform_stats = []
    for s in raw_platform_stats:
        pct = round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0
        platform_stats.append({'platform': s['platform'], 'count': s['count'], 'pct': pct})
        
    top_platform = platform_stats[0]['platform'] if platform_stats else 'Brak'
    
    raw_genre_stats = DigitalGame.objects.exclude(genre__isnull=True).exclude(genre__exact='').values('genre').annotate(count=Count('id')).order_by('-count')[:6]
    genre_stats = []
    for s in raw_genre_stats:
        pct = round((s['count'] / total_collection_count) * 100, 1) if total_collection_count else 0
        genre_stats.append({'genre': s['genre'], 'count': s['count'], 'pct': pct})

    context = {
        'items': items,
        'total_count': items.count(),

        # Dashboard stats
        'total_collection_count': total_collection_count,
        'total_platforms_count': total_platforms_count,
        'total_genres_count': total_genres_count,
        'photo_coverage_pct': photo_coverage_pct,
        'platform_stats': platform_stats,
        'genre_stats': genre_stats,
        'top_platform': top_platform,

        'platforms': available_platforms,
        'genres': available_genres,
        'current_sort': sort_by,
        'active_kolekcje': True
    }
    return render(request, 'library/digital_game_list.html', context)

def digital_game_create(request):
    if request.method == 'POST':
        form = DigitalGameForm(request.POST, request.FILES)
        if form.is_valid():
            game = form.save(commit=False)
            remote_cover_url = request.POST.get('remote_cover_url')
            if remote_cover_url and not request.FILES.get('cover_image'):
                try:
                    resp = requests.get(remote_cover_url, timeout=10)
                    if resp.status_code == 200:
                        file_name = remote_cover_url.split('/')[-1].split('?')[0]
                        if not file_name or '.' not in file_name:
                            file_name = 'cover.jpg'
                        game.cover_image.save(file_name, ContentFile(resp.content), save=False)
                except Exception as e:
                    pass
            game.save()
            messages.success(request, 'Dodano grę cyfrową!')
            return redirect('digital_game_list')
    else:
        form = DigitalGameForm()
    
    return render(request, 'library/digital_game_form.html', {
        'form': form, 
        'is_edit': False,
        'active_kolekcje': True
    })

def digital_game_edit(request, pk):
    item = get_object_or_404(DigitalGame, pk=pk)
    if request.method == 'POST':
        form = DigitalGameForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            game = form.save(commit=False)
            remote_cover_url = request.POST.get('remote_cover_url')
            if remote_cover_url and not request.FILES.get('cover_image'):
                try:
                    resp = requests.get(remote_cover_url, timeout=10)
                    if resp.status_code == 200:
                        file_name = remote_cover_url.split('/')[-1].split('?')[0]
                        if not file_name or '.' not in file_name:
                            file_name = 'cover.jpg'
                        game.cover_image.save(file_name, ContentFile(resp.content), save=False)
                except Exception as e:
                    pass
            game.save()
            messages.success(request, 'Zaktualizowano grę!')
            return redirect('digital_game_list')
    else:
        form = DigitalGameForm(instance=item)
    
    return render(request, 'library/digital_game_form.html', {
        'form': form, 
        'is_edit': True, 
        'item': item,
        'active_kolekcje': True
    })

def digital_game_delete(request, pk):
    item = get_object_or_404(DigitalGame, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Usunięto grę cyfrową.')
        return redirect('digital_game_list')
    return redirect('digital_game_list')

# =======================================================
# STEAM MASS IMPORT
# =======================================================
import json
from django.views.decorators.csrf import csrf_exempt

def steam_fetch_games(request):
    steam_id = request.GET.get('steam_id', '').strip()
    api_key = request.GET.get('api_key', '').strip()
    
    if not steam_id or not api_key:
        return JsonResponse({'error': 'Missing API Key or ID'}, status=400)
        
    is_steam_id64 = steam_id.isdigit() and len(steam_id) == 17 and steam_id.startswith('7656')
    
    if not is_steam_id64:
        vanity_url = f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={api_key}&vanityurl={steam_id}'
        try:
            r = requests.get(vanity_url, timeout=10)
            if r.status_code != 200:
                return JsonResponse({'error': f'Steam API odrzuciło żądanie (Vanity). Status: {r.status_code}'}, status=400)
            data = r.json()
            if data.get('response', {}).get('success') == 1:
                steam_id = data['response']['steamid']
            else:
                return JsonResponse({'error': 'Nie znaleziono profilu Steam o tej nazwie'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Błąd przy sprawdzaniu nazwy: {str(e)}'}, status=500)
            
    owned_games_url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&include_appinfo=1&include_played_free_games=1'
    try:
        r = requests.get(owned_games_url, timeout=15)
        if r.status_code != 200:
            return JsonResponse({'error': f'Steam API zwróciło błąd. Status: {r.status_code}'}, status=400)
        data = r.json()
        games = data.get('response', {}).get('games', [])
        if not games:
            return JsonResponse({'games': []})
            
        existing_titles = set(DigitalGame.objects.filter(platform='Steam').values_list('title', flat=True))
        
        results = []
        for g in games:
            name = g.get('name', 'Unknown')
            if name not in existing_titles:
                results.append({
                    'appid': g.get('appid'),
                    'name': name
                })
        return JsonResponse({'games': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def steam_import_game(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    try:
        data = json.loads(request.body)
        appid = data.get('appid')
        name = data.get('name')
        
        if not appid or not name:
            return JsonResponse({'error': 'Missing data'}, status=400)
            
        if DigitalGame.objects.filter(platform='Steam', title=name).exists():
            return JsonResponse({'status': 'skipped'})
            
        game = DigitalGame(
            title=name,
            platform='Steam',
            is_finished=False
        )
        
        cover_url = f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg'
        try:
            resp = requests.get(cover_url, timeout=10)
            if resp.status_code == 200:
                game.cover_image.save(f'steam_{appid}.jpg', ContentFile(resp.content), save=False)
            else:
                header_url = f'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg'
                resp2 = requests.get(header_url, timeout=10)
                if resp2.status_code == 200:
                    game.cover_image.save(f'steam_{appid}_header.jpg', ContentFile(resp2.content), save=False)
        except Exception:
            pass
            
        game.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def heroic_import(request):
    """Import gier Epic Games lub GOG z pliku JSON z Heroic Games Launcher."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    try:
        data = json.loads(request.body)
        app_name = data.get('app_name', '')
        title = data.get('title', '').strip()
        cover_url = data.get('cover_url', '').strip()
        platform = data.get('platform', 'Epic Games')  # 'Epic Games' lub 'GOG'

        if not title:
            return JsonResponse({'error': 'Missing title'}, status=400)

        existing_game = DigitalGame.objects.filter(platform=platform, title=title).first()

        # If game already exists and has a cover, skip
        if existing_game and existing_game.cover_image:
            return JsonResponse({'status': 'skipped'})

        # Determine target game object
        game = existing_game if existing_game else DigitalGame(
            title=title,
            platform=platform,
            is_finished=False
        )

        if cover_url:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,pl;q=0.8',
                    'Referer': 'https://store.epicgames.com/' if platform == 'Epic Games' else 'https://www.gog.com/',
                }
                resp = requests.get(cover_url, timeout=15, headers=headers, allow_redirects=True)
                if resp.status_code == 200 and len(resp.content) > 500:
                    safe_name = ''.join(c for c in app_name if c.isalnum() or c in '-_')[:50]
                    if not safe_name:
                        safe_name = ''.join(c for c in title if c.isalnum() or c in '-_')[:50]
                    prefix = 'epic' if platform == 'Epic Games' else 'gog'
                    content_type = resp.headers.get('Content-Type', 'image/jpeg')
                    ext = 'png' if ('png' in content_type or cover_url.lower().endswith('.png')) else 'jpg'
                    game.cover_image.save(f'{prefix}_{safe_name}.{ext}', ContentFile(resp.content), save=False)
            except Exception as img_err:
                pass

        game.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def digital_game_bulk_delete(request):
    """Masowe usuwanie gier cyfrowych po liście ID."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            return JsonResponse({'error': 'No IDs provided'}, status=400)
        ids = [int(i) for i in ids if str(i).isdigit()]
        deleted_count, _ = DigitalGame.objects.filter(pk__in=ids).delete()
        return JsonResponse({'deleted': deleted_count})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
