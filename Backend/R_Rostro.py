import cv2
import numpy as np
import os
import time

# Carga del cascade de boca
mouth_cascade = cv2.CascadeClassifier(r"C:\mi-aplicacion2\Haar Cascade\mouth.xml")
if mouth_cascade.empty():
    raise RuntimeError("No se pudo cargar mouth.xml")

# # Directorio donde guardaremos las ROIs para debug
# DEBUG_DIR = r"C:\mi-aplicacion2\debug_faces"
# os.makedirs(DEBUG_DIR, exist_ok=True)

def regla_rostro(frame, keypoints, id_objeto, bbox):
    """
    Detección de mascarilla basándonos en la zona de la boca justo debajo de la nariz.
    Se guarda la ROI en DEBUG_DIR como JPG para inspección.
    """
    x, y, w, h = bbox

    # Si existe el keypoint de la nariz (índice 0)
    nx, ny = keypoints[0]
    if nx > 0 and ny > 0:
        # Ajustes para ROI boca
        offset_y = 5                       # empezamos pocos píxeles debajo de la nariz
        roi_h = max(10, int(h * 0.05))     # alto fijo o 10% de la altura del bbox
        roi_w = max(25, int(w * 0.05))     # ancho fijo o 30% del ancho del bbox

        x1 = int(max(nx - roi_w // 2, 0))
        y1 = int(min(ny + offset_y, frame.shape[0] - 1))
        x2 = int(min(x1 + roi_w, frame.shape[1]))
        y2 = int(min(y1 + roi_h, frame.shape[0]))
        debug_mode = "mouth_nose"
    else:
        # Si no hay nariz, fallback a mitad superior del bbox
        x1, y1 = x, y
        x2, y2 = x + w, y + h // 2
        debug_mode = "fallback"

    # Extraer la ROI
    roi = frame[y1:y2, x1:x2]

    # # Guardar para debug
    # timestamp = int(time.time() * 1000)
    # fname = f"obj{id_objeto}_{debug_mode}_{timestamp}.jpg"
    # path = os.path.join(DEBUG_DIR, fname)
    # if roi.size > 0:
    #     cv2.imwrite(path, roi)
    #     print(f"[DEBUG] Guardada ROI obj {id_objeto} ({debug_mode}) → {path}")
    # else:
    #     print(f"[DEBUG] ROI vacía para obj {id_objeto}, modo={debug_mode}")

    if roi.size == 0:
        return False

    # Convertir a gris y buscar bocas
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    mouths = mouth_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(max(5, roi_w//5), max(5, roi_h//5))
    )

    if len(mouths) > 0:
        print(f"[DEBUG] Obj {id_objeto}: boca encontrada en ROI → NO mascarilla")
        return False

    print(f"[DEBUG] Obj {id_objeto}: no detecta boca en ROI → LLEVA mascarilla")
    return True
