from flask import Blueprint, Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import logging


app = Flask(__name__)
CORS(app)


FACE_VERIFICATION_API_KEY = os.getenv("FACE_VERIFICATION_API_KEY")
FACE_VERIFICATION_API_URL = os.getenv("FACE_VERIFICATION_API_URL")

# Créer un Blueprint pour les routes liées à la vérification des visages
verify_face_bp = Blueprint('verify_face', __name__)

def verify_faces(face_id1, face_id2):
    """Vérifie si deux visages sont identiques et retourne la confiance"""
    headers = {
        'Ocp-Apim-Subscription-Key': FACE_VERIFICATION_API_KEY,
        'Content-Type': 'application/json'
    }
    
    body = {
        "faceId1": face_id1,
        "faceId2": face_id2
    }
    
    response = requests.post(
        FACE_VERIFICATION_API_URL,
        headers=headers,
        json=body
    )
    
    if response.status_code != 200:
        raise Exception(f"Face verification failed: {response.text}")
    
    result = response.json()
    return {
        "isIdentical": result.get('isIdentical', False),
        "confidence": result.get('confidence', 0.0)  # Extraire la confidence
    }

@app.route('/api/verify-faces', methods=['POST'])
def verify_faces_route():
    try:
        # Récupérer les faceId depuis la requête JSON
        data = request.json
        face_id_recto = data.get('faceIdRecto')
        face_id_success = data.get('faceIdSuccess')

        if not face_id_recto or not face_id_success:
            return jsonify({
                "status": "failure",
                "message": "Missing faceId(s)"
            }), 400

        # Vérifier si les visages sont identiques
        verification_result = verify_faces(face_id_recto, face_id_success)

        # Retourner le résultat avec la confidence
        return jsonify({
            "status": "success" if verification_result["isIdentical"] else "failure",
            "message": "Face verification passed" if verification_result["isIdentical"] else "Faces are not identical",
            "isIdentical": verification_result["isIdentical"],
            "confidence": verification_result["confidence"]  # Ajouter la confidence
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5008) 