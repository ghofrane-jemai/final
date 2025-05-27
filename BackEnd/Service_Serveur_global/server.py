from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from flask import Flask
from flask_cors import CORS
from datetime import datetime, timedelta
import base64
import os
import logging
import firebase_admin
from firebase_admin import credentials, firestore


app = Flask(__name__)
CORS(app)


import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIREBASE_CRED_PATH = os.getenv("FIREBASE_KEY_PATH", os.path.join(BASE_DIR, "firebase_key.json"))
def init_firebase():
    if os.path.exists(FIREBASE_CRED_PATH):
        cred = credentials.Certificate(FIREBASE_CRED_PATH)
        firebase_admin.initialize_app(cred)
    else:
        raise RuntimeError(f"Firebase credentials not found at {FIREBASE_CRED_PATH}")

# Initialisation au démarrage
init_firebase()
# Connexion à Firestore
db = firestore.client()
collection = db.collection("users")

# Fonction pour vérifier si l'utilisateur a au moins 18 ans
def is_adult(birthdate):
    today = datetime.today()
    # Calculer l'âge en années en soustrayant la date de naissance de la date actuelle
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age >= 18

@app.route("/api/users", methods=["POST"])
def add_user():
    data = request.json
    print("Données reçues: %s", data)  # Debug: Afficher les données reçues

    # Vérification de la présence des champs nécessaires
    required_fields = ["firstName", "lastName", "country", "dob", "gender", "city", "selfie", "idCardFront", "idCardBack", "comparisonStatus"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Le champ '{field}' est requis"}), 400

    # Validation du format de la date
    try:
        birthdate = datetime.strptime(data["dob"], "%d/%m/%Y")
    except ValueError:
        return jsonify({"error": "Format de date invalide. Utilisez jj/mm/aaaa."}), 400

    # Vérification si l'utilisateur a au moins 18 ans
    if not is_adult(birthdate):
        return jsonify({"error": "L'utilisateur doit avoir au moins 18 ans."}), 400

    # Récupérer les images en base64
    selfie = data.get("selfie")
    idCardFront = data.get("idCardFront")
    idCardBack = data.get("idCardBack")

    # Vérification de la validité des images
    if selfie and not is_valid_base64(selfie):
        return jsonify({"error": "Le selfie est au mauvais format."}), 400

    if idCardFront and not is_valid_base64(idCardFront):
        return jsonify({"error": "La carte d'identité avant est au mauvais format."}), 400

    if idCardBack and not is_valid_base64(idCardBack):
        return jsonify({"error": "La carte d'identité arrière est au mauvais format."}), 400

    user = {
        "firstName": data["firstName"],
        "lastName": data["lastName"],
        "country": data["country"],
        "dob": birthdate,
        "gender": data["gender"],
        "city": data["city"],
        "selfie": selfie,
        "idCardFront": data.get("idCardFront"),
        "idCardBack": data.get("idCardBack"),
        "extractedDataFront": data.get("extractedDataFront"),
        "extractedDataBack": data.get("extractedDataBack"),
        "comparisonStatus": data["comparisonStatus"]  # Ajout du statut de comparaison

    }


    result = collection.insert_one(user)
    print("Utilisateur inséré avec ID: %s", result.inserted_id)

    return jsonify({"message": "Utilisateur ajouté avec succès", "id": str(result.inserted_id)}), 201


# Fonction pour valider le format de la chaîne base64 (optionnel)
def is_valid_base64(data):
    try:
        if isinstance(data, str):
            # Tentative de décodage de la chaîne base64
            base64.b64decode(data)
            return True
        return False
    except Exception:
        return False


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000) 