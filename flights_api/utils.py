from datetime import datetime

def format_flight_info(flight, total_passengers=1, adults=1, children=0, cabin_class="economy", return_date=None):
    price_info = flight.get("unifiedPriceBreakdown", {}).get("price", {})
    unit_price = price_info.get("units", 0) + price_info.get("nanos", 0) / 1e9
    total_price = unit_price * total_passengers

    segments = flight.get("segments", [])
    if not segments:
        return {}

    first_leg = segments[0].get("legs", [{}])[0]
    last_leg  = segments[-1].get("legs", [{}])[-1]

    dep_airport = first_leg.get("departureAirport", {}).get("cityName", "Inconnu")
    arr_airport = last_leg.get("arrivalAirport", {}).get("cityName", "Inconnu")
    dep_time    = first_leg.get("departureTime", "")
    arr_time    = last_leg.get("arrivalTime", "")
    duration    = sum(seg.get("totalTime", 0) for seg in segments)

    carrier_info = first_leg.get("carriersData", [])
    if carrier_info:
        airline_name = carrier_info[0].get("name", "Compagnie inconnue")
        airline_logo = carrier_info[0].get("logo", "")
    else:
        airline_name = "Compagnie inconnue"
        airline_logo = ""

    origin_code = first_leg.get("departureAirport", {}).get("code", "").lower()
    dest_code   = last_leg.get("arrivalAirport", {}).get("code", "").lower()

    dep_date_str = dep_time[:10].replace("-", "")[2:]
    ret_date_str = return_date.replace("-", "")[2:] if return_date else ""

    skyscanner_url = (
        f"https://www.skyscanner.fr/transport/flights/{origin_code}/{dest_code}/"
        f"{dep_date_str}/{ret_date_str}/?adults={adults}&children={children}&cabinclass={cabin_class.lower()}"
    )

    return {
        "departure_city": dep_airport,
        "arrival_city":   arr_airport,
        "departure_time": dep_time[11:16],
        "arrival_time":   arr_time[11:16],
        "duration":       f"{duration // 3600}h{(duration % 3600) // 60}m",
        "price":          round(total_price, 2),
        "currency":       price_info.get("currencyCode", "EUR"),
        "airline":        airline_name,
        "logo":           airline_logo,
        "booking_url":    skyscanner_url
    }

def filter_by_budget(flights, level="medium"):
    if not isinstance(flights, list):
        return []
    flights = [f for f in flights if isinstance(f, dict) and f.get("unifiedPriceBreakdown")]
    flights.sort(key=lambda f: f["unifiedPriceBreakdown"]["price"]["units"])
    if level == "low":
        limit = len(flights) // 3
    elif level == "medium":
        limit = 2 * len(flights) // 3
    else:
        limit = len(flights)
    return flights[:limit]

def filter_by_max_price(flights, max_price, total_passengers):
    results = []
    for f in flights:
        price_info = f.get("unifiedPriceBreakdown", {}).get("price", {})
        unit_price = price_info.get("units", 0) + price_info.get("nanos", 0) / 1e9
        total = unit_price * total_passengers
        if total <= max_price:
            results.append(f)
    return results
