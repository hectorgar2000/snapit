import Constants from 'expo-constants';

// La URL de la API se lee desde app.json → extra.apiUrl
// Esto evita hardcodear la URL y permite cambiarla sin tocar código.
//
// Para cambiar el entorno, edita app.json:
//   "extra": { "apiUrl": "https://tu-app.railway.app" }
//
// Para desarrollo local con dispositivo físico, pon tu IP:
//   "extra": { "apiUrl": "http://192.168.X.X:8000" }

export const API_URL: string =
  Constants.expoConfig?.extra?.apiUrl ?? 'http://10.0.2.2:8000';
