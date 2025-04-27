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

def convert_to_eur(amount, from_currency):
    if from_currency == "EUR":
        return amount
    try:
        res = requests.get(f"https://api.exchangerate.host/convert?from={from_currency}&to=EUR")
        res.raise_for_status()
        rate = res.json().get("result", 1)
        return round(amount * rate, 2)
    except Exception as e:
        print("[Erreur conversion devise]", e)
        return amount

def get_destination_id(city_name):
    url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"
    params = {"name": city_name, "locale": "en-gb"}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        for d in data:
            if d["dest_type"] == "city":
                return d["dest_id"]
    except Exception as e:
        print("[Erreur get_destination_id]", e)
    return None

def search_hotels(dest_id, checkin_date, checkout_date, adults, children, budget_max=None):
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
        "filter_by_currency": "EUR",
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
        if budget_max is not None:
            hotels = [
                h for h in hotels
                if h.get("price_breakdown", {}).get("gross_price", float("inf")) <= budget_max
            ]
        return [format_hotel_info(h) for h in hotels[:9]]
    except Exception as e:
        print("[Erreur search_hotels]", e)
        return []

def format_hotel_info(hotel):
    raw_price    = hotel.get("price_breakdown", {}).get("gross_price")
    raw_currency = hotel.get("price_breakdown", {}).get("currency", "EUR")
    converted    = convert_to_eur(raw_price, raw_currency) if raw_price else None

    return {
        "name":        hotel.get("hotel_name", "Hôtel inconnu"),
        "address":     hotel.get("address", ""),
        "price":       converted,
        "currency":    "€",
        "photo":       hotel.get("max_photo_url", ""),
        "rating":      hotel.get("review_score"),
        "room":        clean_room_info(hotel.get("unit_configuration_label", "")),
        "booking_url": hotel.get("url", "#")
    }

def clean_room_info(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("&nbsp;", " ").strip()
