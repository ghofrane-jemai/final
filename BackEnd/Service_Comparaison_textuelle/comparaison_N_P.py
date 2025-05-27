from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import unicodedata
from difflib import SequenceMatcher
import threading  # Pour exécuter create_account de manière asynchrone
import requests
import logging
import os


app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

user_data_cache = {}
CACHE_EXPIRY_SECONDS = 300  # 5 minutes

# Stockage temporaire en mémoire (remplacez par une base de données en production)
user_data_cache = {
    'transliterated_data': {'الاسم': None, 'اللقب': None},
    'ocr_result': None,  # Initialisation de l'exemple de résultat OCR
    'lock': threading.Lock()  # Pour la synchronisation des accès
}


def trigger_comparison():
    with user_data_cache['lock']:
        if user_data_cache['transliterated_data'] and user_data_cache['ocr_result']:
            print("### Données avant appel à /comparaison :")
            print("#### Translittéré :")
            for key, value in user_data_cache['transliterated_data'].items():
                print(f"  - {key}: {value}")
            print("#### OCR :")
            for key, value in user_data_cache['ocr_result'].items():
                print(f"  - {key}: {value}")

            # Faire une copie des données pour la comparaison
            transliterated_data = user_data_cache['transliterated_data'].copy()
            ocr_result = user_data_cache['ocr_result'].copy()

            # Appel de l'API /comparaison
            response = requests.post("environment.apiUrls.comparaison", json={
                'transliterated_data': transliterated_data,
                'ocr_result': ocr_result
            })
            response.raise_for_status()
            comparison_result = response.json()
            print("\n### Résultat de la comparaison :")
            print(f"#### Statut : {comparison_result.get('statut', 'inconnu')}")
            if "message" in comparison_result:
                print("#### Message : %s", comparison_result["message"])
            if "errors" in comparison_result:
                print("#### Erreurs :")
                for error in comparison_result["errors"]:
                    print(f"  - {error}")
            if "detailed_errors" in comparison_result:
                print("#### Détails des erreurs :")
                for error in comparison_result["detailed_errors"]:
                    for key, value in error.items():
                        print(f"  - {key}: {value}")
            if "validation_results" in comparison_result:
                print("#### Résultats de validation :")
                for field, result in comparison_result["validation_results"].items():
                    print(f"  - **{field}**")
                    for key, value in result.items():
                        print(f"    - {key}: {value}")
            if "user_data" in comparison_result:
                print("#### Données utilisateur :")
                for key, value in comparison_result["user_data"].items():
                    print(f"  - {key}: {value}")
            if "validation_details" in comparison_result:
                print("#### Détails de validation :")
                for field, result in comparison_result["validation_details"].items():
                    print(f"  - **{field}**")
                    for key, value in result.items():
                        print(f"    - {key}: {value}")

@app.route('/transliterate-names', methods=['POST'])
def receive_transliterated_name_or_names():
    data = request.get_json()
    prenom_translittere = data.get('الاسم', '')
    nom_translittere = data.get('اللقب', '')
    dob_translittere = data.get('تاريخ الولادة', '')  # Récupérer la date de naissance translittérée
    genre_translittere = data.get('الجنس', '')  # Récupérer le genre translittéré

    with user_data_cache['lock']:
        if user_data_cache['transliterated_data'] is None:
            user_data_cache['transliterated_data'] = {'الاسم': None, 'اللقب': None, 'تاريخ الولادة': None, 'الجنس':None}

        if prenom_translittere:
            user_data_cache['transliterated_data']['الاسم'] = prenom_translittere
        if nom_translittere:
            user_data_cache['transliterated_data']['اللقب'] = nom_translittere
        if dob_translittere:
            user_data_cache['transliterated_data']['تاريخ الولادة'] = dob_translittere  # Stocker la date de naissance translittérée
        if genre_translittere:
            user_data_cache['transliterated_data']['الجنس'] = genre_translittere  # Stocker le genre translittéré

    # 🔁 Forcer le rappel de l'extraction OCR, même si l'image est la même
    # Simule un appel HTTP vers l'extraction OCR en renvoyant les mêmes données OCR stockées
    with user_data_cache['lock']:
        existing_ocr_data = user_data_cache.get('ocr_result')
    
    if existing_ocr_data:
        # Simuler un rappel de l'endpoint /ocr-extraction avec les mêmes données
        threading.Thread(target=lambda: requests.post(
            'http://localhost:5003/ocr-extraction',
            json={'ocr_result': [f"{key} {value}" for key, value in existing_ocr_data.items()]}
        )).start()

    # Réponse personnalisée
    if prenom_translittere and nom_translittere and dob_translittere:
        return jsonify({
            "message": "Prénom, nom et date de naissance translittérés reçus avec succès",
            "الاسم": prenom_translittere,
            "اللقب": nom_translittere,
            "تاريخ الولادة": dob_translittere,
            "الجنس": genre_translittere
        })
    elif prenom_translittere and nom_translittere and dob_translittere and genre_translittere:
        return jsonify({
            "message": "Prénom et nom translittérés reçus avec succès",
            "الاسم": prenom_translittere,
            "اللقب": nom_translittere,
            "تاريخ الولادة": dob_translittere,
            "الجنس": genre_translittere
        })
    elif prenom_translittere:
        return jsonify({
            "message": "Prénom translittéré reçu avec succès",
            "الاسم": prenom_translittere
        })
    elif nom_translittere:
        return jsonify({
            "message": "Nom translittéré reçu avec succès",
            "اللقب": nom_translittere
        })
    elif dob_translittere:
        return jsonify({
            "message": "Date de naissance translittérée reçue avec succès",
            "تاريخ الولادة": dob_translittere
        })
    elif genre_translittere:
        return jsonify({
            "message": "Genre translittérée reçue avec succès",
            "الجنس": genre_translittere
        })
    else:
        return jsonify({
            "message": "Aucune donnée de translittération reçue"
        })


@app.route('/ocr-extraction', methods=['POST'])
def receive_ocr_extraction():
    data = request.get_json()
    ocr_result = data.get('ocr_result', [])
    genre = data.get('genre', '')  # Récupérer le genre séparément si fourni

    if ocr_result:
        filtered_result = {}
        for value in ocr_result:
            words = value.split()
            if words and words[0] in ('الاسم', 'اللقب'):
                key = words[0]
                rest = ' '.join(words[1:])
                filtered_result[key] = rest
            elif len(words) >= 2 and f'{words[0]} {words[1]}' == 'تاريخ الولادة':
                key = 'تاريخ الولادة'
                rest = ' '.join(words[2:])
                filtered_result[key] = rest
            elif len(words) >= 2 and words[0] in ('الجنس', 'النوع'):  
                key = 'الجنس'  # ou 'النوع' selon votre convention
                rest = ' '.join(words[1:])
                filtered_result[key] = rest

        # Si le genre n'a pas été trouvé dans ocr_result, utiliser la valeur passée séparément
        if 'الجنس' not in filtered_result and genre:
            filtered_result['الجنس'] = genre

        with user_data_cache['lock']:
            user_data_cache['ocr_result'] = filtered_result
            user_data_cache['genre'] = genre  # Stocker le genre pour une utilisation future

        # Déclencher la comparaison si les deux données sont présentes
        with user_data_cache['lock']:
            if user_data_cache['transliterated_data']:
                threading.Thread(target=trigger_comparison).start()

        return jsonify({
            "message": "Résultats OCR reçus avec succès",
            "ocr_result": filtered_result,
            "genre": filtered_result.get('الجنس', genre)  # Retourner le genre
        })




@app.route('/get-comparison-result', methods=['GET'])
def get_comparison_result():
    with user_data_cache['lock']:
        # Vérifier si les données de comparaison existent
        if user_data_cache['transliterated_data'] and user_data_cache['ocr_result']:
            # Vérification des champs requis
            required_fields = ['الاسم', 'اللقب', 'تاريخ الولادة', 'الجنس']
            missing_fields = [
                field for field in required_fields
                if field not in user_data_cache['transliterated_data'] or field not in user_data_cache['ocr_result']
            ]
            
            if missing_fields:
                return jsonify({
                    "statut": "not_ok",
                    "message": "Champs manquants",
                    "missing_fields": missing_fields
                })

            # Récupérer le statut de la comparaison
            statut = user_data_cache.get('comparison_status', 'not_ok')
            
            # Afficher le statut pour le débogage
            print(f"### Statut de la comparaison avant envoi au front : {statut} ###")
            
            return jsonify({
                "statut": statut,
                "message": "Tous les champs sont présents",
                "comparison_status": statut  # Inclure le statut de la comparaison
            })
        
        # Si les données ne sont pas disponibles
        return jsonify({
            "statut": "not_ok",
            "message": "Données de comparaison non trouvées"
        })



@app.route('/comparaison', methods=['POST'])
def comparaison():
    try:
        print("Appel à /comparaison reçu.")
        data = request.get_json()
        print("Données reçues : %s", data)

        transliterated_data = data.get('transliterated_data')
        ocr_result = data.get('ocr_result')

        # Vérification des données reçues
        if not transliterated_data or not ocr_result:
            print("Erreur : Données incomplètes (transliterated_data ou ocr_result manquant)")
            return jsonify({"message": "Erreur serveur", "error": "Données incomplètes"}), 500

        # Ignorer la comparaison si des champs requis sont manquants
        required_fields = ['الاسم', 'اللقب', 'تاريخ الولادة', 'الجنس']
        missing_fields = [
            field for field in required_fields
            if field not in transliterated_data or field not in ocr_result
        ]
        if missing_fields:
            logging.warning(f"Champs manquants : {missing_fields}")
            return jsonify({
                "message": "Comparaison ignorée : champs manquants",
                "missing_fields": missing_fields,
                "statut": "not_ok"  # Ajouter le statut ici
            }), 200

        # Si ocr_result est une liste, transformez-la en dictionnaire
        if isinstance(ocr_result, list):
            print("ocr_result est une liste, transformation en dictionnaire...")
            ocr_extracted = {}
            for field in ['الاسم', 'اللقب', 'تاريخ الولادة', 'الجنس']:
                matching_items = [item for item in ocr_result if item.startswith(field)]
                if matching_items:
                    if field == 'تاريخ الولادة':
                        ocr_extracted[field] = ' '.join(matching_items[0].split(' ')[1:])
                    else:
                        ocr_extracted[field] = matching_items[0].split(' ', 1)[1]
                else:
                    ocr_extracted[field] = ''  # ou une valeur par défaut pertinente
                    logging.warning(f"Champ {field} non trouvé dans ocr_result")
            print("ocr_extracted : %s", ocr_extracted)
        else:
            ocr_extracted = ocr_result  # Si c'est déjà un dictionnaire
            print("ocr_result est déjà un dictionnaire : %s", ocr_extracted)

        # Normaliser les clés
        normalized_transliterated = {
            'الاسم': transliterated_data.get('الاسم', ''),
            'اللقب': transliterated_data.get('اللقب', ''),
            'تاريخ الولادة': transliterated_data.get('تاريخ الولادة', ''),
            'الجنس': transliterated_data.get('الجنس', '')
        }
        print("Données translittérées normalisées : %s", normalized_transliterated)

        # Comparaison des champs
        errors = []
        detailed_results = []
        validation_results = {}
        for field in ['الاسم', 'اللقب', 'تاريخ الولادة', 'الجنس']:
            t_value = normalize_arabic(normalized_transliterated.get(field, '')).strip().lower()
            o_value = normalize_arabic(ocr_extracted.get(field, '')).strip().lower()

            # Vérification présence
            if not t_value or not o_value:
                errors.append(f"Champ {field} manquant")
                logging.warning(f"Champ {field} manquant")
                continue

            # Calcul similarité
            if field == 'تاريخ الولادة':
                t_date_parts = extract_date_parts(t_value)
                o_date_parts = extract_date_parts(o_value)
                is_similar = (t_date_parts == o_date_parts)
                similarity = 1.0 if is_similar else 0.0
            else:
                is_similar, similarity = similar(t_value, o_value)
            similarity_percentage = round(similarity * 100, 2)

            validation_results[field] = {
                "transliterated": normalized_transliterated.get(field),
                "ocr_extracted": ocr_extracted.get(field),
                "normalized_transliterated": t_value,
                "normalized_ocr": o_value,
                "similarity": f"{similarity_percentage}%",
                "is_similar": is_similar
            }
            if not is_similar:
                detailed_results.append(validation_results[field])

        # Déterminer le statut final
        # Déterminer le statut final
        statut = "ok" if not errors and not detailed_results else "not_ok"

        # Stocker le statut dans le cache pour une utilisation future
        user_data_cache['comparison_status'] = statut

        # Afficher le statut dans la console du backend
        print(f"### Statut final de la comparaison : {statut.upper()} ###")

        # Réponse sans erreur 400 si pas de similarité
        if errors:
            print("Erreur de validation : Erreurs présentes")
            return jsonify({
                "message": "Échec de la validation des noms",
                "errors": errors,
                "detailed_errors": detailed_results,
                "validation_results": validation_results,
                "statut": statut  # Inclure le statut ici
            }), 400
        else:
            if detailed_results:
                logging.warning("Écart de similarité détecté")
                return jsonify({
                    "message": "Écart de similarité détecté",
                    "detailed_results": detailed_results,
                    "validation_results": validation_results,
                    "statut": statut  # Inclure le statut ici
                }), 200
            else:
                print("Validation réussie")
                return jsonify({
                    "message": "succès",
                    "user_data": {
                        "الاسم": normalized_transliterated['الاسم'],
                        "اللقب": normalized_transliterated['اللقب'],
                        "تاريخ الولادة": normalized_transliterated['تاريخ الولادة'],
                        "الجنس": normalized_transliterated['الجنس'],
                    },
                    "validation_details": validation_results,
                    "statut": statut  # Inclure le statut ici
                }), 200

    except Exception as e:
        print(f"Erreur dans la route /comparaison : {str(e)}")
        return jsonify({"message": "Erreur serveur", "error": str(e), "statut": "not_ok"}), 500



def extract_date_parts(date_str: str):
    # Supprimer les préfixes non pertinents
    date_str = date_str.replace("الولادة", "").strip()
    
    # Gérer différents formats de date
    parts = date_str.split()
    if len(parts) == 3:
        day, month, year = parts
        return (day, month, year)
    elif "/" in date_str:
        # Format : jj/mm/aaaa
        try:
            day, month, year = date_str.split("/")
            return (day, month, year)
        except ValueError:
            logging.warning(f"Format de date invalide : {date_str}")
            return None
    else:
        logging.warning(f"Structure de date inattendue : {date_str}")
        return None



def normalize_arabic(text):
    if not text:
        return text
        
    text = unicodedata.normalize('NFKD', text)
    replacements = {
        '\u0643': '\u0643',  # ك (kaf) standard
        '\u0649': '\u0649',  # ى (alif maqsura) standard
        '\u0622': '\u0627',  # آ -> ا
        '\u0623': '\u0627',  # أ -> ا
        '\u0625': '\u0627',  # إ -> ا
        '\u0629': '\u0647',  # ة -> ه
        '\u0623\u0654': '\u0623',  # alef avec hamza en bas -> alef avec hamza
        '\u0621\u0654': '\u0623',  # hamza suivi de alef en bas -> alef avec hamza
        '\u061B': '\u0627',  # alef avec hamza en haut -> alef
        '\u0654': '',  # Supprimer le point en dessous (pour gérer "ٕ")
        '\u0627\u0648\u062a': '\u0648\u062a',  # أوت -> اوت (pour la date de naissance)
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Supprimer l'article défini "ال" si pertinent
    # text = text.replace("ال", "")  # Décommenter si nécessaire
    
    return text



def similar(a, b, threshold=0.66):
    """Compare deux chaînes avec un seuil de similarité"""
    if not a or not b:
        return False, 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= threshold, ratio

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5003) 
