import os
from dotenv import load_dotenv
import requests

# Chargement de la clé et du host depuis .env
load_dotenv()
RAPIDAPI_KEY   = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST  = os.getenv("RAPIDAPI_HOST_FLIGHTS")

HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST
}

def get_airport_code(city_name):
    url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchDestination"
    params = {"query": city_name}
    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()
    for result in data.get("data", []):
        if result["id"].endswith(".AIRPORT"):
            return result["id"]
    return None

def search_flights(from_id, to_id, date, adults=1, children=0, cabin_class="ECONOMY", sort="BEST"):
    url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchFlights"
    params = {
        "fromId": from_id,
        "toId": to_id,
        "departDate": date,
        "stops": "none",
        "pageNo": "1",
        "adults": str(adults),
        "children": str(children),
        "children_age": ",".join(["5"] * children) if children > 0 else None,
        "sort": sort,
        "cabinClass": cabin_class,
        "currency_code": "EUR"
    }
    # Retirer les valeurs None
    params = {k: v for k, v in params.items() if v is not None}

    try:
        res = requests.get(url, headers=HEADERS, params=params)
        if res.status_code != 200:
            print("[DEBUG] Échec API vols:", res.status_code, res.text)
            return []
        data = res.json()
        flights = data.get("data", {}).get("flightOffers", [])
        print("[DEBUG] Nombre de vols récupérés:", len(flights))
        return flights
    except Exception as e:
        print("[ERREUR FLASK flights.py]", e)
        return []

def filter_by_max_price(flights, max_price):
    return [
        flight for flight in flights
        if flight.get("price", 999999) <= max_price
    ]

def filter_by_budget(flights, budget_level):
    thresholds = {
        "Économique": 250,
        "Modéré":     600,
        "Luxe":       1200,
    }
    max_price = thresholds.get(budget_level, 600)
    return filter_by_max_price(flights, max_price)
