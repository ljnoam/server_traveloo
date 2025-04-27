import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flights import get_airport_code, search_flights
from utils import format_flight_info

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)
# Lecture des origines CORS depuis .env
origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS(app, resources={r"/api/*": {"origins": origins}})

@app.route("/api/flights", methods=["POST"])
def api_flights():
    data = request.get_json()
    print("[📥 API Flights] Données reçues:", data)

    from_city   = data.get("from")
    to_city     = data.get("to")
    depart_date = data.get("depart_date")
    return_date = data.get("return_date")
    adults      = int(data.get("adults", 1))
    children    = int(data.get("children", 0))
    total_passengers = adults + children

    # Classe de cabine par défaut
    cabin_map = {
        "Économique":     "ECONOMY",
        "Modéré":         "PREMIUM_ECONOMY",
        "Luxe":           "FIRST"
    }
    cabin_class = cabin_map.get(data.get("budget", "Économique"), "ECONOMY")

    # Obtenir les codes d’aéroports
    from_code = get_airport_code(from_city)
    to_code   = get_airport_code(to_city)
    if not from_code or not to_code:
        return jsonify({"error": "Impossible de récupérer les codes d’aéroport"}), 400

    # Appels API
    outbound_raw = search_flights(from_code, to_code, depart_date, adults, children, cabin_class)
    return_raw   = search_flights(to_code, from_code, return_date, adults, children, cabin_class)

    # Formatage des vols (max 5)
    outbound = [
        format_flight_info(f, total_passengers, adults, children, cabin_class, return_date)
        for f in outbound_raw[:5]
    ]
    retour = [
        format_flight_info(f, total_passengers, adults, children, cabin_class, depart_date)
        for f in return_raw[:5]
    ]

    print(f"[✅ API Flights] Vols aller: {len(outbound)} | Vols retour: {len(retour)}")
    return jsonify({"outbound": outbound, "return": retour})

if __name__ == "__main__":
    # Désactiver debug en production !
    app.run(port=5000, debug=False)
