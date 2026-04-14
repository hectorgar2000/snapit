"""
demo.py — SnapIT
Prueba el pipeline completo sin cámara.

Descarga imágenes de prueba de COCO y las pasa por el detector + scorer,
mostrando los resultados en la terminal. Ideal para verificar que
todo funciona antes de abrir el frontend.

Uso:
    python demo.py               → prueba con el objeto del día
    python demo.py --object chair
    python demo.py --object dog --image mi_foto.jpg
    python demo.py --list        → muestra todos los objetos disponibles
"""

import argparse
import sys
import urllib.request
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))


# ── Imágenes de prueba por clase (URLs públicas de COCO/Wikimedia) ────────────
SAMPLE_IMAGES = {
    "chair":        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Above_Gotham.jpg/320px-Above_Gotham.jpg",
    "laptop":       "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Lq_laptop.jpg/320px-Lq_laptop.jpg",
    "cat":          "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/320px-Cat_November_2010-1a.jpg",
    "dog":          "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/YellowLabradorLooking_new.jpg/320px-YellowLabradorLooking_new.jpg",
    "car":          "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/2011_Toyota_Camry_LE.jpg/320px-2011_Toyota_Camry_LE.jpg",
    "bicycle":      "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Left_side_of_Flying_Pigeon.jpg/320px-Left_side_of_Flying_Pigeon.jpg",
    "cell phone":   "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Apple_logo_black.svg/320px-Apple_logo_black.svg.png",
    "bottle":       "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Agua_Mineral.jpg/320px-Agua_Mineral.jpg",
    "cup":          "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/A_small_cup_of_coffee.JPG/320px-A_small_cup_of_coffee.JPG",
    "book":         "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/02_AlteKircheBetten_Fronansicht.jpg/240px-02_AlteKircheBetten_Fronansicht.jpg",
}

DEFAULT_TEST_URL = "https://ultralytics.com/images/bus.jpg"  # imagen de demo de ultralytics


def download_image(url: str, dest: Path) -> bool:
    """Descarga una imagen a disco. Devuelve True si éxito."""
    try:
        print(f"  ⬇  Descargando imagen de prueba…")
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            dest.write_bytes(response.read())
        return True
    except Exception as e:
        print(f"  ⚠️  No se pudo descargar: {e}")
        return False


def run_demo(target_class: str, image_path: str = None, seconds: int = 120, attempt: int = 1):
    """Ejecuta el pipeline completo y muestra los resultados."""

    from core.challenge import get_daily_challenge
    from core.catalog import get_by_coco_name
    from core.detector import get_detector
    from core.scorer import calculate_score, DetectionInput

    # Objeto objetivo
    obj = get_by_coco_name(target_class)
    if not obj:
        print(f"\n❌ Objeto '{target_class}' no está en el catálogo.")
        print("   Usa --list para ver los disponibles.")
        return

    print("\n" + "═"*52)
    print(f"  🎯  SnapIT DEMO")
    print("═"*52)
    print(f"  Objeto objetivo: {obj.emoji} {obj.display_name}")
    print(f"  Dificultad:      {obj.difficulty.upper()}")
    print(f"  Tiempo simulado: {seconds}s desde notificación")
    print(f"  Intento:         {attempt}/3")
    print("═"*52)

    # Imagen: usar la proporcionada, descargar, o buscar en cache
    tmp_dir = Path(__file__).parent / ".demo_cache"
    tmp_dir.mkdir(exist_ok=True)

    if image_path:
        img_path = Path(image_path)
        if not img_path.exists():
            print(f"\n❌ No existe el archivo: {img_path}")
            return
        print(f"\n  📸 Usando imagen: {img_path.name}")
    else:
        cache_file = tmp_dir / f"{target_class.replace(' ', '_')}.jpg"
        if cache_file.exists():
            print(f"\n  📸 Usando imagen en caché: {cache_file.name}")
            img_path = cache_file
        else:
            url = SAMPLE_IMAGES.get(target_class, DEFAULT_TEST_URL)
            if download_image(url, cache_file):
                img_path = cache_file
            else:
                # Fallback: imagen de ultralytics
                fallback = tmp_dir / "fallback.jpg"
                if download_image(DEFAULT_TEST_URL, fallback):
                    img_path = fallback
                else:
                    print("\n❌ Sin conexión para descargar imagen de prueba.")
                    print("   Usa: python demo.py --image tu_foto.jpg")
                    return

    # Detección YOLO
    print("\n  🔍 Ejecutando YOLOv8n…")
    try:
        detector = get_detector()
        result   = detector.analyze(str(img_path), target_class)
    except RuntimeError as e:
        print(f"\n  ❌ {e}")
        return

    # Mostrar todas las detecciones
    print(f"\n  📦 Detecciones encontradas ({len(result.all_detections)}):")
    if not result.all_detections:
        print("     (ninguna)")
    for d in sorted(result.all_detections, key=lambda x: -x.confidence)[:8]:
        marker = " ← TARGET ✅" if d.class_name == target_class else ""
        bar = "█" * int(d.confidence * 20)
        print(f"     {d.class_name:<22} {d.confidence:.0%}  {bar}{marker}")

    # Score
    if result.target_detection:
        td = result.target_detection
        other_count = len([x for x in result.all_detections if x.class_name != target_class])
        score_input = DetectionInput(
            target_object=obj,
            detected_class=td.class_name,
            confidence=td.confidence,
            bbox_area_ratio=td.bbox_area_ratio,
            other_detections=other_count,
            seconds_since_notification=seconds,
            attempt_number=attempt,
        )
    else:
        # No detectado
        best = result.all_detections[0] if result.all_detections else None
        score_input = DetectionInput(
            target_object=obj,
            detected_class=best.class_name if best else "nothing",
            confidence=best.confidence if best else 0.0,
            bbox_area_ratio=0.0,
            other_detections=len(result.all_detections),
            seconds_since_notification=seconds,
            attempt_number=attempt,
        )

    from core.scorer import calculate_score
    score = calculate_score(score_input)

    # Mostrar resultado
    print(f"\n{'═'*52}")
    if score.correct:
        print(f"  ✅  DETECTADO  —  {obj.display_name}")
    else:
        print(f"  ❌  NO DETECTADO  —  se vio: {score_input.detected_class}")
    print(f"{'═'*52}")
    print(f"  Confianza:       {score.confidence_pct}%")
    print(f"  Score base:      {score.base_score:>6}")
    print(f"  + Velocidad:     {score.speed_bonus:>6}   {score.speed_label}")
    print(f"  + Encuadre:      {score.framing_bonus:>6}   {score.framing_label}")
    print(f"  - Clutter:       {score.clutter_penalty:>6}")
    print(f"  - Intento:       {score.attempt_penalty:>6}")
    print(f"  {'─'*30}")
    print(f"  TOTAL:         {'':>2}{score.total_score:>6} pts")
    print(f"{'═'*52}\n")

    # Guardar imagen anotada
    if result.annotated_image:
        out = tmp_dir / f"result_{target_class.replace(' ', '_')}.jpg"
        out.write_bytes(result.annotated_image)
        print(f"  💾 Imagen anotada guardada en: {out}")
        print(f"     (abre el archivo para ver los bounding boxes)\n")


def list_objects():
    from core.catalog import CATALOG
    print("\n📦 Objetos disponibles en SnapIT:\n")
    for diff in ['easy', 'medium', 'hard']:
        emoji_map = {'easy': '⭐', 'medium': '⭐⭐', 'hard': '⭐⭐⭐'}
        items = [o for o in CATALOG if o.difficulty == diff]
        print(f"  {emoji_map[diff]} {diff.upper()} ({len(items)}):")
        for obj in items:
            print(f"     {obj.emoji} {obj.display_name:<22}  coco: '{obj.coco_name}'")
        print()


def main():
    parser = argparse.ArgumentParser(description="SnapIT — demo sin cámara")
    parser.add_argument("--object",  type=str, default=None,  help="Objeto COCO a detectar (ej: chair)")
    parser.add_argument("--image",   type=str, default=None,  help="Ruta a una imagen local")
    parser.add_argument("--seconds", type=int, default=120,   help="Segundos simulados desde la notificación")
    parser.add_argument("--attempt", type=int, default=1,     choices=[1,2,3], help="Número de intento")
    parser.add_argument("--list",    action="store_true",      help="Listar todos los objetos del catálogo")
    args = parser.parse_args()

    if args.list:
        list_objects()
        return

    # Si no se especifica objeto, usar el del día
    if args.object is None:
        from core.challenge import get_daily_challenge
        challenge = get_daily_challenge()
        print(f"\n  (Usando el objeto de hoy: {challenge.emoji} {challenge.display_name})")
        target = challenge.coco_name
    else:
        target = args.object.lower()

    run_demo(
        target_class=target,
        image_path=args.image,
        seconds=args.seconds,
        attempt=args.attempt,
    )


if __name__ == "__main__":
    main()
