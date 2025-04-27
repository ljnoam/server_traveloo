import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)
# Lecture de la chaîne de connexion depuis .env
app.config['SQLALCHEMY_DATABASE_URI']    = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Origines CORS depuis .env
origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
CORS(app, resources={r"/api/*": {"origins": origins}})

db = SQLAlchemy(app)

class Favorite(db.Model):
    __tablename__ = "favorites"
    id          = db.Column(db.Integer,   primary_key=True)
    user_id     = db.Column(db.String,    nullable=False)
    destination = db.Column(db.String)
    start_date  = db.Column(db.Date)
    end_date    = db.Column(db.Date)
    itinerary   = db.Column(db.JSON)
    flights     = db.Column(db.JSON)
    hotels      = db.Column(db.JSON)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

@app.route("/api/favorites", methods=["POST"])
def add_favorite():
    data = request.get_json()
    try:
        fav = Favorite(
            user_id    = data["user_id"],
            destination= data["destination"],
            start_date = data["start_date"],
            end_date   = data["end_date"],
            itinerary  = data["itinerary"],
            flights    = data.get("flights"),
            hotels     = data.get("hotels")
        )
        db.session.add(fav)
        db.session.commit()
        return jsonify({"message": "Itinéraire ajouté aux favoris ✅"}), 201
    except Exception as e:
        print("❌ Erreur POST favorites :", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/favorites/<user_id>", methods=["GET"])
def get_favorites(user_id):
    try:
        results = Favorite.query.filter_by(user_id=user_id).all()
        return jsonify([
            {
                "id":          fav.id,
                "destination": fav.destination,
                "start_date":  fav.start_date,
                "end_date":    fav.end_date,
                "itinerary":   fav.itinerary,
                "flights":     fav.flights,
                "hotels":      fav.hotels,
                "created_at":  fav.created_at
            }
            for fav in results
        ])
    except Exception as e:
        print("❌ Erreur GET favorites :", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5002, debug=False)
