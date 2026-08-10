from django.shortcuts import render
from .models import Experience
from django.shortcuts import render, redirect,get_object_or_404
from .models import Photo, Album
from .forms import PhotoForm,AlbumForm

def portfolio_gallery(request):
    selected_album = request.GET.get('album', '')
    albums = Album.objects.all()
    
    if selected_album:
        photos = Photo.objects.filter(album__id=selected_album).order_by('-uploaded_at')
    else:
        photos = Photo.objects.all().order_by('-uploaded_at')

    context = {
        'photos': photos,
        'albums': albums,
        'selected_album': int(selected_album) if selected_album else '',
    }
    return render(request, 'portfolio/gallery.html', context)

def add_photo(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('portfolio_gallery')
    else:
        form = PhotoForm()
    
    return render(request, 'portfolio/add_photo.html', {'form': form})

def add_album(request):
    if request.method == 'POST':
        form = AlbumForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('portfolio_gallery') # Po zapisaniu wracamy do galerii
    else:
        form = AlbumForm()
    
    return render(request, 'portfolio/add_album.html', {'form': form})

def delete_photo(request, pk):
    photo = get_object_or_404(Photo, pk=pk)
    if request.method == 'POST':
        photo.delete()
        return redirect('portfolio_gallery')
    return redirect('portfolio_gallery')

def cv_view(request):
    # Prosty widok renderujący statyczny szablon CV
    return render(request, 'portfolio/cv.html')

def home_view(request):
    return render(request, 'portfolio/home.html')