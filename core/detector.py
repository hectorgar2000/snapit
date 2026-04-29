"""
detector.py — SnapIT
Wrapper de detección con soporte dual:

  YOLO_MODE=coco   → YOLOv8n (80 clases COCO, ~6 MB RAM) — modo por defecto / plan gratuito
  YOLO_MODE=world  → YOLO-World + CLIP (365+ clases, ~600 MB RAM) — requiere plan Hobby

Para cambiar de modo en Railway: Variables → YOLO_MODE → world
"""

import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from PIL import Image

# ─── Modo de detección ────────────────────────────────────────────────────────
_USE_YOLO_WORLD = os.getenv("YOLO_MODE", "coco").lower() == "world"


@dataclass
class Detection:
    """Una detección individual de YOLO."""
    class_name: str
    confidence: float
    bbox: tuple
    bbox_area_ratio: float


@dataclass
class DetectionResult:
    """Resultado completo del análisis de una imagen."""
    image_width: int
    image_height: int
    all_detections: list[Detection]
    target_detection: Optional[Detection]
    annotated_image: Optional[bytes]


class SnapDetector:
    MODEL_WORLD = "yolov8s-worldv2.pt"
    MODEL_COCO  = "yolov8n.pt"
    CONFIDENCE_THRESHOLD = 0.25

    _CLUTTER_CLASSES = [
        "person", "chair", "table", "laptop", "phone", "bottle",
        "cup", "book", "bag", "car", "sofa", "bed", "tv", "backpack",
    ]

    def __init__(self):
        self._model = None
        self._current_classes: list[str] = []

    def _load_model(self):
        """Carga el modelo según el modo activo."""
        if self._model is not None:
            return
        try:
            if _USE_YOLO_WORLD:
                from ultralytics import YOLOWorld
                print(f"🔄 Cargando {self.MODEL_WORLD} (YOLO-World / Objects365)...")
                self._model = YOLOWorld(self.MODEL_WORLD)
                print("✅ YOLO-World cargado")
            else:
                from ultralytics import YOLO
                print(f"🔄 Cargando {self.MODEL_COCO} (YOLOv8 COCO)...")
                self._model = YOLO(self.MODEL_COCO)
                print("✅ YOLOv8-COCO cargado")
        except ImportError:
            raise RuntimeError("ultralytics no está instalado.")

    def _set_classes(self, target_class: str):
        """Solo necesario en modo YOLO-World."""
        if not _USE_YOLO_WORLD:
            return
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
        self._load_model()
        self._set_classes(target_class)

        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        else:
            raise ValueError("image_input debe ser path (str/Path) o bytes")

        img_w, img_h = img.size
        img_area = img_w * img_h

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
        try:
            annotated = results[0].plot()
            from PIL import Image as PILImage
            img_rgb = PILImage.fromarray(annotated[..., ::-1])
            buf = io.BytesIO()
            img_rgb.save(buf, format="JPEG", quality=85)
            return buf.getvalue()
        except Exception:
            return b""


_detector_instance: Optional[SnapDetector] = None


def get_detector() -> SnapDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SnapDetector()
    return _detector_instance
