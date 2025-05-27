# -------------------------------------- profile_detection ---------------------------------------
detect_frontal_face = 'profile_detection/haarcascades/haarcascade_frontalface_alt.xml'
detect_perfil_face = 'profile_detection/haarcascades/haarcascade_profileface.xml'



# definir la relacion de aspecto del ojo EAT
# definir el numero de frames consecutivos que debe estar por debajo del umbral
EYE_AR_THRESH = 0.23 #baseline
EYE_AR_CONSEC_FRAMES = 1

# eye landmarks
eye_landmarks = "blink_detection/model_landmarks/shape_predictor_68_face_landmarks.dat"