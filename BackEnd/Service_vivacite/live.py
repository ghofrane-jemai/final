from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import requests
import os
import base64
import traceback  # Ajoutez cet import
import glob       # Ajoutez cet import
import cv2        # Ajoutez cet import
import numpy as np  # Ajoutez cet import
import os
import logging



app = Flask(__name__)
CORS(app)


FACE_DETECTION_API_KEY = os.getenv("FACE_DETECTION_API_KEY")
FACE_DETECTION_API_URL = os.getenv("FACE_DETECTION_API_URL")

FACE_VERIFICATION_API_KEY = os.getenv("FACE_VERIFICATION_API_KEY")
FACE_VERIFICATION_API_URL = os.getenv("FACE_VERIFICATION_API_URL")


# Ajoutez cette fonction
def clean_old_images():
    """Supprime les anciennes images de capture"""
    for file in glob.glob("capture_*.jpg"):
        try:
            os.remove(file)
            print(f"Deleted old file: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {str(e)}")

def detect_faces(image_path):
    """Détecte les visages dans une image et retourne les faceIds"""
    headers = {
        'Ocp-Apim-Subscription-Key': FACE_DETECTION_API_KEY,
        'Content-Type': 'application/octet-stream'
    }
    
    with open(image_path, 'rb') as image_file:
        response = requests.post(
            FACE_DETECTION_API_URL,
            headers=headers,
            data=image_file.read(),
            params={'returnFaceId': 'true'}
        )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Face detection failed: {response.text}")

def verify_faces(face_id1, face_id2):
    """Vérifie si deux visages sont identiques"""
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
    
    return response.json()

@app.route('/api/liveness', methods=['POST'])
def liveness_detection():
    try:
        # Nettoyer les anciennes images avant de commencer
        clean_old_images()
        result = subprocess.run(
            ['C:\\Users\\user\\AppData\\Local\\Programs\\Python\\Python37\\python.exe', 'face_anti_spoofing.py'],
            capture_output=True,
            text=True
        )

        print("Script output:", result.stdout)
        print("Script errors:", result.stderr)

        if "Vivacite avec succes" not in result.stdout:
            return jsonify({
                "status": "failure",
                "message": "Detection de vivacite echouee",
                "details": result.stderr
            }), 400

        # Vérifier que les deux images existent
        if not all(os.path.exists(img) for img in ["capture_start.jpg", "capture_success.jpg"]):
            return jsonify({
                "status": "failure",
                "message": "Absence des images requises"
            }), 400

        # Détection des visages
        start_faces = detect_faces("capture_start.jpg")
        success_faces = detect_faces("capture_success.jpg")

        if not start_faces or not success_faces:
            return jsonify({
                "status": "failure",
                "message": "Détection faciale échouée en une ou deux images"
            }), 400

        # Vérification de similarité
        verification = verify_faces(start_faces[0]['faceId'], success_faces[0]['faceId'])

        # Préparation de la réponse
        with open("capture_success.jpg", "rb") as img_file:
            img_data = img_file.read()
            if len(img_data) > 2 * 1024 * 1024:  # Compression si > 2MB
                img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
                _, img_data = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
                img_data = img_data.tobytes()
            
            encoded_img = base64.b64encode(img_data).decode('utf-8')

        # Nettoyage
        try:
            os.remove("capture_start.jpg")
            os.remove("capture_success.jpg")
        except Exception as e:
            print(f"Error cleaning files: {str(e)}")

        return jsonify({
            "status": "success",
            "message": "Vivacité et vérification faciale passées",
            "selfie": encoded_img,
            "success_face_id": success_faces[0]['faceId'],
            "start_face_id": start_faces[0]['faceId'],
            "is_identical": verification.get('isIdentical', False),
            "confidence": verification.get('confidence', 0)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5005) 