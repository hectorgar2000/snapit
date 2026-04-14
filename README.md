# 📸 SnapIT

> El juego diario de detección de objetos con IA. Estilo Wordle, pero con tu cámara.

Cada día hay un objeto diferente. Lo fotografías, YOLO-World lo detecta y te da una puntuación según la confianza de la IA, la velocidad, el encuadre y el clutter. Compite con amigos en el feed diario.

---

## Demo

![SnapIT](https://img.shields.io/badge/estado-en%20desarrollo-yellow)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green)
![YOLO](https://img.shields.io/badge/YOLO--World-yolov8s--worldv2-purple)
![Expo](https://img.shields.io/badge/Expo-SDK%2054-black)

---

## Características

- **Reto diario determinista** — mismo objeto para todos, generado por hash de la fecha
- **Detección con YOLO-World** — modelo entrenado en Objects365 (365 clases), entiende lenguaje natural vía CLIP
- **Scoring completo** — velocidad, encuadre, clutter, intentos, dificultad
- **Auth completa** — registro, login, JWT, modo invitado
- **Sistema de amigos** — solicitar, aceptar, buscar (solo cuentas registradas)
- **Feed social** — ve las fotos de hoy de toda la comunidad o solo amigos
- **Likes y comentarios** en el feed
- **Perfil** con historial, rachas y estadísticas
- **Ranking global**
- **Notificaciones push** a una hora sorpresa cada día (hash criptográfico del día)
- **PWA instalable** — funciona como app en Android/iOS desde el navegador
- **App móvil nativa** — React Native/Expo para Android e iOS

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI + SQLModel + SQLite / PostgreSQL |
| Frontend web | SPA Vanilla JS servida desde FastAPI |
| App móvil | React Native + Expo SDK 54 |
| ML | YOLO-World `yolov8s-worldv2.pt` (Ultralytics) |
| Auth | PyJWT + bcrypt directo (compatible con Python 3.13) |
| Deploy | Docker + Railway |

---

## Estructura del proyecto

```
snapit/
├── api/
│   ├── main.py        # Todos los endpoints FastAPI
│   ├── database.py    # Modelos SQLModel + migraciones
│   ├── models.py      # Schemas Pydantic
│   └── auth.py        # JWT + bcrypt
├── core/
│   ├── detector.py    # YOLO-World wrapper (singleton)
│   ├── catalog.py     # 91 objetos con nombre, emoji y dificultad
│   ├── challenge.py   # Reto diario determinista por hash de fecha
│   └── scorer.py      # Fórmula de puntuación
├── frontend/
│   ├── index.html     # SPA completa
│   ├── manifest.json  # PWA manifest
│   └── sw.js          # Service worker (offline-first)
├── mobile/            # App React Native / Expo
│   ├── App.tsx        # Navegación principal (bottom tabs)
│   ├── app.json       # Config Expo + permisos
│   ├── eas.json       # Perfiles de build (APK / AAB)
│   └── src/
│       ├── screens/   # AuthScreen, PlayScreen, FeedScreen, FriendsScreen, LeaderboardScreen
│       ├── api.ts     # Cliente HTTP (todas las llamadas al backend)
│       ├── auth.ts    # AsyncStorage: sesión y estado local
│       ├── config.ts  # URL de la API
│       ├── theme.ts   # Colores y estilos comunes
│       └── types.ts   # Interfaces TypeScript
├── Dockerfile
├── railway.toml
└── run.py             # Lanzador local
```

---

## Arrancar en local

### Backend + Web

```bash
# 1. Clonar e instalar dependencias
git clone https://github.com/hectorgar2000/snapit.git
cd snapit
pip install -r requirements.txt

# 2. Arrancar
python run.py
# → Abre http://localhost:8000/app
```

El modelo YOLO-World (~50 MB) se descarga automáticamente en el primer arranque.

### App móvil

```bash
cd mobile
npm install
npx expo start
```

Escanea el QR con **Expo Go** (iOS o Android). Asegúrate de que `src/config.ts` apunta a tu servidor:

```typescript
// Dispositivo físico (misma red WiFi)
export const API_URL = 'http://192.168.X.X:8000';

// Producción
export const API_URL = 'https://tu-app.railway.app';
```

---

## Build de la app móvil

Requiere cuenta gratuita en [expo.dev](https://expo.dev) y la CLI de EAS:

```bash
npm install -g eas-cli
eas login
```

| Perfil | Formato | Uso |
|---|---|---|
| `preview` | `.apk` | Instalar directamente en Android |
| `production` | `.aab` | Subir a Google Play Store |

```bash
# APK para instalar directamente
eas build --platform android --profile preview

# AAB para Google Play
eas build --platform android --profile production
```

---

## Variables de entorno

Copia `.env.example` a `.env` para desarrollo local:

| Variable | Descripción | Default |
|---|---|---|
| `SNAPIT_SECRET` | Clave secreta para JWT. **Cámbiala en producción.** | `snapit-dev-secret-...` |
| `DATABASE_URL` | URL de base de datos. SQLite local por defecto, PostgreSQL en producción. | `sqlite:///snapit.db` |
| `PORT` | Puerto del servidor. Railway lo inyecta automáticamente. | `8000` |

Genera una clave segura para producción:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Deploy en Railway

1. Sube el repo a GitHub
2. En [railway.app](https://railway.app) → `New Project` → `Deploy from GitHub repo`
3. Railway detecta el `Dockerfile` automáticamente
4. Añade un addon **PostgreSQL**: `New` → `Database` → `PostgreSQL`  
   Railway inyecta `DATABASE_URL` solo al enlazarlo con el servicio
5. En `Variables` del servicio, añade `SNAPIT_SECRET` con una clave segura
6. En `Settings` → `Networking` → `Generate Domain`

---

## API

Documentación interactiva disponible en `/docs` cuando el servidor está corriendo.

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/register` | Registro con email y contraseña |
| `POST` | `/login` | Login, devuelve JWT |
| `GET` | `/me` | Datos del usuario autenticado |
| `POST` | `/guest` | Crea usuario invitado |
| `GET` | `/today` | Reto del día |
| `GET` | `/week` | Vista semanal |
| `POST` | `/submit` | Envía foto y recibe puntuación |
| `GET` | `/feed` | Feed del día (`?friends_only=true`) |
| `GET` | `/leaderboard` | Ranking global |
| `GET/POST/DELETE` | `/friends/...` | Gestión de amigos |
| `GET` | `/user/{u}/history` | Historial de un usuario |
| `POST/DELETE` | `/submission/{id}/like` | Likes |
| `GET/POST` | `/submission/{id}/comments` | Comentarios |

---

## Fórmula de puntuación

```
score = (base × dificultad) + velocidad + encuadre − clutter − penalización_intento
```

| Factor | Descripción |
|---|---|
| Base | Según dificultad del objeto (1000 / 1500 / 2000 pts) |
| Velocidad | Hasta +500 pts si respondes en < 30 s |
| Encuadre | Hasta +300 pts si el objeto ocupa > 40% del frame |
| Clutter | −50 pts por cada objeto extra detectado |
| Intento | −20% por intento 2, −40% por intento 3 |

---

## Licencia

MIT
