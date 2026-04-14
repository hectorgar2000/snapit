# SnapIT — Cómo arrancar

## 1. Instalar dependencias

```bash
cd snapit
pip install -r requirements.txt
```

## 2. Arrancar la API

```bash
uvicorn api.main:app --reload --port 8000
```

La API queda en: http://localhost:8000  
Docs interactivos: http://localhost:8000/docs

## 3. Abrir el frontend

Abre el archivo `frontend/index.html` directamente en el navegador.  
(Chrome/Edge recomendado para acceso a la cámara)

## 4. Ejecutar los tests

```bash
# Tests del core engine
python tests/test_core.py

# Tests de la API
python tests/test_api.py
```

---

## Estructura del proyecto

```
snapit/
├── core/
│   ├── catalog.py      ← 45 objetos jugables (COCO)
│   ├── scorer.py       ← fórmula de puntuación
│   ├── challenge.py    ← reto diario determinista
│   └── detector.py     ← YOLOv8n wrapper
├── api/
│   ├── main.py         ← FastAPI (6 endpoints)
│   ├── database.py     ← SQLite + SQLModel
│   └── models.py       ← schemas Pydantic
├── frontend/
│   └── index.html      ← app web completa
├── tests/
│   ├── test_core.py    ← 15 tests
│   └── test_api.py     ← 11 tests
└── requirements.txt
```

## Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/today` | Reto del día |
| GET | `/week` | Calendario semanal |
| POST | `/submit` | Enviar foto → recibir score |
| GET | `/leaderboard` | Ranking global |
| GET | `/feed` | Feed del día |
| GET | `/user/{username}` | Stats de un usuario |

## Sistema de puntuación

```
Score = (base_points × confianza × dificultad)
      + bonus_velocidad   (+500/300/100/0)
      + bonus_encuadre    (+300/150/0/-100)
      - penalización_clutter (50 por objeto extra, máx 300)
      - penalización_intento (0 / -200 / -400)
```
