import io
import csv
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from django.utils import timezone
from .models import Category, Transaction, Account


CATEGORY_KEYWORD_RULES = [
    # 🛒 Jedzenie & Artykuły spożywcze
    (r'(biedronka|lidl|dino|kaufland|carrefour|auchan|zabka|żabka|stokrotka|intermarche|netto|aldi|spolem|społem|piekarnia|cukiernia|delikatesy|frisco|zakupy spozywcze|warzywniak)', 'Jedzenie & Artykuły spożywcze', 'expense'),
    
    # 🚗 Transport & Paliwo
    (r'(orlen|bp station|shell|circle k|moya|amic|autostrada|a4|a1|a2|autopay|uber|bolt|freenow|mpk|ztm|jakdojade|pkp|intercity|koleje|polregio|stacja paliw|parking|wulkanizacja|myjnia)', 'Transport & Paliwo', 'expense'),
    
    # 🏠 Mieszkanie & Czynsz
    (r'(czynsz|wspolnota|wspólnota|spoldzielnia|spółdzielnia|wynajem|odstepne|odstępne|zarzadca|zarządca|administracja budynku)', 'Mieszkanie & Czynsz', 'expense'),
    
    # ⚡ Rachunki & Media
    (r'(pge|energa|enea|tauron|pgnig|gazownia|orange|play|plus|t-mobile|upc|vectra|netia|toya|multimedia|wodociagi|wodociągi|smieci|ścieki|aquanet|mpwik)', 'Rachunki & Media', 'expense'),
    
    # 💊 Zdrowie & Apteka
    (r'(apteka|doz|gemini|rossmann|hebe|medicover|lux med|enel-med|stomatolog|dentysta|lekarz|przychodnia|badania krwi|diagnostyka|alablaboratoria|rehabilitacja|okulista)', 'Zdrowie & Apteka', 'expense'),
    
    # 🎬 Rozrywka & Wyjścia
    (r'(netflix|spotify|hbo|disney|apple\.com|youtube|steam|playstation|sony playstation|xbox|nintendo|gog\.com|cinema|multikino|helios|kino|teatr|restauracja|kawiarnia|mcdonald|kfc|burger|pizza|pyszne|ubereats|glovo|wolt|starbucks|costa|pub|bar)', 'Rozrywka & Wyjścia', 'expense'),
    
    # 💎 Kolekcje & Hobby
    (r'(olx|vinted|allegro|empik|lego|komiks|antyki|numizmatyka|gry planszowe|modelarstwo|swiatksiazki|taniaksiazka|audiobook)', 'Kolekcje & Hobby', 'expense'),
    
    # 👕 Ubrania & Zakupy
    (r'(zara|h&m|reserved|ccc|eobuwie|zalando|answear|modivo|cropp|house|mohito|sinsay|pepco|action|decathlon|ikea|castorama|leroy|obi|media markt|rtv euro|x-kom|morele)', 'Ubrania & Zakupy', 'expense'),
    
    # 🏢 Faktura B2B / Kontrakt
    (r'(faktura|kontrakt|b2b|gonito|uslugi programistyczne|usługi programistyczne|zlecenie|wynagrodzenie b2b|it services)', 'Faktura B2B / Kontrakt', 'income'),
    
    # 🏛️ Podatki, ZUS & Księgowość
    (r'(zus|ubezpieczen|ubezpieczeń|urzad skarbowy|urząd skarbowy|vat-7|ppe|pit-5|podatek|cashdirector|ksiegow|księgow|infakt|wfirma)', 'Rachunki & Media', 'expense'),

    # 💼 Wynagrodzenie / Pensja
    (r'(wynagrodzenie|pensja|wyplata|wypłata|przelew wynagrodzenia|uposazenie|zaliczka na poczet wynagrodzenia|wynagrodzenie za prace)', 'Wynagrodzenie / Pensja', 'income'),
    
    # 🎁 Premia / Bonus
    (r'(premia|bonus|nagroda|świadczenie|dodatek|zwrot podatku|urzad skarbowy|urząd skarbowy)', 'Premia / Bonus', 'income'),
]


def clean_amount_str(raw_val):
    if not raw_val:
        return Decimal('0.00')
    val = str(raw_val).strip()
    val = re.sub(r'[^\d,.\-+]', '', val)
    if ',' in val and '.' in val:
        if val.rfind(',') > val.rfind('.'):
            val = val.replace('.', '').replace(',', '.')
        else:
            val = val.replace(',', '')
    else:
        val = val.replace(',', '.')
    
    try:
        return Decimal(val)
    except InvalidOperation:
        return Decimal('0.00')


def parse_date_str(raw_val):
    if not raw_val:
        return timezone.now().date()
    val = str(raw_val).strip()[:10]
    
    formats = [
        '%Y-%m-%d', '%d.%m.%Y', '%d-%m-%Y', '%d/%m/%Y',
        '%Y.%m.%d', '%Y/%m/%d', '%d%m%Y', '%Y%m%d'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return timezone.now().date()


def match_category(title, transaction_type):
    lower_title = title.lower()
    for pattern, cat_name, c_type in CATEGORY_KEYWORD_RULES:
        if c_type == transaction_type and re.search(pattern, lower_title):
            cat = Category.objects.filter(name__icontains=cat_name.split(' ')[0], category_type=transaction_type).first()
            if cat:
                return cat
            
    default_name = 'Inne wydatki' if transaction_type == 'expense' else 'Inne przychody'
    return Category.objects.filter(name__icontains=default_name, category_type=transaction_type).first()


def decode_csv_content(file_bytes):
    encodings = ['utf-8-sig', 'utf-8', 'cp1250', 'windows-1250', 'iso-8859-2', 'latin2']
    for enc in encodings:
        try:
            return file_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode('utf-8', errors='replace')


def detect_delimiter(text_sample):
    lines = [l for l in text_sample.splitlines() if l.strip()][:10]
    sample = '\n'.join(lines)
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=';,\t')
        return dialect.delimiter
    except Exception:
        semicolons = sample.count(';')
        commas = sample.count(',')
        return ';' if semicolons >= commas else ','


def parse_bank_csv(file_bytes, account):
    text_content = decode_csv_content(file_bytes)
    delimiter = detect_delimiter(text_content)
    
    lines = text_content.splitlines()
    start_idx = 0
    header_row = None
    
    for i, line in enumerate(lines):
        line_clean = line.strip().lower()
        if delimiter in line_clean or ';' in line_clean or ',' in line_clean:
            has_date = any(k in line_clean for k in ['data operacji', 'data transakcji', 'data księgowania', 'started date', 'data waluty', 'transaction date'])
            has_amount_or_title = any(k in line_clean for k in ['kwota', 'amount', 'tytuł', 'opis operacji', 'saldo', 'odbiorca', 'obciążen', 'uznan'])
            if has_date and has_amount_or_title:
                header_row = i
                break

    if header_row is not None:
        start_idx = header_row
        reader_input = lines[start_idx:]
    else:
        reader_input = lines

    reader = csv.reader(reader_input, delimiter=delimiter)
    try:
        raw_headers = next(reader)
    except StopIteration:
        return []

    headers = [h.strip().lower() for h in raw_headers]

    date_col = None
    title_col = None
    desc_col = None
    sender_col = None
    amount_col = None
    charge_col = None
    credit_col = None

    # Precyzyjne rozpoznawanie kolumn (najpierw szukamy dokładnego Tytułu, potem Opisu)
    for idx, h in enumerate(headers):
        clean_h = h.lstrip('#').strip()
        if date_col is None and any(k in clean_h for k in ['data operacji', 'data transakcji', 'started date', 'data księgowania', 'data waluty', 'data']):
            date_col = idx
        elif title_col is None and any(k == clean_h or k in clean_h for k in ['tytuł', 'tytuł operacji', 'tytuł przelewu', 'details']):
            title_col = idx
        elif desc_col is None and any(k in clean_h for k in ['opis operacji', 'opis', 'description', 'szczegóły']):
            desc_col = idx
        elif sender_col is None and any(k in clean_h for k in ['odbiorca', 'nadawca', 'kontrahent', 'partner', 'nazwa odbiorcy', 'dane kontrahenta']):
            sender_col = idx
        elif amount_col is None and any(k in clean_h for k in ['kwota operacji', 'kwota transakcji', 'kwota w walucie', 'kwota', 'amount']):
            amount_col = idx
        elif charge_col is None and 'obciążen' in clean_h:
            charge_col = idx
        elif credit_col is None and 'uznan' in clean_h:
            credit_col = idx

    # Jeśli nie znaleziono kolumny 'tytuł', użyj 'opis'
    if title_col is None and desc_col is not None:
        title_col = desc_col
    elif title_col is None and len(headers) > 1:
        title_col = 1

    if date_col is None: date_col = 0
    if amount_col is None and len(headers) > 2: amount_col = 2

    parsed_transactions = []
    from collections import Counter
    existing_txs_list = list(
        Transaction.objects.filter(account=account).values_list('date', 'amount', 'transaction_type')
    )
    existing_counts = Counter(existing_txs_list)

    for row_idx, row in enumerate(reader):
        if not row:
            continue

        raw_date = row[date_col].strip() if (date_col is not None and date_col < len(row)) else ''
        if not raw_date:
            continue
        # Sprawdzamy czy wiersz zaczyna się od daty (format YYYY-MM-DD, DD.MM.YYYY itp.)
        if not re.search(r'^\d{4}[-./]\d{1,2}[-./]\d{1,2}|^\d{1,2}[-./]\d{1,2}[-./]\d{2,4}', raw_date):
            continue
        tx_date = parse_date_str(raw_date)

        t_title = row[title_col].strip() if (title_col is not None and title_col < len(row)) else ''
        t_desc = row[desc_col].strip() if (desc_col is not None and desc_col < len(row)) else ''
        t_sender = row[sender_col].strip() if (sender_col is not None and sender_col < len(row)) else ''

        # Budowanie czytelnego tytułu transakcji
        parts = []
        if t_sender:
            parts.append(t_sender)
        if t_title and (not t_sender or t_title.lower() not in t_sender.lower()):
            parts.append(t_title)
        elif not t_title and t_desc and (not t_sender or t_desc.lower() not in t_sender.lower()):
            parts.append(t_desc)

        full_title = ' - '.join(parts) if parts else (t_title or t_desc or t_sender or "Transakcja bankowa")
        full_title = re.sub(r'\s+', ' ', full_title).strip()

        # Odczyt kwoty
        raw_amount = Decimal('0.00')
        if charge_col is not None and credit_col is not None:
            charge_val = clean_amount_str(row[charge_col]) if charge_col < len(row) else Decimal('0.00')
            credit_val = clean_amount_str(row[credit_col]) if credit_col < len(row) else Decimal('0.00')
            if charge_val != 0:
                raw_amount = -abs(charge_val)
            elif credit_val != 0:
                raw_amount = abs(credit_val)
        elif amount_col is not None and amount_col < len(row):
            raw_amount = clean_amount_str(row[amount_col])

        if raw_amount == 0:
            continue

        if raw_amount < 0:
            t_type = 'expense'
            amount = abs(raw_amount)
        else:
            t_type = 'income'
            amount = abs(raw_amount)

        category = match_category(full_title, t_type)

        # Precyzyjne wykrywanie duplikatu (metoda puli)
        tx_key = (tx_date, amount, t_type)
        if existing_counts[tx_key] > 0:
            is_duplicate = True
            existing_counts[tx_key] -= 1  # Zużywamy jedno dopasowanie z bazy
        else:
            is_duplicate = False

        parsed_transactions.append({
            'row_id': row_idx,
            'date': tx_date,
            'date_str': tx_date.strftime('%Y-%m-%d'),
            'title': full_title,
            'amount': amount,
            'amount_str': f"{amount:.2f}",
            'type': t_type,
            'category_id': category.id if category else '',
            'category_name': category.name if category else 'Brak kategorii',
            'category_icon': category.icon if category else '🏷️',
            'is_duplicate': is_duplicate,
            'selected': not is_duplicate,
        })

    return parsed_transactions
