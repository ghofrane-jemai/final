import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Component, ElementRef, ViewChild } from '@angular/core';

enum UserFields {
  FirstName = 'firstName',
  LastName = 'lastName',
  Country = 'country',
  City = 'city',
  Dob = 'dob',
  Gender = 'gender',
  IdCardFront = 'idCardFront',
  IdCardBack = 'idCardBack',
  Selfie = 'selfie'
}

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent {
  UserFields = UserFields; // Exposer l'énumération
  @ViewChild('lastNameInput') lastNameInput: ElementRef | null = null; // Référence pour le champ lastName
  @ViewChild('videoElement') videoElement: ElementRef | null = null;
  @ViewChild('canvasElement') canvasElement: ElementRef | null = null;
  // Gestion des étapes
  currentStep: number = 1;
  steps = [
    { number: 1, title: 'Données personnelles', completed: false },
    { number: 2, title: 'Vivacité', completed: false },
    { number: 3, title: 'Insertion CIN', completed: false },
    { number: 4, title: 'Validation', completed: false }

  ];


  
user = {
    firstName: '',
    lastName: '',
    email: '', // Nouveau champ
    phone: '', // Nouveau champ
    postalCode: '', // Nouveau champ
    address: '', // Nouveau champ
    country: 'Tunisie',
    city: '',
    dob: '',
    dobArabic:'',
    gender: '',
    genderArabic:'',
    idCardFront: '' as string | null,
    idCardBack: '' as string | null,
    extractedDataFront: {},
    extractedDataBack: {},
    selfie: '' as string | null,
    rectoFaceId: '' as string | null,
    successFaceId:'' as string | null,
    numeroUniqueCB: '',
    dateDelivranceCB: '',
    numeroUniqueExtrait: '' as string | null,
    Datededelivrance: '' as string | null,
};

  ageError: string = '';
  dateError: string = '';

  ngOnInit() {
    this.onCountryChange(); // pour initialiser la liste des villes dès le début
  }
  cities: string[] = [];
  selectedVersoImage: File | null = null;
  selectedVersoImageHash: string | null = null;
  isSubmitting = false;
  livenessStatus: string = '';
  successFaceId: string = '';
  previousFirstname: string = '';
  previousLastname: string = '';

  citiesByCountry: { [key: string]: string[] } = {
      "Tunisie": ["Nabeul", "Qurbus", "Kélibia", "Yasmine Hammamet", "Kerkouane", "Al Huwariyah", 
        "Kairouan", "Douz", "Nefta", "Ksar Ghilane", "Gafsa", "Degueche", "Shabikah", "Tozeur", 
        "Bizerte", "Takrouna", "Djebba", "Midoun", "Djerba Ajim", "Ghizen", "Arkou", "Houmt Souk", 
        "Aghir", "Hara Sghira Er Riadh", "Mellita", "Souk Houmet", "Mezraia", "Djerba Midun", 
        "Ksar Hadada", "Tataouine Nord", "Tataouine Ville", "Ghomrassen", "Testour", "Kesra", 
        "Beja, Tunisie", "Le Kef", "Makthar", "Sabria", "Toujane", "Zaghouan", "Zriba", "Matmata", 
        "Gabès Médina", "Tamezret", "La Marsa", "La Goulette", "Tunis", "Carthage", "Sidi Bou Saïd", 
        "Sbeïtla", "Monastir", "Sahline", "Ariana, Tunisie", "CHENINI", "Douiret", "Bani Khedeche", 
        "Ksar Ouled Brahim", "Sangho", "Médine", "Mahboubine", "Khalfallah", "Ksar Hallouf", "Zarzis", 
        "Guellala", "Hammam Sousse", "Hammamet", "Sousse", "M'saken", "El Jem", "Hiboun", "Mahdia"],
};


  constructor(private http: HttpClient) {}
nextStep(): void {
    if (this.currentStep < this.steps.length && this.validateCurrentStep()) {
      this.currentStep++;
      this.updateSteps();
    }
  }

  prevStep(): void {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.updateSteps();
    }
  }

  updateSteps(): void {
    this.steps.forEach(step => {
      step.completed = step.number < this.currentStep;
    });
  }

validateCurrentStep(): boolean {
  switch (this.currentStep) {
    case 1: // Données personnelles
      return this.validatePersonalInfo();
    case 2: // Vivacité
      return this.user.selfie !== null;
    case 3: // Insertion CIN
      return this.user.idCardFront !== null && this.user.idCardBack !== null;
    case 4: // Validation KYC
      return true; // Toujours accessible une fois les étapes précédentes validées
    default:
      return false;
  }
}
  validatePersonalInfo(): boolean {
    return (
      this.user.firstName !== '' &&
      this.user.lastName !== '' &&
      this.user.email !== '' &&
      this.user.phone !== '' &&
      this.user.postalCode !== '' &&
      this.user.address !== '' &&
      this.user.country !== '' &&
      this.user.city !== '' &&
      this.user.dob !== '' &&
      this.user.gender !== ''
    );
  }
  validateForm(): boolean {
    return this.validatePersonalInfo() && 
           this.user.selfie !== null &&
           this.user.idCardFront !== null && 
           this.user.idCardBack !== null;
  }

  validateEmail(email: string): boolean {
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(String(email).toLowerCase());
}


onFileChangeRecto(event: Event, field: UserFields) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
        const file = input.files[0];
        // Réinitialiser les données extraites et autres champs liés au recto
        this.user.extractedDataFront = {}; // Réinitialiser les résultats extraits
        this.user.rectoFaceId = null;     // Réinitialiser le faceId du recto
        this.user.idCardFront = null;     // Réinitialiser l'image du recto en base64
        this.user.numeroUniqueExtrait = null;

        // Vérification de l'extension du fichier
        const allowedExtensions = ['jpg', 'jpeg', 'png'];
        const fileExtension = file.name.split('.').pop()?.toLowerCase();
        if (!allowedExtensions.includes(fileExtension || '')) {
            alert('Erreur : Seuls les fichiers JPG, JPEG et PNG sont autorisés.');
            return; // Arrêter le traitement si l'extension n'est pas valide
        }

        // Appeler le serveur pour traiter l'image
        const formData = new FormData();
        formData.append('image', file);
        this.http.post('http://localhost:5001/ocr/recto', formData).subscribe(
            (response: any) => {
                console.log('Résultat OCR Recto:', response);
                
                // Ajoutez cette vérification au début du traitement de la réponse
                if (response.message === "Image probablement falsifiée (artefacts détectés)") {
                    alert(response.message);
                    return;
                }
                
                // Le reste de votre code existant...
                const ligne3 = response.donnees[2];

                // Supposons que le numéro unique soit constitué de chiffres
                const match = ligne3.match(/\d+/); // extrait la première séquence de chiffres

                this.user.numeroUniqueExtrait = match ? match[0] : null; // Stockage direct dans user

                console.log('Numéro unique extrait et stocké:', this.user.numeroUniqueExtrait);
                if (response.faceId) {
                    this.user.rectoFaceId = response.faceId; // Stocker le faceId de recto
                    console.log('Face ID de recto stocké avec succès :', this.user.rectoFaceId);
                    // Vérifier les visages si un success_face_id existe déjà
                    if (this.user.successFaceId) {
                        this.verifyFacesAndSubmit();
                    }
                } else {
                    console.error('Aucun faceId trouvé dans la réponse.');
                }
                if (!response.error) {
                    alert('Succès : ' + response.message);
                }
                // Stocker le genre en arabe
                this.user.gender = response.genre === 'homme' ? 'ذكر' : 'أنثى';
                if (response.error) {
                    alert('Erreur : ' + response.message);
                    return;
                }
                // Convertir l'image en base64 et stocker
                this.getBase64Image(file).then(base64 => {
                    this.user.idCardFront = base64;
                });
                // Stocker les données extraites
                this.user.extractedDataFront = response.donnees;
                // Envoyer les données à comparaison_N_P.py
                const ocrData = {
                    'ocr_result': this.user.extractedDataFront,
                    'genre': this.user.gender // Envoyer le genre au serveur
                };
                this.http.post('http://localhost:5003/ocr-extraction', ocrData).subscribe(
                    (response: any) => {
                        console.log(`Résultats d'extraction OCR envoyés au serveur Python :`, response);
                    },
                    error => {
                        console.error('Erreur lors de l\'envoi des données à comparaison_N_P.py (OCR Recto):', error);
                    }
                );
                if (this.selectedVersoImage) {
                    this.processVersoImage(this.selectedVersoImage);
                }
            },
            error => {
                console.error('Erreur lors du traitement OCR Recto :', error);
            }
        );
    }
}
  
processVersoImage(image: File) {
  // Nettoyer les données précédentes du Verso
  this.user.idCardBack = null;
  this.user.extractedDataBack = {};

  const formData = new FormData();
  formData.append('image', image);
  

  this.http.post('http://localhost:5002/ocr/verso', formData)
      .subscribe((response: any) => {
          console.log('Résultat OCR Verso:', response);
          if (response.message === "Conditions non remplies") {
            alert("Erreur : Elle ne s'agit pas d'un Verso de CIN");
            return;
          }
          this.getBase64Image(image).then(base64 => {
              this.user.idCardBack = base64;
          });
          this.user.extractedDataBack = response.donnees; // Stocker les résultats extractés
      }, error => {
          console.error('Erreur lors du traitement OCR Verso:', error);
      });
}


onFileChangeVerso(event: Event, field: UserFields) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
        this.selectedVersoImage = input.files[0]; // Stocker l'image Verso
        this.selectedVersoImageHash = this.selectedVersoImage.name + this.selectedVersoImage.lastModified;
        const file = input.files[0];
                // Vérification de l'extension du fichier
                const allowedExtensions = ['jpg', 'jpeg', 'png'];
                const fileExtension = file.name.split('.').pop()?.toLowerCase();
                if (!allowedExtensions.includes(fileExtension || '')) {
                    alert('Erreur : Seuls les fichiers JPG, JPEG et PNG sont autorisés.');
                    return; // Arrêter le traitement si l'extension n'est pas valide
                }
        this.user.idCardBack = null;
        this.user.extractedDataBack = {};
        // Appeler le serveur pour traiter l'image
        const formData = new FormData();
        formData.append('image', file);
        

        this.http.post('http://localhost:5002/ocr/verso', formData)
            .subscribe((response: any) => {
              console.log('Résultat OCR Verso:', response);

              // Accéder à la ligne 4 dans le tableau `donnees`
              const ligne4 = response.donnees[4];

              // Vérifier qu'elle existe et contient une date
            if (ligne4) {
                const match = ligne4.match(/(\d{2}\s\S+\s\d{4})/);
                this.user.Datededelivrance = match ? match[1] : null; // Stockage direct
                console.log('Date de délivrance extraite:', this.user.Datededelivrance);
            } else {
                console.log("La ligne 4 n'existe pas dans les données OCR.");
              }

                console.log('Données code-barres:', response.code_barres);
                if (response.code_barres && response.code_barres.length > 0) {
                  const barcode = response.code_barres[0]; // Prend le premier code-barres
                  const numeroUniqueCB = barcode.substring(0, 8);
                  const dateRaw = barcode.slice(-6); // 6 derniers chiffres

                  const jour = dateRaw.substring(0, 2);
                  const mois = dateRaw.substring(2, 4);
                  const yy = parseInt(dateRaw.substring(4, 6), 10);

                  const annee = yy < 25 ? `20${yy.toString().padStart(2, '0')}` : `19${yy.toString().padStart(2, '0')}`;

                  const moisArabe: { [key: string]: string } = {
                    '01': 'جانفي',
                    '02': 'فيفري',
                    '03': 'مارس',
                    '04': 'أفريل',
                    '05': 'ماي',
                    '06': 'جوان',
                    '07': 'جويلية',
                    '08': 'أوت',
                    '09': 'سبتمبر',
                    '10': 'أكتوبر',
                    '11': 'نوفمبر',
                    '12': 'ديسمبر'
                  };

                  const moisNom = moisArabe[mois] || 'غير معروف';
                  const dateDelivranceCB = `${jour} ${moisNom} ${annee}`;

                  console.log("Numéro unique (Code-barres):", numeroUniqueCB);
                  console.log("Date de délivrance (Code-barres):", dateDelivranceCB);

                  this.user.numeroUniqueCB = numeroUniqueCB;
                  this.user.dateDelivranceCB = dateDelivranceCB;
                }




                if (response.message != "Conditions non remplies") {
                  alert("Erreur : L'image insérée est un Verso");
                }

                if (response.message === "Conditions non remplies") {
                  alert("Erreur : Elle ne s'agit pas d'un Verso de CIN");
                  return;
                }
                this.getBase64Image(file).then(base64 => {
                  this.user.idCardBack = base64;
                });
                this.user.extractedDataBack = response.donnees; // Stocker les résultats extractés
            }, error => {
                console.error('Erreur lors du traitement OCR Verso:', error);
            });
    }
}

// Nouvelle méthode pour convertir l'image en base64
getBase64Image(file: File): Promise<string | null> {
  const reader = new FileReader();
  reader.readAsDataURL(file);
  return new Promise(resolve => {
    reader.onload = () => resolve(reader.result as string);
  });
}




  async checkCameraAccess(): Promise<boolean> {
    try {
      // Demande l'accès à la caméra
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      // Libère la caméra après la vérification
      stream.getVideoTracks()[0].stop();
      return true; // La caméra est accessible
    } catch (error) {
      console.error('Erreur d\'accès à la caméra :', error);
      return false; // La caméra n'est pas accessible
    }
  }
  

liveness(event: Event) {
    event.preventDefault();
    this.user.successFaceId = null;
    this.user.selfie = null;

    this.checkCameraAccess().then((cameraAccessible) => {
        if (!cameraAccessible) {
            alert('Camèra non valable ou bien non activée');
            return;
        }

        const headers = new HttpHeaders({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        });

        this.http.post('http://localhost:5005/api/liveness', {}, { headers })
            .subscribe({
                next: (response: any) => {
                    console.log('Full response:', response);
                    
                    if (response.status === 'success') {
                        this.user.selfie = 'data:image/jpeg;base64,' + response.selfie;
                        this.user.successFaceId = response.success_face_id;
                        
                        if (response.is_identical) {
                            alert('Vivacité et vérification faciale réussies !');
                            
                            if (this.user.rectoFaceId) {
                                this.verifyFacesAndSubmit();
                            }
                        } else {
                            alert(`Les visages ne correspondent pas (confiance: ${response.confidence})`);
                        }
                    } else {
                        alert('Échec: ' + (response.message || 'Unknown error'));
                    }
                },
                error: (err) => {
                    console.error('API Error:', err);
                    if (err.status === 400) {
                        alert('Échec de la détection: ' + (err.error.message || 'Erreur inconnue'));
                    } else {
                        alert('Erreur technique - voir console pour détails');
                    }
                }
            });
    });
}

  onCountryChange() {
    const selectedCountry = this.user.country;
    this.cities = this.citiesByCountry[selectedCountry] || [];
    this.user.city = '';
  }
  



  convertDateToArabic(dateStr: string): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!dateStr) {
        resolve('');
        return;
      }
  
      const parts = dateStr.split('/');
      if (parts.length !== 3) {
        resolve(dateStr); // Retourne la date originale si le format est incorrect
        return;
      }
  
      const day = parts[0];
      const month = parts[1];
      const year = parts[2];
  
      const monthNames = ['جانفي', 'فيفري','مارس','أفريل','ماي','جوان','جويلية','أوت','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
      
  
      const monthIndex = parseInt(month, 10) - 1;
      if (monthIndex < 0 || monthIndex >= 12) {
        resolve(dateStr); // Retourne la date originale si le mois est invalide
        return;
      }
  
      const arabicDate = `${day} ${monthNames[monthIndex]} ${year}`;
      resolve(arabicDate);
    });
  }
  


  onDateChange() {
    const birthdate = new Date(this.user.dob);
    const today = new Date();
    
    if (birthdate.getFullYear() > today.getFullYear()) {
      this.dateError = "Choix incorrect : l'année choisie ne peut pas être supérieure à l'année actuelle.";
      this.ageError = "";
      return;
    } else {
      this.dateError = "";
    }
  
    const age = today.getFullYear() - birthdate.getFullYear();
    const monthDiff = today.getMonth() - birthdate.getMonth();
  
    if (age < 18 || (age === 18 && monthDiff < 0)) {
      this.ageError = "Vous devez avoir au moins 18 ans.";
    } else {
      this.ageError = "";
    }
  
    // Convertir la date en format arabe et l'envoyer au serveur
    const formattedDate = this.formatDate(this.user.dob);
    this.convertDateToArabic(formattedDate).then(arabicDate => {
      this.user.dobArabic = arabicDate;
      console.log('Date transformée en arabe:', this.user.dobArabic);
      
      // Envoyer la date au serveur
      this.sendTransliteratedDate(arabicDate);
    }).catch(error => {
      console.error('Erreur lors de la conversion de la date:', error);
    });
  }

  sendTransliteratedDate(arabicDate: string) {
    const apiUrl = 'http://localhost:5003/transliterate-names';
    const data = {
      'تاريخ الولادة': arabicDate,
    };
  
    this.http.post(apiUrl, data, { headers: { 'Content-Type': 'application/json' } })
      .subscribe(response => {
        console.log('Date en arabe envoyée avec succès:', response);
      }, error => {
        console.error('Erreur lors de l\'envoi de la date:', error);
      });
  }
  






  onGenderChange(genre: string) {
    this.user.genderArabic = genre; // Mettre à jour le genre dans l'objet user
    console.log('Genre sélectionné:', this.user.genderArabic);
    
    // Envoyer le genre au serveur
    this.sendTransliteratedGender(genre);
}

sendTransliteratedGender(genre: string) {
    const apiUrl = 'http://localhost:5003/transliterate-names';

    // Convertir le genre en arabe
    const genderArabic = (genre === 'homme') ? 'ذكر' : 'أنثى';

    const data = {
        'الجنس': genderArabic // Utiliser le genre en arabe
    };

    this.http.post(apiUrl, data, { headers: { 'Content-Type': 'application/json' } })
        .subscribe(response => {
            console.log('Genre en arabe envoyé avec succès:', response);
        }, error => {
            console.error('Erreur lors de l\'envoi du genre:', error);
        });
}



  checkFocusOutFirstName(event: FocusEvent) {
    const firstname = (event.target as HTMLInputElement).value.trim();
    if (firstname!== '' && firstname!== this.previousFirstname) {
      this.sendTransliteratedName('firstName', firstname);
      this.previousFirstname = firstname;
    }
  }
  
  checkFocusOutLastName(event: FocusEvent) {
    const lastname = (event.target as HTMLInputElement).value.trim();
    if (lastname!== '' && lastname!== this.previousLastname) {
      this.sendTransliteratedName('lastName', lastname);
      this.previousLastname = lastname;
    }
  }

  
  sendTransliteratedName(field: string, value: string) {
    const apiUrl = 'http://localhost:5007/transliterate';
    const data = {
      [field === 'firstName'? 'firstName' : 'lastName']: value
    };
  
    this.http.post(apiUrl, data, { headers: { 'Content-Type': 'application/json' } })
     .subscribe(response => {
        const transliteratedName = field === 'firstName'? (response as any)['الاسم'] : (response as any)['اللقب'];
        console.log(`${field} translittéré : ${transliteratedName}`);
  
        // Envoyer le résultat au serveur Python
        const sendData = {
          [field === 'firstName'? 'الاسم' : 'اللقب']: transliteratedName
        };

        
        this.http.post('http://localhost:5003/transliterate-names', sendData, { headers: { 'Content-Type': 'application/json' } })
         .subscribe(sendResponse => {
            console.log(`${field} envoyé au serveur Python avec succès`);
          }, sendError => {
            console.error(`Erreur lors de l'envoi de ${field} au serveur Python :`, sendError);
          });


      }, error => {
        console.error(`Erreur lors de la translittération de ${field} :`, error);
      });
  }
  

  transliterateFirstName(): void {
    if (this.user.firstName.trim()!== '') {
      const apiUrl = 'http://localhost:5000/transliterate';
      const data = {
        firstName: this.user.firstName
      };
  
      this.http.post(apiUrl, data, { headers: { 'Content-Type': 'application/json' } })
        .subscribe(response => {
          console.log(`Prénom translittéré : ${(response as any)['الاسم']}`);
          // Traitement supplémentaire si nécessaire
        }, error => {
          console.error('Erreur lors de la translittération du prénom :', error);
        });
    }
  }
  
  transliterateLastName(): void {
    if (this.user.lastName.trim()!== '') {
      const apiUrl = 'http://localhost:5000/transliterate';
      const data = {
        lastName: this.user.lastName
      };
  
      this.http.post(apiUrl, data, { headers: { 'Content-Type': 'application/json' } })
        .subscribe(response => {
console.log(`Nom translittéré : ${(response as any)['اللقب']}`);
          // Traitement supplémentaire si nécessaire
        }, error => {
          console.error('Erreur lors de la translittération du nom :', error);
        });
    }
  }

  verifyFacesAndSubmit() {
    // Récupérer les faceId depuis les réponses précédentes
    const faceIdRecto = this.user.rectoFaceId; // FaceId de l'image recto
    const faceIdSuccess = this.user.successFaceId; // FaceId de l'image success

    if (!faceIdRecto || !faceIdSuccess) {
        alert('Les faceId ne sont pas disponibles pour la vérification.');
        return;
    }

    console.log('Face ID de recto :', faceIdRecto);
    console.log('Face ID de success :', faceIdSuccess);

    // Préparer les données pour la vérification des visages
    const data = {
        faceIdRecto: faceIdRecto,
        faceIdSuccess: faceIdSuccess
    };

    // Appeler l'API backend pour la vérification des visages
    this.http.post('http://localhost:5008/api/verify-faces', data).subscribe(
        (response: any) => {
            console.log('Résultat de la vérification des visages :', response);
            if (response.isIdentical) {
                alert('Vérification des visages réussie !');
            } else {
                alert('Les visages ne correspondent pas.');
            }
        },
        (error) => {
            console.error('Erreur lors de la vérification des visages :', error);
            alert('Une erreur est survenue lors de la vérification des visages.');
        }
    );
}
  

formatPhoneNumber(event: any) {
    let value = event.target.value.replace(/\D/g, ''); // Supprime tous les caractères non numériques

    // Limite la longueur à 8 chiffres max
    if (value.length > 8) {
        value = value.substring(0, 8);
    }

    // Formate en XX XXX XXX
    if (value.length > 5) {
        value = value.substring(0, 2) + ' ' + value.substring(2, 5) + ' ' + value.substring(5);
    } else if (value.length > 2) {
        value = value.substring(0, 2) + ' ' + value.substring(2);
    }

    event.target.value = value;
}

onlyNumberKey(event: any) {
    const charCode = (event.which) ? event.which : event.keyCode;
    // Autoriser uniquement les chiffres (0-9)
    if (charCode > 31 && (charCode < 48 || charCode > 57)) {
        event.preventDefault();
        return false;
    }
    return true;
}

async onSubmit() {
  if (this.isSubmitting) return;
  this.isSubmitting = true;

  // 1. Validation des champs obligatoires
  if (!this.validateForm()) {
      alert("Veuillez remplir tous les champs du formulaire.");
      this.isSubmitting = false;
      return;
  }

  // 2. Validation de l'âge
  const birthdate = new Date(this.user.dob);
  const today = new Date();
  if (birthdate.getFullYear() > today.getFullYear()) {
      alert("Choix incorrect : l'année choisie ne peut pas être supérieure à l'année actuelle.");
      this.isSubmitting = false;
      return;
  }
  const age = today.getFullYear() - birthdate.getFullYear();
  const monthDiff = today.getMonth() - birthdate.getMonth();
  if (age < 18 || (age === 18 && monthDiff < 0)) {
      alert("Vous devez avoir au moins 18 ans.");
      this.isSubmitting = false;
      return;
  }

  // 3. Vérification que les faceIds sont disponibles
  if (!this.user.rectoFaceId || !this.user.successFaceId) {
      alert("La vérification faciale n'a pas été effectuée.");
      this.isSubmitting = false;
      return;
  }

  // 4. Comparaison des numéros uniques et des dates
    console.log('DEBUG - Numéro extrait:', this.user.numeroUniqueExtrait);
    console.log('DEBUG - Numéro CB:', this.user.numeroUniqueCB);

    if (!this.user.numeroUniqueExtrait || !this.user.numeroUniqueCB) {
        alert("Les informations du recto ou du verso n'ont pas été correctement extraites.");
        this.isSubmitting = false;
        return;
    }

    if (this.user.numeroUniqueExtrait.toString().trim() !== this.user.numeroUniqueCB.toString().trim()) {
        alert(`Le numéro unique extrait du recto (${this.user.numeroUniqueExtrait}) ne correspond pas au numéro du code-barres (${this.user.numeroUniqueCB}).`);
        this.isSubmitting = false;
        return;
    }

  // 4. Comparaison des numéros uniques et des dates
    console.log('DEBUG - Date de délivrance extraite:', this.user.Datededelivrance);
    console.log('DEBUG - Date de délivrance CB:', this.user.dateDelivranceCB);

if (!this.user.Datededelivrance || !this.user.dateDelivranceCB) {
    alert("Les dates de délivrance n'ont pas été correctement extraites.");
    this.isSubmitting = false;
    return;
}

if (this.user.Datededelivrance.trim() !== this.user.dateDelivranceCB.trim()) {
    alert(`La date de délivrance extraite du recto (${this.user.Datededelivrance}) ne correspond pas à la date du code-barres (${this.user.dateDelivranceCB}).`);
    this.isSubmitting = false;
    return;
}






  try {
      // 5. Vérification faciale
      const verifyResponse = await this.http.post<any>(
          'http://localhost:5008/api/verify-faces',
          {
              faceIdRecto: this.user.rectoFaceId,
              faceIdSuccess: this.user.successFaceId
          }
      ).toPromise();

      if (!verifyResponse.isIdentical) {
          alert("La vérification faciale a échoué. Les visages ne correspondent pas.");
          this.isSubmitting = false;
          return;
      }

      // 6. Vérification OCR
      const comparisonResultResponse = await this.http.get<any>(
          'http://localhost:5003/get-comparison-result'
      ).toPromise();
      
      if (comparisonResultResponse.statut == "ok") {
          alert("Les données insérées se correspondent.");
          this.isSubmitting = true;
      }

      if (comparisonResultResponse.statut !== "ok") {
          alert("Les données insérées ne se correspondent pas.");
          this.isSubmitting = false;
          return;
      }

      // Toutes les validations sont passées - soumission des données
      const userData = {
          firstName: this.user.firstName,
          lastName: this.user.lastName,
          country: this.user.country,
          city: this.user.city,
          dob: this.formatDate(this.user.dob),
          dobArabic: this.user.dobArabic,
          gender: this.user.gender,
          idCardFront: this.user.idCardFront,
          idCardBack: this.user.idCardBack,
          extractedDataFront: this.user.extractedDataFront,
          extractedDataBack: this.user.extractedDataBack,
          selfie: this.user.selfie,
          comparisonStatus: comparisonResultResponse.statut,
          faceVerified: verifyResponse.isIdentical,
          numeroUniqueCB: this.user.numeroUniqueCB,
          dateDelivranceCB: this.user.dateDelivranceCB,
          numeroUniqueExtrait: this.user.numeroUniqueExtrait,
          Datededelivrance: this.user.Datededelivrance
      };

      this.http.post('http://localhost:5000/api/users', userData)
          .subscribe(
              (response) => {
                  console.log('Utilisateur ajouté avec succès!');
                  alert('Création du compte se fait avec succès!');
                  
                  // Réinitialiser le formulaire
                  this.resetForm();
                  
                  // Revenir à l'étape 1
                  this.currentStep = 1;
                  this.updateSteps();
              },
              (error) => {
                  console.error('Erreur lors de l\'ajout:', error);
                  alert('Erreur lors de l\'enregistrement: ' + error.error.message);
              }
          ).add(() => {
              this.isSubmitting = false;
          });

  } catch (error) {
      console.error("Erreur:", error);
      alert("Une erreur est survenue lors de la vérification.");
      this.isSubmitting = false;
  }
}
resetForm() {
    this.user = {
        firstName: '',
        lastName: '',
        email: '', // Réinitialiser email
        phone: '', // Réinitialiser téléphone
        postalCode: '', // Réinitialiser code postal
        address: '', // Réinitialiser adresse
        country: '',
        city: '',
        dob: '',
        dobArabic: '',
        gender: '',
        genderArabic:'',
        idCardFront: '',
        idCardBack: '',
        extractedDataFront: {},
        extractedDataBack: {},
        selfie: null,
        rectoFaceId:null,
        successFaceId:null,
        numeroUniqueCB: '',
        dateDelivranceCB: '',
        numeroUniqueExtrait: '',
        Datededelivrance: '',
    };

    const fileInputs = document.querySelectorAll('input[type="file"]') as NodeListOf<HTMLInputElement>;
    fileInputs.forEach(input => input.value = '');

    const selfiePreview = document.getElementById('selfiePreview') as HTMLImageElement;
    if (selfiePreview) {
        selfiePreview.src = '';
    }
}

 
  /*
  checkFocusOut(event: FocusEvent) {
    const firstname = (event.target as HTMLInputElement).value.trim();
    if (firstname !== '') {
      this.http.post('http://localhost:5000/transliterate', { text: firstname })
        .subscribe({
          next: (data: any) => console.log('Texte en arabe :', data.arabic),
          error: err => console.error('Erreur lors de la translittération:', err)
        });
    }
  }*/
  
  
  formatDate(date: string): string {
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  }
}













