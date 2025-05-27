from flask import Flask, request, jsonify
import requests
import time
import logging
import cv2
import numpy as np
from flask_cors import CORS
from PIL import Image
from pyzbar.pyzbar import decode

import io
import os


app = Flask(__name__)
CORS(app)
mots_restants_cache = ""



subscription_key_ocr = os.getenv("SUBSCRIPTION_KEY_OCR")
ocr_url = os.getenv("OCR_URL")


def detect_face(image_data):
    image_bytes = image_data.read()
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return len(faces) > 0

def decode_barcode(image_data):
    image_data.seek(0)
    try:
        image = Image.open(image_data)
        decoded_objects = decode(image)
        return [obj.data.decode("utf-8") for obj in decoded_objects]
    except Exception as e:
        print("Erreur de décodage du code-barres: {}".format(e))
        return []

@app.route('/ocr/verso', methods=['POST'])
def handle_ocr():
    try:
        if 'image' not in request.files:
            print("Aucun fichier d'image fourni")
            return jsonify({
                "message": "Aucun fichier d'image fourni",
                "donnees": [],
                "is_valid": False,
                "error": "Aucune image fournie"
            }), 400

        image_data = request.files['image']
        print("Fichier d'image reçu : {}".format(image_data.filename))

        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Content-Type': 'application/octet-stream'
        }

        try:
            image_data.seek(0)
            response = requests.post(ocr_url, headers=headers, data=image_data)
            response.raise_for_status()
        except requests.RequestException as e:
            print("Erreur Azure OCR : {}".format(e))
            return jsonify({"message": "Erreur Azure OCR", "donnees": []}), 500

        operation_url = response.headers["Operation-Location"]
        print("URL de l'opération : {}".format(operation_url))

        while True:
            try:
                result_response = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': subscription_key})
                result_response.raise_for_status()
            except requests.RequestException as e:
                print("Erreur récupération résultat : {}".format(e))
                return jsonify({"message": "Erreur récupération résultat", "donnees": []}), 500

            result = result_response.json()
            if result['status'] == 'succeeded':
                lines = []
                for read_result in result["analyzeResult"]["readResults"]:
                    for line in read_result["lines"]:
                        lines.append(line["text"])

                image_data.seek(0)
                face_detected = detect_face(image_data)
                text_contains_alm = any("الأم" in line for line in lines)

                barcode_data = decode_barcode(image_data)  # Décode le code-barres

                if not face_detected and text_contains_alm:
                    if len(lines) >= 4 and mots_restants_cache:
                        mots = lines[4].split()
                        if mots:
                            lines[4] = f"{mots_restants_cache} {' '.join(mots[1:])}"

                    print("Il s'agit bien d'une image verso, retour des données")
                    return jsonify({
                        "message": "Traitement OCR réussi",
                        "donnees": lines,
                        "code_barres": barcode_data
                    })

                else:
                    print("Conditions non remplies : visage détecté ou 'الأم' non trouvé.")
                    return jsonify({"message": "Conditions non remplies", "donnees": [], "code_barres": barcode_data}), 200

            elif result['status'] == 'failed':
                print("Échec du traitement OCR")
                return jsonify({"message": "Échec du traitement OCR", "donnees": []}), 500

            time.sleep(1)

    except Exception as e:
        print("Erreur inattendue : {}".format(e))
        return jsonify({"message": "Erreur inattendue", "donnees": []}), 500

@app.route('/ocr/verso/update', methods=['POST'])
def update_verso():
    data = request.get_json()
    mots_restants = data.get("mots_restants")
    if mots_restants:
        global mots_restants_cache
        mots_restants_cache = mots_restants
        return jsonify({"message": "Mots restants mis à jour"}), 200
    else:
        return jsonify({"message": "Aucuns mots restants fournis"}), 400

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5002) 
