from flask import Flask, request, jsonify
import requests
import time
from flask_cors import CORS
import re
import logging
import cv2
import numpy as np
import os

app = Flask(__name__)
CORS(app)  # Autorise les requêtes de http://localhost:4200


# Récupère les variables
subscription_key_ocr = "742b00e495304dc4b45c496c1f1c5d41"  # Clé OCR
ocr_url = "https://stbdetectocr.cognitiveservices.azure.com/vision/v3.2/read/analyze"

subscription_key_face = "714ce515da8c4ed6a10e21cb0696cd47"  # Clé Face Detection
face_detection_url = "https://stbfacedetect.cognitiveservices.azure.com/face/v1.0/detect"
# === Détection de falsification ===
def detect_vertical_streaks_from_bytes(image_bytes, min_length=50, intensity_threshold=150, min_width=20, min_streaks=3):
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError("Impossible de décoder l'image depuis les bytes.")

        image_blurred = cv2.GaussianBlur(image, (5, 5), 0)
        _, thresholded_image = cv2.threshold(image_blurred, intensity_threshold, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        vertical_streaks = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w / h > 0.1 and h > min_length and w > min_width and h < 0.8 * image.shape[0]:
                vertical_streaks.append((x, y, w, h))

        if len(vertical_streaks) >= min_streaks:
            return False  # Falsifiée
        else:
            return True   # Authentique

    except Exception as e:
        print(f"Erreur lors de la détection de falsification : {e}")
        return False

# === Autres fonctions ===
def corriger_date_naissance(lines):
    corrected_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.search(r"تار?ي?خ? ?الولادة", line):
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if re.search(r"\d{4}", next_line):
                fusion = re.sub(r"[^\w\s\u0600-\u06FF\d]", "", line + " " + next_line)
                corrected_lines.append(fusion.strip())
                i += 2
                continue
        corrected_lines.append(line)
        i += 1

    if len(corrected_lines) >= 2:
        avant_dern_line = corrected_lines[-2].strip()
        mots = avant_dern_line.split()
        reste = " ".join(mots[2:]) if len(mots) > 2 else ""
        corrected_lines[-2] = f"تاريخ الولادة {reste}".strip()
    return corrected_lines

def detect_tunisia(lines):
    return any(re.search(r"الجمهورية التونسية", line) for line in lines)

def detect_faces_with_azure(image_bytes):
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key_face,
        'Content-Type': 'application/octet-stream'
    }
    response = requests.post(
        face_detection_url,
        headers=headers,
        data=image_bytes,
        params={'returnFaceId': 'true'}
    )
    if response.status_code == 200:
        faces = response.json()
        return faces[0]['faceId'] if faces else None
    else:
        raise Exception(f"Face detection failed: {response.text}")

# === Route OCR Recto avec vérification falsification ===
@app.route('/ocr/recto', methods=['POST'])
def handle_ocr():
    image_data = request.files['image']
    image_bytes = image_data.read()

    # Vérifier si l'image est authentique ou falsifiée
    authentique = detect_vertical_streaks_from_bytes(image_bytes)
    if not authentique:
        return jsonify({
            "message": "Image probablement falsifiée (artefacts détectés)",
            "donnees": [],
            "error": True
        }), 200

    # Lancer l'OCR
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key_ocr,
        'Content-Type': 'application/octet-stream'
    }
    response = requests.post(ocr_url, headers=headers, data=image_bytes)
    operation_url = response.headers["Operation-Location"]

    while True:
        result_response = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': subscription_key_ocr})
        result = result_response.json()

        if result['status'] == 'succeeded':
            lines = []
            for read_result in result["analyzeResult"]["readResults"]:
                for line in read_result["lines"]:
                    lines.append(line["text"])

            corrected = corriger_date_naissance(lines)

            genre = "Homme"
            if any(re.search(r"بنت", line) for line in corrected):
                genre = "أنثى"

            tunisia_detected = detect_tunisia(corrected)
            if not tunisia_detected:
                return jsonify({"message": "Elle ne s'agit pas d'un Recto de CIN!", "donnees": [], "error": True}), 200

            try:
                face_id = detect_faces_with_azure(image_bytes)
                if not face_id:
                    return jsonify({"message": "Échec de la détection de visage", "donnees": [], "error": True}), 200
            except Exception as e:
                print(f"Erreur détection visage : {str(e)}")
                return jsonify({"message": "Erreur détection visage", "donnees": [], "error": True}), 500

            if corrected:
                last_line = corrected[-1].strip()
                mots = last_line.split()
                if not last_line.startswith("مكانها"):
                    if len(mots) > 1:
                        corrected[-1] = f"مكانها {' '.join(mots[1:])}"
                    else:
                        corrected[-1] = "مكانها"

                mots_restants = " ".join(mots[1:]) if len(mots) > 1 else ""
                try:
                    verso_url = "http://localhost:5002/ocr/verso/update"
                    response = requests.post(verso_url, json={"mots_restants": mots_restants})
                    response.raise_for_status()
                    print("Mots restants envoyés avec succès")
                except requests.RequestException as e:
                    print(f"Erreur envoi mots restants : {e}")

            return jsonify({
                "message": "L'image insérée est un Recto",
                "donnees": corrected,
                "deuxième mot": mots_restants,
                "genre": genre,
                "faceId": face_id
            })

        elif result['status'] == 'failed':
            return jsonify({"message": "Échec du traitement OCR", "donnees": [], "error": True})

        time.sleep(1)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5001) 
