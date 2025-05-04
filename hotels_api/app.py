# app.py

import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from hotel_api import get_destination_id, search_hotels

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)

# Origines CORS depuis .env (on peut restreindre ici plus finement)
origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

# Configuration CORS pour gérer OPTIONS et autoriser nos requêtes front
CORS(
    app,
    resources={r"/api/*": {"origins": origins}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    supports_credentials=True
)

@app.route("/api/hotels", methods=["POST"])
def api_hotels():
    data = request.get_json()
    print("\n[📥 API Hôtel] Données reçues:", data)

    if not data:
        return jsonify({"error": "Requête vide"}), 400

    city         = data.get("destination")
    checkin_date = data.get("startDate")
    checkout_date= data.get("endDate")
    adults       = int(data.get("adults", 1))
    children     = int(data.get("children", 0))
    use_custom   = data.get("useCustomBudget", False)

    try:
        budget_max = float(data.get("budgetHotels") or 0)
    except (ValueError, TypeError):
        budget_max = 0

    if not city or not checkin_date or not checkout_date:
        return jsonify({"error": "Champs manquants"}), 400

    dest_id = get_destination_id(city)
    if not dest_id:
        return jsonify({"error": "Destination introuvable"}), 400

    print(f"[🔍 API Hôtel] Recherche d'hôtels à {city} (id {dest_id}) du {checkin_date} au {checkout_date}")

    hotels = search_hotels(
        dest_id=dest_id,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        adults=adults,
        children=children,
        budget_max=budget_max if use_custom else None
    )

    if not hotels:
        return jsonify({"hotels": [], "message": "Aucun hôtel trouvé"}), 200

    return jsonify({"hotels": hotels}), 200

if __name__ == "__main__":
    app.run(port=5001, debug=False)
