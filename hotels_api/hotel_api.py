import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()
RAPIDAPI_KEY         = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST_HOTELS = os.getenv("RAPIDAPI_HOST_HOTELS")

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST_HOTELS
}

def _safe_float(val):
    """Convertit val en float ou retourne +inf."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return float("inf")

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
    Recherche jusqu'à 9 hôtels en EUR, filtre sur budget_max (en €)
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
        "filter_by_currency": "EUR",   # l’API renvoie déjà en euros
    }
    if children > 0:
        params["children_number"] = children
        params["children_ages"]   = ",".join(["5"] * children)

    try:
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()
        results = res.json().get("result", [])

        # Filtrer par budget total en € si nécessaire
        if budget_max is not None:
            def total_eur(h):
                return _safe_float(h["price_breakdown"].get("gross_price"))
            results = [h for h in results if total_eur(h) <= budget_max]

        # Formater et ne garder que 9 hôtels
        return [
            format_hotel_info(h, checkin_date, checkout_date)
            for h in results[:9]
        ]

    except Exception as e:
        print("[Erreur search_hotels]", e)
        return []

def format_hotel_info(
    hotel: dict,
    checkin_date: str,
    checkout_date: str
) -> dict:
    """
    Formate les infos d'un hôtel :
      - total  : prix pour tout le séjour (en €)
      - price  : prix par nuit (en €)
      - nights : nombre de nuits
      + nom, adresse, photo, note, room, booking_url, currency
    """
    pb       = hotel.get("price_breakdown", {})
    raw_price= _safe_float(pb.get("gross_price", 0))
    total    = round(raw_price, 2)

    # Calcul du nombre de nuits
    try:
        d1 = datetime.fromisoformat(checkin_date)
        d2 = datetime.fromisoformat(checkout_date)
        nights = max((d2 - d1).days, 1)
    except Exception:
        nights = 1

    per_night = round(total / nights, 2)

    return {
        "name":        hotel.get("hotel_name", "Hôtel inconnu"),
        "address":     hotel.get("address", ""),
        "photo":       hotel.get("max_photo_url", ""),
        "rating":      hotel.get("review_score"),
        "room":        clean_room_info(hotel.get("unit_configuration_label", "")),
        "booking_url": hotel.get("url", "#"),

        "nights":   nights,
        "total":    total,
        "price":    per_night,
        "currency": "€"
    }

def clean_room_info(text: str) -> str:
    """Supprime balises HTML et &nbsp;."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&nbsp;", " ").strip()
