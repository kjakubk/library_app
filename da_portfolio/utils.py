import os
import requests
import yfinance as yf
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import Market, Publisher, Game, Genre, Platform, StockMetric

CLIENT_ID = os.getenv('IGDB_CLIENT_ID', 'gbf6bckx8klifbv43swd7oo0xn1g9e')
CLIENT_SECRET = os.getenv('IGDB_CLIENT_SECRET', 'd98b75be7axxld2sx2c3znn0b720gs')

# Lista 51 globalnych spółek giełdowych z przypisanym Rynkiem
PUBLISHERS_CONFIG = [
    # --- POLSKA (GPW) ---
    {'name': 'CD Projekt', 'ticker': 'CDR.WA', 'market': 'Polska'},
    {'name': 'Ten Square Games', 'ticker': 'TEN.WA', 'market': 'Polska'},
    {'name': '11 bit studios', 'ticker': '11B.WA', 'market': 'Polska'},
    {'name': 'PlayWay', 'ticker': 'PLW.WA', 'market': 'Polska'},
    {'name': 'Creepy Jar', 'ticker': 'CRJ.WA', 'market': 'Polska'},
    {'name': 'CI Games', 'ticker': 'CIG.WA', 'market': 'Polska'},
    {'name': 'People Can Fly', 'ticker': 'PCF.WA', 'market': 'Polska'},
    {'name': 'Huuuge Games', 'ticker': 'HUG.WA', 'market': 'Polska'},
    
    # --- USA ---
    {'name': 'Microsoft', 'ticker': 'MSFT', 'market': 'USA'},
    {'name': 'Electronic Arts', 'ticker': 'EA', 'market': 'USA'},
    {'name': 'Take-Two Interactive', 'ticker': 'TTWO', 'market': 'USA'},
    {'name': 'Roblox', 'ticker': 'RBLX', 'market': 'USA'},
    {'name': 'Playtika', 'ticker': 'PLTK', 'market': 'USA'},
    {'name': 'AppLovin', 'ticker': 'APP', 'market': 'USA'},
    {'name': 'Unity Software', 'ticker': 'U', 'market': 'USA'},
    {'name': 'Warner Bros', 'ticker': 'WBD', 'market': 'USA'},
    
    # --- JAPONIA ---
    {'name': 'Sony', 'ticker': 'SONY', 'market': 'Japonia'},
    {'name': 'Nintendo', 'ticker': 'NTDOY', 'market': 'Japonia'},
    {'name': 'Nexon', 'ticker': '3659.T', 'market': 'Japonia'},
    {'name': 'Square Enix', 'ticker': '9684.T', 'market': 'Japonia'},
    {'name': 'Capcom', 'ticker': '9697.T', 'market': 'Japonia'},
    {'name': 'Konami', 'ticker': '9766.T', 'market': 'Japonia'},
    {'name': 'Sega', 'ticker': '6460.T', 'market': 'Japonia'},
    {'name': 'Bandai Namco', 'ticker': '7832.T', 'market': 'Japonia'},
    {'name': 'Koei Tecmo', 'ticker': '3635.T', 'market': 'Japonia'},
    {'name': 'GungHo', 'ticker': '3765.T', 'market': 'Japonia'},
    {'name': 'CyberAgent', 'ticker': '4751.T', 'market': 'Japonia'},
    
    # --- CHINY / SEA ---
    {'name': 'Tencent', 'ticker': 'TCEHY', 'market': 'Chiny / Azja'},
    {'name': 'NetEase', 'ticker': 'NTES', 'market': 'Chiny / Azja'},
    {'name': 'Sea Limited', 'ticker': 'SE', 'market': 'Chiny / Azja'},
    
    # --- KOREA POŁUDNIOWA ---
    {'name': 'Krafton', 'ticker': '259960.KS', 'market': 'Korea Południowa'},
    {'name': 'NCSOFT', 'ticker': '036570.KS', 'market': 'Korea Południowa'},
    {'name': 'Netmarble', 'ticker': '251270.KS', 'market': 'Korea Południowa'},
    {'name': 'Pearl Abyss', 'ticker': '263750.KQ', 'market': 'Korea Południowa'},
    {'name': 'Kakao Games', 'ticker': '293490.KQ', 'market': 'Korea Południowa'},
    {'name': 'Wemade', 'ticker': '112040.KQ', 'market': 'Korea Południowa'},
    {'name': 'Com2uS', 'ticker': '078340.KQ', 'market': 'Korea Południowa'},
    {'name': 'Gravity', 'ticker': 'GRVY', 'market': 'Korea Południowa'},
    
    # --- EUROPA (poza Polską) ---
    {'name': 'Ubisoft', 'ticker': 'UBI.PA', 'market': 'Europa'},
    {'name': 'Embracer Group', 'ticker': 'EMBRAC-B.ST', 'market': 'Europa'},
    {'name': 'Paradox Interactive', 'ticker': 'PDX.ST', 'market': 'Europa'},
    {'name': 'Remedy Entertainment', 'ticker': 'REMEDY.HE', 'market': 'Europa'},
    {'name': 'Focus Entertainment', 'ticker': 'ALFOC.PA', 'market': 'Europa'},
    {'name': 'Nacon', 'ticker': 'NACON.PA', 'market': 'Europa'},
    {'name': 'Team17', 'ticker': 'TM17.L', 'market': 'Europa'},
    {'name': 'Frontier Developments', 'ticker': 'FDEV.L', 'market': 'Europa'},
    {'name': 'Devolver Digital', 'ticker': 'DEVO.L', 'market': 'Europa'},
    {'name': 'Stillfront Group', 'ticker': 'SF.ST', 'market': 'Europa'},
    {'name': 'Starbreeze', 'ticker': 'STAR-B.ST', 'market': 'Europa'},
    {'name': 'Enad Global 7', 'ticker': 'EG7.ST', 'market': 'Europa'},
    {'name': 'Atari', 'ticker': 'ALATA.PA', 'market': 'Europa'},
]


# --- ETAP 1: FINANSE I GIEŁDA ---

def fetch_and_save_stock_data():
    """Pobiera notowania giełdowe i zapisuje wymiary rynków oraz wydawców (wraz z adresami)."""
    print(f"--- ROZPOCZYNAM POBIERANIE DANYCH FINANSOWYCH DLA {len(PUBLISHERS_CONFIG)} SPÓŁEK ---")
    
    for pub_info in PUBLISHERS_CONFIG:
        # 1. Pobieramy lub tworzymy Rynek
        market_obj, _ = Market.objects.get_or_create(name=pub_info['market'])
        
        # 2. Pobieramy lub aktualizujemy Wydawcę (z przypisanym Rynkiem)
        publisher_obj, _ = Publisher.objects.update_or_create(
            ticker=pub_info['ticker'],
            defaults={'name': pub_info['name'], 'market': market_obj}
        )
        print(f"Pobieranie notowań dla: {publisher_obj.name} ({publisher_obj.market.name})...")
        
        try:
            ticker_data = yf.Ticker(publisher_obj.ticker)
            info = ticker_data.info
            
            # --- POBIERANIE DANYCH ADRESOWYCH I AKTUALIZACJA PROFILU FIRMY ---
            publisher_obj.address = info.get('address1', '')
            publisher_obj.city = info.get('city', '')
            publisher_obj.country = info.get('country', '')
            publisher_obj.save() # Zapisujemy nowe dane adresowe w bazie
            
            df_hist = ticker_data.history(period="5y")
            shares_outstanding = info.get('sharesOutstanding', info.get('impliedSharesOutstanding'))
            
            for date_idx, row in df_hist.iterrows():
                metric_date = date_idx.date()
                stock_close = round(row['Close'], 4) if not pd_isna(row['Close']) else None
                volume = int(row['Volume']) if not pd_isna(row['Volume']) else None
                
                market_cap = None
                if stock_close and shares_outstanding:
                    market_cap = round(stock_close * shares_outstanding, 2)
                
                StockMetric.objects.update_or_create(
                    publisher=publisher_obj,
                    date=metric_date,
                    defaults={
                        'stock_close': stock_close,
                        'volume': volume,
                        'market_cap': market_cap
                    }
                )
            print(f"-> Sukces: {publisher_obj.name}")
        except Exception as e:
            print(f"-> Błąd przy pobieraniu {publisher_obj.name}: {e}")


def pd_isna(val):
    """Pomocnicze sprawdzenie czy wartość jest typu NaN."""
    return val != val


# --- ETAP 2: IGDB API & GRY ---

def get_igdb_token(client_id, client_secret):
    auth_url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(auth_url, params=params)
    response.raise_for_status()
    return response.json()['access_token']


def fetch_batch(offset, batch_size, headers):
    url = 'https://api.igdb.com/v4/games'
    query = f"""
        fields name, first_release_date, total_rating, genres.name, platforms.name, involved_companies.company.name;
        sort total_rating desc;
        limit {batch_size};
        offset {offset};
        where total_rating != null & first_release_date != null;
    """
    try:
        response = requests.post(url, headers=headers, data=query, timeout=10)
        if response.status_code == 200:
            return offset, response.json()
    except Exception as e:
        print(f"Błąd przy offset {offset}: {e}")
    return offset, []


def fetch_and_save_games(total_games=20000, batch_size=200, max_workers=4):
    """Pobiera gry z API IGDB i wiąże je z wydawcami z naszej bazy."""
    print("\n--- ROZPOCZYNAM POBIERANIE DANYCH O GRACH Z IGDB ---")
    
    token = get_igdb_token(CLIENT_ID, CLIENT_SECRET)
    headers = {'Client-ID': CLIENT_ID, 'Authorization': f'Bearer {token}'}
    
    publishers_in_db = list(Publisher.objects.all())
    genres_cache = {}
    platforms_cache = {}
    
    offsets = list(range(0, total_games, batch_size))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_batch, offset, batch_size, headers): offset for offset in offsets}
        
        for future in as_completed(futures):
            offset, raw_data = future.result()
            if not raw_data:
                continue
                
            for game_data in raw_data:
                game_id = game_data.get('id')
                title = game_data.get('name')
                release_date = datetime.fromtimestamp(game_data['first_release_date']).date() if 'first_release_date' in game_data else None
                rating = round(game_data.get('total_rating', 0), 2)
                
                # Dopasowanie wydawcy z bazy na podstawie nazwy
                matched_publisher = None
                if 'involved_companies' in game_data:
                    for comp in game_data['involved_companies']:
                        comp_name = comp.get('company', {}).get('name', '')
                        for pub in publishers_in_db:
                            if pub.name.lower() in comp_name.lower() or comp_name.lower() in pub.name.lower():
                                matched_publisher = pub
                                break
                
                game_obj, _ = Game.objects.update_or_create(
                    game_id=game_id,
                    defaults={
                        'title': title,
                        'release_date': release_date,
                        'rating': rating,
                        'publisher': matched_publisher
                    }
                )
                
                if 'genres' in game_data:
                    g_objs = []
                    for g in game_data['genres']:
                        g_name = g['name']
                        if g_name not in genres_cache:
                            genres_cache[g_name], _ = Genre.objects.get_or_create(name=g_name)
                        g_objs.append(genres_cache[g_name])
                    game_obj.genres.set(g_objs)
                    
                if 'platforms' in game_data:
                    p_objs = []
                    for p in game_data['platforms']:
                        p_name = p['name']
                        if p_name not in platforms_cache:
                            platforms_cache[p_name], _ = Platform.objects.get_or_create(name=p_name)
                        p_objs.append(platforms_cache[p_name])
                    game_obj.platforms.set(p_objs)
                    
            print(f"Przetworzono paczkę gier: offset {offset}")


def run_full_etl():
    """Uruchamia pełny proces ETL."""
    fetch_and_save_stock_data()
    fetch_and_save_games(total_games=200000, batch_size=100)
    print("\n=== PROCES ETL ZAKOŃCZONY SUKCESEM ===")