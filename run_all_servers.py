# run_all_servers.py
import subprocess

# Lancer server.py
subprocess.Popen(["python", "D:/3emeISAMM/PFE/V2 - Copie/BackEnd/Service_Serveur_global/server.py"])

# Lancer Azure_OCR_recto.py
subprocess.Popen(["python", "D:/3emeISAMM/PFE/V2 - Copie/BackEnd/Service_Recto/azure_ocr_recto.py"])


subprocess.Popen(["python", "D:/3emeISAMM/PFE/V2 - Copie/BackEnd/Service_transliteration/yamli.py"])

# Lancer Azure_OCR_verso.py
subprocess.Popen(["python", "D:/3emeISAMM/PFE/V2 - Copie/BackEnd/Service_Verso/azure_ocr_verso.py"])

# Lancer comparaison_N_P.py
subprocess.Popen(["python", "D:/3emeISAMM/PFE/V2 - Copie/BackEnd/Service_Comparaison_textuelle/comparaison_N_P.py"])
subprocess.Popen(["python", "D:/3emeISAMM/PFE/V2 - Copie/BackEnd/Service_Verification_faciale/verifyface.py"])

# Lancer live.py
#subprocess.Popen(['C://Users//user//AppData//Local//Programs//Python//Python37//python.exe', 'D://3emeISAMM//PFE//Code//face_liveness_detection-Anti-spoofing//live.py'])

