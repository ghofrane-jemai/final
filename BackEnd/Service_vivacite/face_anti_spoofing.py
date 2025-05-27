import random
import cv2
import imutils
import f_liveness_detection
import questions
import time
import os
import logging


# Instancier la caméra
cv2.namedWindow('Detection de vivacite')
cam = cv2.VideoCapture(0)

# Vérifier que la caméra est ouverte
if not cam.isOpened():
    raise Exception("Erreur: Impossible d'ouvrir la caméra")

# Paramètres
COUNTER, TOTAL = 0, 0
counter_ok_questions = 0
counter_ok_consecutives = 0
limit_consecutives = 3
limit_questions = 6
counter_try = 0
limit_try = 50

# Flags pour prendre une seule fois la photo au bon moment
photo_start_taken = False
photo_success_taken = False

def clean_old_images():
    """
    Supprime les anciennes images générées lors des exécutions précédentes.
    """
    image_files = [
        "capture_start.jpg",
        "capture_success.jpg"
    ]
    
    for file_name in image_files:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"Suppression réussie : {file_name}")
            except Exception as e:
                print(f"Échec de la suppression de {file_name} : {str(e)}")


def show_image(cam, text, color=(0, 0, 255)):
    """Affiche une image avec un texte"""
    ret, im = cam.read()
    if not ret:
        print("Avertissement: Impossible de lire l'image de la caméra")
        return None
    im = imutils.resize(im, width=720)
    cv2.putText(im, text, (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)
    return im

# Supprimer les anciennes images avant de commencer
clean_old_images()

# ----------- Capture dès que la caméra est ouverte --------------
ret, im = cam.read()
if ret:
    im = imutils.resize(im, width=720)
    cv2.imwrite("capture_start.jpg", im)
    print("Photo prise au démarrage: capture_start.jpg")
    photo_start_taken = True
else:
    print("Erreur: Impossible de capturer l'image de démarrage")

# ---------------------------------------------------------------

for i_questions in range(0, limit_questions):
    # Générer une question aléatoire
    index_question = random.randint(0, 2)
    question = questions.question_bank(index_question)

    # Afficher la question pendant 3 secondes
    start_time = time.time()
    while time.time() - start_time < 1:  # Attendre 4 secondes
        im = show_image(cam, question)
        if im is not None:
            cv2.imshow('Detection de vivacite', im)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    # Continuer à afficher la question jusqu'à la fin du défi
    for i_try in range(limit_try):
        ret, im = cam.read()
        if not ret:
            continue
            
        im = imutils.resize(im, width=720)
        im = cv2.flip(im, 1)
        
        TOTAL_0 = TOTAL
        out_model = f_liveness_detection.detect_liveness(im, COUNTER, TOTAL_0)
        TOTAL = out_model['total_blinks']
        COUNTER = out_model['count_blinks_consecutives']
        dif_blink = TOTAL - TOTAL_0
        blinks_up = 1 if dif_blink > 0 else 0

        challenge_res = questions.challenge_result(question, out_model, blinks_up)

        im = show_image(cam, question)
        if im is not None:
            cv2.imshow('Detection de vivacite', im)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if challenge_res == "pass":
            im = show_image(cam, question + " : ok")
            if im is not None:
                cv2.imshow('Detection de vivacite', im)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            counter_ok_consecutives += 1
            if counter_ok_consecutives == limit_consecutives:
                counter_ok_questions += 1
                counter_try = 0
                counter_ok_consecutives = 0
                break
        elif challenge_res == "fail":
            counter_try += 1
            show_image(cam, question + " : fail")
        elif i_try == limit_try - 1:
            break

# ---------------------- Résultat final -----------------------------

if counter_ok_questions == limit_questions:
    print("Vivacite avec succes")
    im = show_image(cam, "Vivacite avec succes", color=(0, 255, 0))
    if im is not None:
        cv2.imshow('Detection de vivacite', im)
    
    
    # Attendre 1 seconde avant de capturer la photo
    cv2.waitKey(1000)

    # Afficher un message "Je vais prendre une photo de toi"
    im = show_image(cam, "Je vais prendre une photo de toi...", color=(255, 255, 255))
    cv2.imshow('Detection de vivacite', im)
    cv2.waitKey(2000)  # Attendre 2 secondes pour que l'utilisateur soit prêt

    # Capturer l'image
    ret, captured_image = cam.read()
    if ret:
        captured_image = imutils.resize(captured_image, width=720)
        cv2.imwrite("capture_success.jpg", captured_image)  # Sauvegarder l'image dans un fichier
        print("Photo prise et sauvegardée sous 'capture_success.jpg'")
else:
    im = show_image(cam, "Vivacite echouee", color=(0, 0, 255))
    cv2.imshow('Detection de vivacite', im)
    print("Vivacite echouee")

# Attendre 1 seconde et fermer la fenêtre
cv2.waitKey(1000)  # Attendre 1 seconde

# --------------------------------------------------------------------

# Nettoyage
cv2.destroyAllWindows()  # Fermer les fenêtres
cam.release()  # Libérer la caméra

# Vérification finale des images
required_images = [
    "capture_start.jpg",
    "capture_success.jpg"
]
missing_images = [img for img in required_images if not os.path.exists(img) or os.path.getsize(img) == 0]

if missing_images:
    print(f"ATTENTION: Images manquantes ou vides: {', '.join(missing_images)}")
else:
    print("Toutes les images recadrées ont été correctement enregistrées")