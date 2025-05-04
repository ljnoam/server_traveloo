import os
import re
import requests
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()
RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST_HOTELS")

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST
}

def get_destination_id(city_name):
    """
    Récupère l'ID Booking.com d'une ville à partir de son nom.
    """
    url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"
    params = {"name": city_name, "locale": "en-gb"}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        for d in data:
            if d.get("dest_type") == "city":
                return d.get("dest_id")
    except Exception as e:
        print("[Erreur get_destination_id]", e)
    return None

def search_hotels(dest_id, checkin_date, checkout_date, adults, children, budget_max=None):
    """
    Recherche des hôtels et renvoie une liste de dictionnaires formatés.
    Les prix sont déjà demandés en EUR grâce à filter_by_currency.
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
        "filter_by_currency": "EUR",      # ← l’API renvoie déjà en euros
        "include_adjacency":  "true",
        "page_number":        "0"
    }
    if children > 0:
        params["children_number"] = children
        params["children_ages"]   = ",".join(["5"] * children)

    try:
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()
        hotels = res.json().get("result", [])

        # Filtrer par budget total si nécessaire
        if budget_max is not None:
            hotels = [
                h for h in hotels
                if h.get("price_breakdown", {}).get("gross_price", float("inf")) <= budget_max
            ]

        # Ne garder que les 9 premiers
        return [format_hotel_info(h) for h in hotels[:9]]
    except Exception as e:
        print("[Erreur search_hotels]", e)
        return []

def format_hotel_info(hotel):
    """
    Extrait et formate les infos d'un hôtel, en supposant que
    gross_price est déjà en euros.
    """
    raw_price = hotel.get("price_breakdown", {}).get("gross_price")
    price_eur = round(raw_price, 2) if raw_price is not None else None

    return {
        "name":        hotel.get("hotel_name", "Hôtel inconnu"),
        "address":     hotel.get("address", ""),
        "price":       price_eur,
        "currency":    "€",
        "photo":       hotel.get("max_photo_url", ""),
        "rating":      hotel.get("review_score"),
        "room":        clean_room_info(hotel.get("unit_configuration_label", "")),
        "booking_url": hotel.get("url", "#")
    }

def clean_room_info(text):
    """
    Enlève les balises HTML et les espaces insécables.
    """
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&nbsp;", " ").strip()
