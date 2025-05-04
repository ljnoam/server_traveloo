import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()
RAPIDAPI_KEY        = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST_HOTELS= os.getenv("RAPIDAPI_HOST_HOTELS")

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST_HOTELS
}

# Endpoint pour récupérer les taux de change
EXCHANGE_URL = "https://booking-com.p.rapidapi.com/v1/metadata/exchange-rates"

# Cache en mémoire des taux de change { "USD": 0.92, ... }
_rates_cache: dict[str, float] = {}

def _safe_float(val):
    """Convertit en float ou retourne +inf pour filtrage budget."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return float("inf")

def get_rate_to_eur(from_currency: str, locale: str = "en-gb") -> float:
    """
    Récupère via l'API Booking.com le taux de conversion from_currency → EUR.
    Met en cache pour éviter les appels répétitifs.
    """
    from_currency = from_currency.upper()
    if from_currency == "EUR":
        return 1.0
    if from_currency in _rates_cache:
        return _rates_cache[from_currency]

    params = {"currency": from_currency, "locale": locale}
    try:
        resp = requests.get(EXCHANGE_URL, headers=HEADERS, params=params)
        resp.raise_for_status()
        rate = resp.json()["rates"]["EUR"]
        _rates_cache[from_currency] = rate
        return rate
    except Exception as e:
        print("[Erreur get_rate_to_eur]", e)
        return 1.0  # fallback

def get_destination_id(city_name: str) -> str | None:
    """
    Récupère l'ID Booking.com d'une ville à partir de son nom.
    """
    url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"
    params = {"name": city_name, "locale": "en-gb"}
    try:
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        for d in r.json():
            if d.get("dest_type") == "city":
                return d.get("dest_id")
    except Exception as e:
        print("[Erreur get_destination_id]", e)
    return None

def search_hotels(
    dest_id: str,
    checkin_date: str,
    checkout_date: str,
    adults: int,
    children: int,
    budget_max: float | None = None
) -> list[dict]:
    """
    Recherche jusqu'à 9 hôtels, convertit les prix en EUR,
    filtre sur budget_max (en euros) si fourni,
    et renvoie la liste formatée.
    """
    url = "https://booking-com.p.rapidapi.com/v1/hotels/search"
    params = {
        "checkin_date":       checkin_date,
        "checkout_date":      checkout_date,
        "adults_number":      adults,
        "room_number":        1,
        "dest_id":            dest_id,
        "dest_type":          "city",
        "order_by":           "popularity",
        "locale":             "en-gb",
        "units":              "metric",
        "include_adjacency":  "true",
        "page_number":        0,
        "filter_by_currency": "EUR",      # ← indispensable pour éviter le 422
    }
    if children > 0:
        params["children_number"] = children
        params["children_ages"]   = ",".join(["5"] * children)

    try:
        res = requests.get(url, headers=HEADERS, params=params)
        # En cas d'erreur, on affiche le body pour comprendre le 422
        if not res.ok:
            print(f"[Erreur search_hotels] HTTP {res.status_code} :", res.text)
        res.raise_for_status()

        results = res.json().get("result", [])

        # Filtrage budget (en euros) si demandé
        if budget_max is not None:
            def total_eur(h):
                cents    = _safe_float(h["price_breakdown"].get("gross_price"))
                orig_cur = h["price_breakdown"].get("currency", "EUR")
                return (cents / 100.0) * get_rate_to_eur(orig_cur)
            results = [h for h in results if total_eur(h) <= budget_max]

        # Formatage et limite à 9 hôtels
        return [
            format_hotel_info(h, checkin_date, checkout_date)
            for h in results[:9]
        ]

    except Exception as e:
        print("[Exception search_hotels]", e)
        return []

def format_hotel_info(
    hotel: dict,
    checkin_date: str,
    checkout_date: str
) -> dict:
    """
    Formate les infos d'un hôtel :
      - total  : prix pour tout le séjour (€)
      - price  : prix par nuit (€)
      - nights : nombre de nuits
      - name, address, photo, rating, room, booking_url, currency
    """
    pb       = hotel.get("price_breakdown", {})
    cents    = _safe_float(pb.get("gross_price", 0))
    orig_cur = pb.get("currency", "EUR")

    # Conversion → euros
    amount    = cents / 100.0
    rate      = get_rate_to_eur(orig_cur)
    total_eur = round(amount * rate, 2)

    # Calcul du nombre de nuits
    try:
        d1 = datetime.fromisoformat(checkin_date)
        d2 = datetime.fromisoformat(checkout_date)
        nights = max((d2 - d1).days, 1)
    except Exception:
        nights = 1

    per_night = round(total_eur / nights, 2)

    return {
        "name":        hotel.get("hotel_name", "Hôtel inconnu"),
        "address":     hotel.get("address", ""),
        "photo":       hotel.get("max_photo_url", ""),
        "rating":      hotel.get("review_score"),
        "room":        clean_room_info(hotel.get("unit_configuration_label", "")),
        "booking_url": hotel.get("url", "#"),

        "nights":      nights,
        "total":       total_eur,
        "price":       per_night,
        "currency":    "€"
    }

def clean_room_info(text: str) -> str:
    """Enlève balises HTML et &nbsp;."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&nbsp;", " ").strip()
