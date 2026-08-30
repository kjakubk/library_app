import requests

# --- DANE KONFIGURACYJNE ---
IMMICH_URL = "http://192.168.1.226:2283/api"
API_KEY = "7wH9tRK4m0KINSrRL13iHaps1Iycrj3WBjbNoR91w4"
PARTNER_USER_ID = "e3b6be8a-d725-4b65-86f6-5e46ea4889ab"
# --------------------

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

def update_albums_to_owner():
    print("Pobieranie listy albumów z Immicha...")
    response = requests.get(f"{IMMICH_URL}/albums", headers=headers)
    
    if response.status_code != 200:
        print(f"Błąd podczas pobierania albumów: {response.status_code} - {response.text}")
        return

    albums = response.json()
    print(f"Znaleziono {len(albums)} albumów. Nadaję uprawnienia 'owner'...\n")

    success_count = 0
    for album in albums:
        album_id = album['id']
        album_name = album.get('albumName', 'Bez nazwy')
        
        # Zmieniamy rolę z "editor" na "owner", żeby mogła też kasować i zarządzać
        payload = {
            "albumUsers": [
                {
                    "role": "owner",
                    "userId": PARTNER_USER_ID
                }
            ]
        }
        
        share_response = requests.put(
            f"{IMMICH_URL}/albums/{album_id}/users", 
            headers=headers, 
            json=payload
        )
        
        if share_response.status_code in [200, 201, 204]:
            print(f"[SUKCES] Nadano uprawnienia właściciela dla: '{album_name}'")
            success_count += 1
        else:
            print(f"[BŁĄD] Nie udało się zaktualizować '{album_name}': {share_response.status_code} - {share_response.text}")

    print(f"\nZakończono! Zaktualizowano pomyślnie {success_count} z {len(albums)} albumów.")

if __name__ == "__main__":
    update_albums_to_owner()