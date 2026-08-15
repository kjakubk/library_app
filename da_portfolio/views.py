import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Max, Q
from .models import Game, Publisher, Market, Genre, Platform, StockMetric


@login_required
def game_market_view(request):
    """Główny widok dashboardu analitycznego rynku gamingowego."""
    search_query = request.GET.get('q', '').strip()
    selected_market = request.GET.get('market', '').strip()
    selected_genre = request.GET.get('genre', '').strip()

    # 1. Podstawowe metryki KPI
    total_games = Game.objects.count()
    total_publishers = Publisher.objects.count()
    total_markets = Market.objects.count()
    
    avg_rating_aggregate = Game.objects.filter(rating__isnull=False, rating__gt=0).aggregate(avg_score=Avg('rating'))
    avg_rating = round(avg_rating_aggregate['avg_score'] or 0, 1)

    total_stock_metrics = StockMetric.objects.count()

    # 2. Gry z filtrami
    games_qs = Game.objects.select_related('publisher', 'publisher__market').prefetch_related('genres', 'platforms')
    
    if search_query:
        games_qs = games_qs.filter(
            Q(title__icontains=search_query) |
            Q(publisher__name__icontains=search_query) |
            Q(publisher__ticker__icontains=search_query)
        )
    
    if selected_market:
        games_qs = games_qs.filter(publisher__market__name=selected_market)
        
    if selected_genre:
        games_qs = games_qs.filter(genres__name=selected_genre)

    top_games = games_qs.filter(rating__isnull=False).order_by('-rating', '-release_date')[:15]

    # 3. Wydawcy i podział geograficzny
    publishers = Publisher.objects.select_related('market').annotate(games_count=Count('games')).order_by('-games_count', 'name')

    # 4. Agregacje do wykresów (Chart.js)
    # A. Gatunki gier
    genre_distribution = Genre.objects.annotate(count=Count('games')).filter(count__gt=0).order_by('-count')[:8]
    genre_labels = [g.name for g in genre_distribution]
    genre_data = [g.count for g in genre_distribution]

    # B. Rynki geograficzne
    market_distribution = Market.objects.annotate(pub_count=Count('publishers'), games_count=Count('publishers__games')).order_by('-pub_count')
    market_labels = [m.name for m in market_distribution]
    market_pub_data = [m.pub_count for m in market_distribution]
    market_games_data = [m.games_count for m in market_distribution]

    # Dostępne filtry
    available_markets = Market.objects.all().order_by('name')
    available_genres = Genre.objects.annotate(count=Count('games')).filter(count__gt=0).order_by('name')

    context = {
        'total_games': total_games,
        'total_publishers': total_publishers,
        'total_markets': total_markets,
        'avg_rating': avg_rating,
        'total_stock_metrics': total_stock_metrics,
        'top_games': top_games,
        'publishers': publishers[:12],
        'all_publishers_count': publishers.count(),
        'available_markets': available_markets,
        'available_genres': available_genres,
        'selected_market': selected_market,
        'selected_genre': selected_genre,
        'search_query': search_query,
        # JSON dla Chart.js
        'genre_labels_json': json.dumps(genre_labels),
        'genre_data_json': json.dumps(genre_data),
        'market_labels_json': json.dumps(market_labels),
        'market_pub_data_json': json.dumps(market_pub_data),
        'market_games_data_json': json.dumps(market_games_data),
    }

    return render(request, 'da_portfolio/game_market.html', context)