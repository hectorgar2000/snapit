"""
detector.py — SnapIT
Wrapper sobre YOLO-World (yolov8s-worldv2.pt) para detección de objetos.
Entrenado en Objects365 (365 clases) + CLIP text matching → acepta cualquier descripción.

Recibe una imagen (path o bytes) y devuelve:
  - La mejor detección del objeto objetivo (si existe)
  - Todas las detecciones para calcular clutter
  - Imagen anotada con bounding boxes
"""

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from PIL import Image


@dataclass
class Detection:
    """Una detección individual de YOLO."""
    class_name: str
    confidence: float       # 0.0 – 1.0
    bbox: tuple             # (x1, y1, x2, y2) en píxeles
    bbox_area_ratio: float  # Área del bbox / área total del frame


@dataclass
class DetectionResult:
    """Resultado completo del análisis de una imagen."""
    image_width: int
    image_height: int
    all_detections: list[Detection]        # Todas las detecciones
    target_detection: Optional[Detection]  # La mejor detección del objetivo
    annotated_image: Optional[bytes]       # JPEG con bboxes dibujados


class SnapDetector:
    """
    Detector principal de SnapIT usando YOLO-World.
    Carga el modelo una sola vez y reutiliza para todas las inferencias.

    YOLO-World usa CLIP para matching de texto → no está limitado a clases fijas.
    Se especifican las clases justo antes de cada inferencia con set_classes().
    """

    MODEL_NAME = "yolov8s-worldv2.pt"   # Entrenado en Objects365 + GoldG
    CONFIDENCE_THRESHOLD = 0.25

    # Objetos comunes para detectar clutter adicional al objetivo
    _CLUTTER_CLASSES = [
        "person", "chair", "table", "laptop", "phone", "bottle",
        "cup", "book", "bag", "car", "sofa", "bed", "tv", "backpack",
    ]

    def __init__(self):
        self._model = None
        self._current_classes: list[str] = []

    def _load_model(self):
        """Carga el modelo en memoria (lazy loading)."""
        if self._model is None:
            try:
                from ultralytics import YOLOWorld
                print(f"🔄 Cargando {self.MODEL_NAME} (YOLO-World / Objects365)...")
                self._model = YOLOWorld(self.MODEL_NAME)
                print("✅ YOLO-World cargado")
            except ImportError:
                raise RuntimeError(
                    "ultralytics no está instalado. "
                    "Ejecuta: pip install ultralytics"
                )

    def _set_classes(self, target_class: str):
        """
        Configura las clases a detectar para esta inferencia.
        El objetivo siempre va primero (índice 0) seguido de objetos de clutter.
        """
        classes = [target_class] + [c for c in self._CLUTTER_CLASSES if c != target_class]
        if classes != self._current_classes:
            self._model.set_classes(classes)
            self._current_classes = classes

    def analyze(
        self,
        image_input: Union[str, Path, bytes],
        target_class: str,
        conf_threshold: float = CONFIDENCE_THRESHOLD,
    ) -> DetectionResult:
        """
        Analiza una imagen y busca el objeto objetivo.

        Args:
            image_input:    Path al archivo de imagen, o bytes de la imagen.
            target_class:   Descripción del objeto (ej. "cup", "wooden chair").
                            YOLO-World acepta lenguaje natural gracias a CLIP.
            conf_threshold: Confianza mínima para considerar una detección.

        Returns:
            DetectionResult con todas las detecciones y la mejor del objetivo.
        """
        self._load_model()
        self._set_classes(target_class)

        # Cargar imagen con PIL
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        else:
            raise ValueError("image_input debe ser path (str/Path) o bytes")

        img_w, img_h = img.size
        img_area = img_w * img_h

        # Inferencia YOLO-World
        results = self._model(img, conf=conf_threshold, verbose=False)

        all_detections: list[Detection] = []
        target_detection: Optional[Detection] = None
        best_conf = 0.0

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                cls_id   = int(box.cls[0])
                cls_name = self._model.names[cls_id]
                conf     = float(box.conf[0])
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]

                bbox_area  = (x2 - x1) * (y2 - y1)
                area_ratio = bbox_area / img_area if img_area > 0 else 0.0

                det = Detection(
                    class_name=cls_name,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    bbox_area_ratio=round(area_ratio, 4),
                )
                all_detections.append(det)

                if cls_name == target_class and conf > best_conf:
                    best_conf = conf
                    target_detection = det

        annotated_bytes = self._annotate(results, target_class)

        return DetectionResult(
            image_width=img_w,
            image_height=img_h,
            all_detections=all_detections,
            target_detection=target_detection,
            annotated_image=annotated_bytes,
        )

    def _annotate(self, results, target_class: str) -> bytes:
        """Genera una imagen JPEG con los bounding boxes dibujados."""
        try:
            annotated = results[0].plot()
            from PIL import Image as PILImage
            img_rgb = PILImage.fromarray(annotated[..., ::-1])  # BGR → RGB
            buf = io.BytesIO()
            img_rgb.save(buf, format="JPEG", quality=85)
            return buf.getvalue()
        except Exception:
            return b""


# Singleton global
_detector_instance: Optional[SnapDetector] = None


def get_detector() -> SnapDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SnapDetector()
    return _detector_instance


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Uso: python detector.py <imagen> <clase_objetivo>")
        print("Ejemplo: python detector.py foto.jpg cup")
        sys.exit(1)

    img_path = sys.argv[1]
    target   = sys.argv[2]

    detector = get_detector()
    result   = detector.analyze(img_path, target)

    print(f"\n📸 Imagen: {img_path} ({result.image_width}×{result.image_height})")
    print(f"🔍 Buscando: '{target}'")
    print(f"📦 Detecciones totales: {len(result.all_detections)}")

    if result.target_detection:
        td = result.target_detection
        print(f"\n✅ '{target}' ENCONTRADO:")
        print(f"   Confianza:  {td.confidence:.1%}")
        print(f"   Área frame: {td.bbox_area_ratio:.1%}")
        print(f"   BBox:       {[round(v) for v in td.bbox]}")
    else:
        print(f"\n❌ '{target}' no detectado")

    print("\n🗂️  Todas las detecciones:")
    for d in result.all_detections:
        marker = " ← TARGET" if d.class_name == target else ""
        print(f"   {d.class_name:<25} conf={d.confidence:.2f}  área={d.bbox_area_ratio:.2%}{marker}")
