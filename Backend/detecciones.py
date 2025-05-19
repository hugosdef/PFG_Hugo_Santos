# detections_logger.py
import csv
import os

# Ruta donde se guardan las detecciones
DETECTIONS_CSV = os.path.join(os.path.dirname(__file__), "detecciones.csv")

def init_logger(video_id):
    """
    Inicializa (o reinicia) el fichero de detecciones.
    Debe llamarse al arrancar el procesamiento de cada vídeo.
    """
    with open(DETECTIONS_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["video_id", "regla", "t_alerta"])


def log_detection(video_id, regla, t_alerta):
    """
    Añade una línea al fichero de detecciones.
    """
    with open(DETECTIONS_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([video_id, regla, f"{t_alerta:.3f}"])
