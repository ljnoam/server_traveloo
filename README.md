Voici un fichier `README.md` complet, prêt à être collé, pour que ton collègue sache comment installer les dépendances et exécuter les différentes APIs (`flights`, `hotels`, `favorites`). Il est structuré de manière claire et professionnelle :

---

```markdown
# ✈️🛏️ Travel Planner API

Ce projet est composé de trois services Flask interconnectés, permettant de rechercher des vols, des hôtels et de sauvegarder des itinéraires favoris dans une base de données Supabase.

## 🧱 Structure du projet

```
├── app.py                 # API pour les vols (port 5000)
├── hotel_api.py          # Fonctions liées aux hôtels (Booking API)
├── flights.py            # Fonctions liées aux vols (Booking Flights API)
├── utils.py              # Utilitaires pour le traitement des données de vol
├── favorites_api.py      # API pour gérer les favoris (port 5002)
├── requirements.txt      # Dépendances Python
```

## 🚀 Lancer les applications

### 1. 📦 Installation des dépendances

Assurez-vous d’avoir Python 3.9+ installé. Ensuite, créez un environnement virtuel (optionnel mais recommandé) :

```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install -r requirements.txt
```

**Fichier `requirements.txt` (à créer si non présent) :**
```txt
Flask
Flask-Cors
Flask-SQLAlchemy
requests
```

### 2. 🔐 Configuration des clés API

Les services utilisent l’API de **Booking.com via RapidAPI**. Les clés sont déjà codées en dur dans les fichiers (`hotel_api.py`, `flights.py`). Si besoin de changement :

- `x-rapidapi-key`
- `x-rapidapi-host`

> ⚠️ Il est recommandé de stocker ces clés dans un fichier `.env` et de les lire avec `os.environ`.

### 3. ▶️ Lancer les serveurs Flask

#### API Vols (`app.py` dans `/api/flights`)
```bash
python app.py
# Port 5000
```

#### API Hôtels (`app.py` dans `/api/hotels`)
Renommer ou séparer ce fichier si besoin, puis :
```bash
python app.py
# Port 5001
```

#### API Favoris (`favorites_api.py`)
```bash
python favorites_api.py
# Port 5002
```

> 💡 Astuce : exécute chaque API dans un terminal distinct.

## 🗃️ Base de données Supabase

La connexion est déjà configurée dans `favorites_api.py`. Les favoris sont stockés dans une table `favorites` avec les champs suivants :
- `user_id`
- `destination`
- `start_date` / `end_date`
- `itinerary`
- `flights` / `hotels` (JSON)
- `created_at`

### 🔧 Initialisation de la base

Si tu exécutes le projet pour la première fois :

```python
from favorites_api import db
db.create_all()
```

Tu peux ajouter ce code temporairement dans `favorites_api.py` avant le `app.run(...)` pour créer la table.

---

## 📮 Exemple de requêtes

### 🔍 Rechercher des vols

`POST /api/flights` sur `http://localhost:5000/api/flights`

```json
{
  "from": "Paris",
  "to": "Rome",
  "startDate": "2024-07-10",
  "endDate": "2024-07-15",
  "adults": 2,
  "children": 1,
  "useCustomBudget": true,
  "budgetFlights": 300
}
```

### 🔍 Rechercher des hôtels

`POST /api/hotels` sur `http://localhost:5001/api/hotels`

```json
{
  "destination": "Rome",
  "startDate": "2024-07-10",
  "endDate": "2024-07-15",
  "adults": 2,
  "children": 1,
  "useCustomBudget": true,
  "budgetHotels": 200
}
```

### ❤️ Ajouter un favori

`POST /api/favorites` sur `http://localhost:5002/api/favorites`

```json
{
  "user_id": "123",
  "destination": "Rome",
  "start_date": "2024-07-10",
  "end_date": "2024-07-15",
  "itinerary": { "steps": ["flight", "hotel"] },
  "flights": [...],
  "hotels": [...]
}
```

### 📥 Récupérer les favoris

`GET /api/favorites/<user_id>`  
→ `http://localhost:5002/api/favorites/123`

---

## ✅ À faire éventuellement

- Externaliser les clés API dans un fichier `.env`
- Séparer les services en modules distincts (flights_service, hotels_service, etc.)
- Ajouter un `docker-compose.yml` pour tout lancer facilement

---

Bon dev 🚀
```

---

Souhaite-tu que je génère aussi le fichier `requirements.txt` à coller ?