import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';

import en from './en';
import es from './es';

// Idiomas disponibles en la app
const SUPPORTED = ['en', 'es'] as const;
type SupportedLang = typeof SUPPORTED[number];

// Detectar idioma del dispositivo, usar inglés si no está soportado
const deviceLang = Localization.getLocales()[0]?.languageCode ?? 'en';
const lng: SupportedLang = (SUPPORTED as readonly string[]).includes(deviceLang)
  ? (deviceLang as SupportedLang)
  : 'en';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      es: { translation: es },
    },
    lng,
    fallbackLng:  'en',
    interpolation: { escapeValue: false },
    // Necesario para React Native (no hay DOM)
    compatibilityJSON: 'v4',
  });

export default i18n;

// ── Para añadir un idioma nuevo ───────────────────────────────────────────────
// 1. Crea mobile/src/i18n/fr.ts (o el idioma que sea) siguiendo la misma
//    estructura que en.ts / es.ts
// 2. Importa el archivo aquí: import fr from './fr';
// 3. Añádelo a resources: fr: { translation: fr }
// 4. Añade 'fr' al array SUPPORTED
// ─────────────────────────────────────────────────────────────────────────────
