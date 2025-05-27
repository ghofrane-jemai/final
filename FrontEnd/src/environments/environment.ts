export const environment = { 
  production: false,
  apiUrls: {
    transliteration: 'http://192.168.49.2:31057/transliterate',
    transliterationNames: 'http://192.168.49.2:31053/transliterate-names',
    getcomparisonresult: 'http://192.168.49.2:31053/get-comparison-result',
    ocrextraction: 'http://192.168.49.2:31053/ocr-extraction',
    recto: 'http://192.168.49.2:31051/ocr/recto',
    verso: 'http://192.168.49.2:31052/ocr/verso',
    ocrversoupdate: 'http://192.168.49.2:31052/ocr/verso/update',
    comparaison: 'http://192.168.49.2:31053/comparaison',
    verification: 'http://192.168.49.2:31058/api/verify-faces',
    vivacite: 'http://192.168.49.2:31055/api/liveness',
    global: 'http://192.168.49.2:31050/api/users',
  }
};
