"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings              # <--- Tego brakowało!
from django.conf.urls.static import static
from portfolio import views as portfolio_views  # Importujemy widoki z portfolio

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', portfolio_views.home_view, name='home'), # <--- Strona główna
    path('kolekcje/',include('library.urls')), #łączenie routingu apki
    path('cv/', include('portfolio.urls')), # <--- Nowa linijka dla CV
]
# Dodajemy obsługę plików z folderu media


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)