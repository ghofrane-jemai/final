from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from flask import Flask
from flask_cors import CORS
from datetime import datetime, timedelta
import base64
import requests
import json
import re
import logging
import os
from flask import Flask
app = Flask(__name__)
CORS(app)

def transliterate_with_yamli(text):
    api_url = "https://api.yamli.com/transliterate.ashx"
    params = {
        "tool": "api",
        "account_id": "000006",
        "prot": "https",
        "hostname": "www.yamli.com",
        "path": "/clavier-arabe/",
        "build": "5515",
        "sxhr_id": "7"
    }
    words = text.split()
    transliterated_words = []

    for word in words:
        params["word"] = word
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()  # Cela soulèvera une exception pour les codes d'état HTTP non réussis (4xx, 5xx)
            if response.status_code == 200:
                result_data = response.text.split('dataCallback(')[1].split(');')[0]
                result_json = json.loads(result_data)["data"]
                if result_json:
                    choices = result_json.split('|')
                    first_choice = choices[0].split('/')[0]
                    filtered_choice = re.sub(r'[^ء-ي]', '', first_choice)
                    transliterated_words.append(filtered_choice)
                else:
                    transliterated_words.append(word)
            else:
                transliterated_words.append(f"Erreur {response.status_code}")
        except requests.exceptions.RequestException as e:
            # En cas d'erreur réseau
            transliterated_words.append(f"Erreur réseau: {str(e)}")
        except Exception as e:
            # En cas d'erreur générale
            transliterated_words.append(f"Erreur: {str(e)}")

    return ' '.join(transliterated_words)
@app.route('/transliterate', methods=['POST'])
def transliterate():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Aucun JSON reçu'}), 400
    
    # Vérifier si l'un des champs est présent
    firstName = data.get('firstName', '')
    lastName = data.get('lastName', '')

    if not firstName and not lastName:
        return jsonify({'error': 'Au moins l\'un des champs "firstName" ou "lastName" est requis'}), 400

    response_data = {}

    if firstName:
        resultFirstName = transliterate_with_yamli(firstName)
        response_data['الاسم'] = resultFirstName
        print(f"Prénom reçu pour translittération : {firstName}")

    if lastName:
        resultLastName = transliterate_with_yamli(lastName)
        response_data['اللقب'] = resultLastName
        print(f"Nom reçu pour translittération : {lastName}")

    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response



@app.route('/transliterate', methods=['OPTIONS'])
def handle_preflight():
    response = jsonify({'message': 'CORS preflight passed'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5007) 