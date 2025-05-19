from ultralytics import YOLO
import cv2
import numpy as np

# Cargar modelos
yolo_detector = YOLO(r"yolo11n.pt")
yolo_pose_model = YOLO("yolo11n-pose.pt")

def detect_objects(frame):
    """
    Procesa un frame para detectar objetos y estimar la pose.
    Retorna un diccionario con detecciones de personas, teléfonos, coches y poses.
    """
    detections = {"persons": [], "phones": [], "poses": [], "cars": []}

    results = yolo_detector(frame)[0]
    for box in results.boxes:
        cls_id = int(box.cls.item())
        conf = float(box.conf.item())
        label = yolo_detector.names[cls_id]
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        w, h = x2 - x1, y2 - y1

        if label == "person" and conf > 0.5:
            detections["persons"].append([x1, y1, w, h, "person"])
        elif label == "cell phone" and conf > 0.3:
            detections["phones"].append([x1, y1, w, h, "phone"])
        elif label == "car" and conf > 0.5:
            detections["cars"].append([x1, y1, w, h, "car"])

    
    pose_results = yolo_pose_model(frame)
    if pose_results and pose_results[0].keypoints is not None:
        # kp_array tendrá forma (n, 17, 2): n detecciones, 17 keypoints (cada uno [x,y])
        kp_array = pose_results[0].keypoints.xy.numpy()
        detections["poses"] = [person_kp.tolist() for person_kp in kp_array]
    else:
        detections["poses"] = [[] for _ in detections["persons"]]
    print(kp_array.shape)
    return detections




