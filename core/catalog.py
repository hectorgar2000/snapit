"""
catalog.py — SnapIT
Catálogo de objetos jugables con YOLO-World / Objects365 (365 clases).

El campo `coco_name` contiene el texto que se pasa a YOLO-World.
Gracias a CLIP, acepta tanto nombres de clases exactos como descripciones
en lenguaje natural (ej. "wooden chair", "coffee mug").
"""

import os
from dataclasses import dataclass
from typing import Optional

# Clases detectables por YOLOv8 estándar (COCO-80)
COCO_CLASSES: set[str] = {
    "chair", "couch", "laptop", "cell phone", "book", "bottle", "cup",
    "keyboard", "mouse", "tv", "clock", "vase", "backpack", "umbrella",
    "bicycle", "car", "potted plant", "bed", "dining table", "refrigerator",
    "microwave", "oven", "sink", "toilet", "suitcase", "handbag", "knife",
    "toaster", "scissors", "toothbrush", "hair drier", "remote", "wine glass",
    "motorcycle", "bird", "cat", "dog", "sports ball", "tennis racket",
    "kite", "fire hydrant", "stop sign", "parking meter", "bench",
    "skateboard", "tie", "spoon", "fork", "bowl",
}


@dataclass
class SnapObject:
    coco_name:    str       # Texto para YOLO-World (nombre Objects365 o descripción)
    display_name: str       # Nombre mostrado al usuario (en español)
    emoji:        str
    difficulty:   str       # "easy" | "medium" | "hard"
    base_points:  int
    hint:         Optional[str] = None


# ─── Catálogo — objetos fotografiables en entornos cotidianos ─────────────────
CATALOG: list[SnapObject] = [

    # ══════════════ EASY ══════════════════════════════════════════════════════
    # Domésticos / oficina — muy comunes y fáciles de encontrar

    SnapObject("chair",          "Silla",           "🪑", "easy", 1000, "Algo en lo que sentarse"),
    SnapObject("couch",          "Sofá",            "🛋️", "easy", 1000, "Para relajarse en el salón"),
    SnapObject("laptop",         "Portátil",        "💻", "easy", 1000, "Tu compañero de trabajo"),
    SnapObject("cell phone",     "Móvil",           "📱", "easy", 1000, "Siempre a mano"),
    SnapObject("book",           "Libro",           "📚", "easy", 1000, "Para leer"),
    SnapObject("bottle",         "Botella",         "🍶", "easy", 1000, "Contiene líquido"),
    SnapObject("cup",            "Taza",            "☕", "easy", 1000, "Para tu café o té"),
    SnapObject("keyboard",       "Teclado",         "⌨️", "easy", 1000, "Para escribir en el ordenador"),
    SnapObject("mouse",          "Ratón",           "🖱️", "easy", 1000, "Periférico del ordenador"),
    SnapObject("tv",             "Televisión",      "📺", "easy", 1000, "La pantalla grande del salón"),
    SnapObject("clock",          "Reloj",           "🕐", "easy", 1000, "Te dice la hora"),
    SnapObject("vase",           "Jarrón",          "🏺", "easy", 1000, "Decoración con flores"),
    SnapObject("backpack",       "Mochila",         "🎒", "easy", 1000, "Para llevar cosas"),
    SnapObject("umbrella",       "Paraguas",        "☂️", "easy", 1000, "Para la lluvia"),
    SnapObject("pillow",         "Almohada",        "🛏️", "easy", 1000, "Para dormir cómodo"),
    SnapObject("lamp",           "Lámpara",         "💡", "easy", 1000, "Ilumina la habitación"),
    SnapObject("mirror",         "Espejo",          "🪞", "easy", 1000, "Refleja tu imagen"),
    SnapObject("pen",            "Bolígrafo",       "🖊️", "easy", 1000, "Para escribir a mano"),
    SnapObject("pencil",         "Lápiz",           "✏️", "easy", 1000, "Se puede borrar"),
    SnapObject("bowl",           "Bol",             "🥣", "easy", 1000, "Para cereales o sopa"),
    SnapObject("fork",           "Tenedor",         "🍴", "easy", 1000, "Cubierto para comer"),
    SnapObject("spoon",          "Cuchara",         "🥄", "easy", 1000, "Para la sopa"),
    SnapObject("glasses",        "Gafas",           "👓", "easy", 1000, "Para ver mejor"),
    SnapObject("hat",            "Sombrero",        "🎩", "easy", 1000, "Va en la cabeza"),
    SnapObject("shoe",           "Zapato",          "👟", "easy", 1000, "Para los pies"),
    SnapObject("trash bin",      "Papelera",        "🗑️", "easy", 1000, "Para tirar basura"),
    SnapObject("flower",         "Flor",            "🌸", "easy", 1000, "Colorida y con pétalos"),
    SnapObject("plant",          "Planta",          "🪴", "easy", 1000, "Verde y viva"),

    # ══════════════ MEDIUM ════════════════════════════════════════════════════
    # Algo más específicos — en casa pero no siempre a la vista

    SnapObject("bicycle",        "Bicicleta",       "🚲", "medium", 1500, "Transporte de dos ruedas"),
    SnapObject("car",            "Coche",           "🚗", "medium", 1500, "Transporte de cuatro ruedas"),
    SnapObject("potted plant",   "Planta en maceta","🌿", "medium", 1500, "Naturaleza en casa"),
    SnapObject("bed",            "Cama",            "🛏️", "medium", 1500, "Donde duermes"),
    SnapObject("dining table",   "Mesa de comedor", "🪵", "medium", 1500, "Superficie grande con patas"),
    SnapObject("refrigerator",   "Nevera",          "🧊", "medium", 1500, "Mantiene la comida fría"),
    SnapObject("microwave",      "Microondas",      "📦", "medium", 1500, "Calienta la comida rápido"),
    SnapObject("oven",           "Horno",           "🔥", "medium", 1500, "Para cocinar"),
    SnapObject("sink",           "Fregadero",       "🚿", "medium", 1500, "Para lavar los platos"),
    SnapObject("toilet",         "Inodoro",         "🚽", "medium", 1500, "En el baño"),
    SnapObject("suitcase",       "Maleta",          "🧳", "medium", 1500, "Para viajar"),
    SnapObject("handbag",        "Bolso",           "👜", "medium", 1500, "Accesorio de mano"),
    SnapObject("knife",          "Cuchillo",        "🔪", "medium", 1500, "Para cortar en la cocina"),
    SnapObject("pan",            "Sartén",          "🍳", "medium", 1500, "Para freír"),
    SnapObject("toaster",        "Tostadora",       "🍞", "medium", 1500, "Para tostar el pan"),
    SnapObject("kettle",         "Hervidor",        "🫖", "medium", 1500, "Para calentar agua"),
    SnapObject("coffee machine", "Cafetera",        "☕", "medium", 1500, "Hace el café por la mañana"),
    SnapObject("headphones",     "Auriculares",     "🎧", "medium", 1500, "Para escuchar música"),
    SnapObject("speaker",        "Altavoz",         "🔊", "medium", 1500, "Reproduce sonido"),
    SnapObject("camera",         "Cámara",          "📷", "medium", 1500, "Para hacer fotos"),
    SnapObject("painting",       "Cuadro",          "🖼️", "medium", 1500, "Decoración en la pared"),
    SnapObject("curtain",        "Cortina",         "🪟", "medium", 1500, "Cubre la ventana"),
    SnapObject("bench",          "Banco",           "🪑", "medium", 1500, "Asiento largo exterior"),
    SnapObject("skateboard",     "Monopatín",       "🛹", "medium", 1500, "Tabla con ruedas"),
    SnapObject("tie",            "Corbata",         "👔", "medium", 1500, "Accesorio formal"),
    SnapObject("watch",          "Reloj de pulsera","⌚", "medium", 1500, "Lo llevas en la muñeca"),
    SnapObject("candle",         "Vela",            "🕯️", "medium", 1500, "Llama pequeña decorativa"),
    SnapObject("basket",         "Cesta",           "🧺", "medium", 1500, "Para llevar cosas"),
    SnapObject("blanket",        "Manta",           "🧣", "medium", 1500, "Para abrigarse en el sofá"),
    SnapObject("pot",            "Olla",            "🫕", "medium", 1500, "Para cocinar"),
    SnapObject("soap",           "Jabón",           "🧼", "medium", 1500, "Para lavarse las manos"),
    SnapObject("comb",           "Peine",           "💈", "medium", 1500, "Para el cabello"),
    SnapObject("iron",           "Plancha",         "👕", "medium", 1500, "Para las arrugas de la ropa"),
    SnapObject("fan",            "Ventilador",      "🌀", "medium", 1500, "Mueve el aire"),

    # ══════════════ HARD ══════════════════════════════════════════════════════
    # Menos comunes, difíciles de fotografiar o requieren salir a buscarlos

    SnapObject("fire hydrant",   "Boca de incendios","🚒", "hard", 2000, "Roja, en la calle"),
    SnapObject("stop sign",      "Señal de stop",    "🛑", "hard", 2000, "Octagonal y roja"),
    SnapObject("parking meter",  "Parquímetro",      "⏱️", "hard", 2000, "Para pagar el aparcamiento"),
    SnapObject("kite",           "Cometa",           "🪁", "hard", 2000, "Vuela con el viento"),
    SnapObject("bird",           "Pájaro",           "🐦", "hard", 2000, "Pequeño y que vuela"),
    SnapObject("cat",            "Gato",             "🐱", "hard", 2000, "Felino doméstico"),
    SnapObject("dog",            "Perro",            "🐶", "hard", 2000, "Can doméstico"),
    SnapObject("sports ball",    "Pelota",           "⚽", "hard", 2000, "Esférica, para jugar"),
    SnapObject("tennis racket",  "Raqueta de tenis", "🎾", "hard", 2000, "Para jugar al tenis"),
    SnapObject("scissors",       "Tijeras",          "✂️", "hard", 2000, "Para cortar"),
    SnapObject("toothbrush",     "Cepillo de dientes","🪥","hard", 2000, "Higiene dental"),
    SnapObject("hair drier",     "Secador de pelo",  "💨", "hard", 2000, "Para secar el cabello"),
    SnapObject("remote",         "Mando a distancia","📡", "hard", 2000, "Controla la tele"),
    SnapObject("wine glass",     "Copa de vino",     "🍷", "hard", 2000, "Cristal fino y elegante"),
    SnapObject("motorcycle",     "Moto",             "🏍️", "hard", 2000, "Más rápida que una bici"),
    SnapObject("fire extinguisher","Extintor",       "🧯", "hard", 2000, "Rojo, en paredes o pasillos"),
    SnapObject("umbrella",       "Paraguas abierto", "☂️", "hard", 2000, "Desplegado contra la lluvia"),
    SnapObject("skateboard",     "Monopatín en uso", "🛹", "hard", 2000, "Tabla sobre ruedas"),
    SnapObject("bicycle helmet", "Casco de ciclista","🪖", "hard", 2000, "Protección para la cabeza"),
    SnapObject("padlock",        "Candado",          "🔒", "hard", 2000, "Seguridad de una puerta"),
    SnapObject("screwdriver",    "Destornillador",   "🔧", "hard", 2000, "Herramienta de taller"),
    SnapObject("hammer",         "Martillo",         "🔨", "hard", 2000, "Para clavar clavos"),
    SnapObject("tape measure",   "Cinta métrica",    "📏", "hard", 2000, "Para medir distancias"),
    SnapObject("sunglasses",     "Gafas de sol",     "🕶️", "hard", 2000, "Para el sol fuerte"),
    SnapObject("trophy",         "Trofeo",           "🏆", "hard", 2000, "Premio por ganar"),
    SnapObject("guitar",         "Guitarra",         "🎸", "hard", 2000, "Instrumento de cuerda"),
    SnapObject("violin",         "Violín",           "🎻", "hard", 2000, "Instrumento de arco"),
    SnapObject("piano",          "Piano",            "🎹", "hard", 2000, "Instrumento de teclas"),
    SnapObject("dart",           "Dardo",            "🎯", "hard", 2000, "Se lanza a una diana"),
    SnapObject("ladder",         "Escalera de mano", "🪜", "hard", 2000, "Para subir a lugares altos"),
]

# Índice rápido por coco_name (texto para YOLO-World)
CATALOG_INDEX: dict[str, SnapObject] = {obj.coco_name: obj for obj in CATALOG}

_USE_YOLO_WORLD = os.getenv("YOLO_MODE", "coco").lower() == "world"


def get_active_catalog() -> list[SnapObject]:
    """Devuelve el catálogo filtrado según el modo de detección activo."""
    if _USE_YOLO_WORLD:
        return CATALOG
    # Modo COCO: solo objetos detectables por YOLOv8 estándar
    seen: set[str] = set()
    result = []
    for obj in CATALOG:
        if obj.coco_name in COCO_CLASSES and obj.coco_name not in seen:
            seen.add(obj.coco_name)
            result.append(obj)
    return result


def get_by_coco_name(name: str) -> Optional[SnapObject]:
    """Busca un objeto por su clase/texto YOLO-World."""
    return CATALOG_INDEX.get(name)


def get_by_difficulty(difficulty: str) -> list[SnapObject]:
    """Filtra objetos por dificultad (catálogo completo)."""
    return [obj for obj in CATALOG if obj.difficulty == difficulty]


def get_by_difficulty_active(difficulty: str) -> list[SnapObject]:
    """Filtra objetos por dificultad del catálogo activo según YOLO_MODE."""
    return [obj for obj in get_active_catalog() if obj.difficulty == difficulty]


def all_coco_names() -> list[str]:
    """Devuelve todos los textos YOLO-World del catálogo activo."""
    return [obj.coco_name for obj in get_active_catalog()]


if __name__ == "__main__":
    print(f"📦 Catálogo SnapIT: {len(CATALOG)} objetos")
    for diff in ["easy", "medium", "hard"]:
        items = get_by_difficulty(diff)
        print(f"  {diff.upper()}: {len(items)} objetos — "
              + ", ".join(o.display_name for o in items[:5]) + ("…" if len(items) > 5 else ""))
