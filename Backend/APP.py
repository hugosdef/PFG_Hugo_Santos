import cv2
import numpy as np
import os
import time
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from Yolo_Detecciones import detect_objects
from Tracker_Objetos import tracker, EuclideanDistTracker  

from R_Tiempo_En_Escena import tiempo_en_escena, memoria_comportamiento
from R_Mirada import es_frontal 
from R_Rostro import regla_rostro
from R_Agachado import persona_agachada
from R_Fotografia import regla_fotografia
from alerta_email import send_suspicious_alert
from evaluacion_computacional import EvaluacionComputacional
from detecciones import init_logger,log_detection

app = Flask(__name__)
CORS(app)

# Directorios de archivos estáticos y frames capturados
DIRECTORIO_STATIC = r"C:\mi-aplicacion2\static"
DIRECTORIO_FRAMES_CAPTURADOS = os.path.join(DIRECTORIO_STATIC, "captured_frames")

# Crear directorios si no existen
for directorio in [DIRECTORIO_STATIC, DIRECTORIO_FRAMES_CAPTURADOS]:
    if not os.path.exists(directorio):
        os.makedirs(directorio)

# Directorio donde guardamos las capturas de comportamientos sospechosos
CAPTURES_DIR = os.path.join(DIRECTORIO_STATIC, "actividades_sospechosas")
os.makedirs(CAPTURES_DIR, exist_ok=True)
for f in os.listdir(CAPTURES_DIR):
    os.remove(os.path.join(CAPTURES_DIR, f))

    
frame_capturado = None  # Almacena el último frame capturado (si lo hubiera)
personas_capucha_detectada = set()  # Evita alertas repetidas para la misma persona

# Variables globales de progreso
contador_frames_actual = 0
total_de_frames = 0

# Instanciar rastreadores
rastreador_telefono = EuclideanDistTracker(max_desaparecidos=100, max_distancia=600, variacion_tamano=0.75,
                                           umbral_solapamiento=0.3, distancia_minima=150)
rastreador_coche = EuclideanDistTracker(max_desaparecidos=50, max_distancia=500, variacion_tamano=0.7,
                                        umbral_solapamiento=0.3, distancia_minima=100)

# Diccionarios para seguimiento de coches estáticos
conteo_coche_estatico = {}
ultima_bbox_coche = {}


conteo_frames_persona_mask  = {}  
conteo_mask_detectada = {}    

@app.route("/")
def home():
    return "Servidor Flask funcionando correctamente."

# Endpoint de progreso
@app.route("/progress", methods=["GET"])
def progress():
    return jsonify({
        "actual": contador_frames_actual,
        "total": total_de_frames
    })

@app.route("/procesar_video", methods=["POST"])
def procesar_video():
    global frame_capturado, personas_capucha_detectada, contador_frames_actual, total_de_frames, conteo_deteccion_oreja, conteo_frames_persona
    eval_comp = EvaluacionComputacional()
    eval_comp.start()

    conteo_mask_detectada       = {}
    conteo_frames_persona_mask = {}

    info_frames_capturados = {}  # No se guardan frames, solo se procesan
    contador_frontal = {}        # Cuenta de frames con detección frontal
    personas_agachadas = set()    # Para evitar alertas múltiples de "agachado"
    ids_sospechosos = set()       # IDs considerados sospechosos (para caja fija)

    try:
        if "video" not in request.files:
            return jsonify({"error": "No se ha enviado ningún archivo"}), 400

        # Limpiar directorios y reiniciar variables
        for archivo in os.listdir(DIRECTORIO_FRAMES_CAPTURADOS):
            os.remove(os.path.join(DIRECTORIO_FRAMES_CAPTURADOS, archivo))
        personas_capucha_detectada.clear()

        video_file = request.files["video"]
        ruta_video = os.path.join(DIRECTORIO_STATIC, "temp_video.mp4")
        ruta_video_procesado = os.path.join(DIRECTORIO_STATIC, "output_video.mp4")

        if os.path.exists(ruta_video):
            os.remove(ruta_video)
        if os.path.exists(ruta_video_procesado):
            os.remove(ruta_video_procesado)

        video_file.save(ruta_video)
        video_id = os.path.splitext(os.path.basename(ruta_video))[0]
        #init_logger(video_id)

        cap = cv2.VideoCapture(ruta_video)
        if not cap.isOpened():
            return jsonify({"error": "No se pudo abrir el video. Verifica el formato."}), 500

        ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        total_de_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        contador_frames = 0

        # Umbral frontal: 1.5 segundos de frames frontales
        umbral_frontal = int(1.5 * fps)

        try:
            fourcc = cv2.VideoWriter_fourcc(*'H264')
            video_writer = cv2.VideoWriter(ruta_video_procesado, fourcc, fps, (ancho, alto))
            if not video_writer.isOpened():
                raise Exception("Fallback necesario")
        except:
            print("H264 no disponible, cambiando a mp4v")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(ruta_video_procesado, fourcc, fps, (ancho, alto))

        if not video_writer.isOpened():
            return jsonify({"error": "No se pudo inicializar el VideoWriter."}), 500

        sospechoso = False
        razones_finales = set()

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            eval_comp.frame_processed() 
            contador_frames += 1
            contador_frames_actual = contador_frames
            print(f"Procesando frame {contador_frames} de {total_de_frames}...")
            t_alerta = contador_frames / fps

            detecciones = detect_objects(frame)
            if not isinstance(detecciones, dict):
                print("ERROR: detect_objects() no devolvió un diccionario, se corrige...")
                detecciones = {"persons": [], "phones": [], "poses": [], "cars": []}

            # Actualizar rastreadores para personas, teléfonos y coches
            objetos_rastreado = tracker.update(detecciones.get("persons", []))
            telefonos_rastreado = rastreador_telefono.update(detecciones.get("phones", []))
            coches_rastreado = tracker.update(detecciones.get("cars", []))

            # Seguimiento de coches estáticos
            for coche in coches_rastreado:
                x, y, w, h, id_coche, etiqueta = coche
                bbox_actual = (x, y, w, h)
                if id_coche in ids_sospechosos:
                    bbox_ultima = ultima_bbox_coche.get(id_coche, bbox_actual)
                    centro_ultimo = (bbox_ultima[0] + bbox_ultima[2] / 2, bbox_ultima[1] + bbox_ultima[3] / 2)
                    centro_actual = (x + w / 2, y + h / 2)
                    dist = np.linalg.norm(np.array(centro_actual) - np.array(centro_ultimo))
                    if dist > 20:
                        ids_sospechosos.discard(id_coche)
                        conteo_coche_estatico[id_coche] = 1
                        ultima_bbox_coche[id_coche] = bbox_actual
                    else:
                        conteo_coche_estatico[id_coche] = 100
                else:
                    if id_coche in ultima_bbox_coche:
                        if ultima_bbox_coche[id_coche] == bbox_actual:
                            conteo_coche_estatico[id_coche] += 1
                        else:
                            conteo_coche_estatico[id_coche] = 1
                            ultima_bbox_coche[id_coche] = bbox_actual
                    else:
                        conteo_coche_estatico[id_coche] = 1
                        ultima_bbox_coche[id_coche] = bbox_actual

                    if conteo_coche_estatico[id_coche] >= 5:
                        razones_finales.add(f"Coche {id_coche} parado en la propiedad.")
                        ids_sospechosos.add(id_coche)
                        ruta = os.path.join(CAPTURES_DIR, f"persona_{id_coche}.jpg")
                        cv2.imwrite(ruta, frame)

            # Reglas de comportamiento para personas
            es_sospechoso, razones_detectadas = tiempo_en_escena(objetos_rastreado, contador_frames, fps, frame_capturado)
            if es_sospechoso:
                sospechoso = True
                #log_detection(video_id, "tiempo_en_escena", t_alerta)
            for razon in razones_detectadas:
                razones_finales.add(razon)
                tokens = razon.split()
                #
                if len(tokens) > 2 and tokens[1].isdigit():
                    ids_sospechosos.add(int(tokens[1]))

            # Detección de teléfonos con poses (posible fotografía)
            if len(detecciones.get("phones", [])) > 0:
                condicion_telefono = False
                if "poses" in detecciones and len(detecciones["poses"]) > 0:
                    for pose in detecciones["poses"]:
                        # Cada 'pose' es la lista de 17 pares [x, y]
                        keypoints = pose
                        if len(keypoints) >= 11:
                            if regla_fotografia(keypoints):
                                #condicion_telefono = True
                                #log_detection(video_id, "regla_fotografia", t_alerta)
                                break
                if condicion_telefono:
                    razones_finales.add("Se ha detectado un teléfono y las muñecas están más altas que los codos. Posible foto.")
                    ruta = os.path.join(CAPTURES_DIR, f"persona.jpg")
                    cv2.imwrite(ruta, frame)
 
            for idx, (x, y, w, h, id_objeto, etiqueta) in enumerate(objetos_rastreado):
                if etiqueta == "person" and "poses" in detecciones and idx < len(detecciones["poses"]):
                    kp_data = detecciones["poses"][idx]
                    if isinstance(kp_data, list) and len(kp_data) >= 5:
                        keypoints = kp_data  # Lista de 17 pares [x, y]
                        bbox_objeto = (x, y, x + w, y + h)
                 
                        if es_frontal(keypoints[:5]):
                            conteo_frames_persona_mask[id_objeto] = conteo_frames_persona_mask.get(id_objeto, 0) + 1
                            lleva_mask = regla_rostro(frame, keypoints, id_objeto, bbox_objeto)
                            print(f"[DEBUG] Persona {id_objeto}: lleva mascarilla? {lleva_mask}")
                            
                            if lleva_mask:
                                conteo_mask_detectada[id_objeto] = conteo_mask_detectada.get(id_objeto, 0) + 1
                            
            # Dibujar cajas para personas
            for idx, (x, y, w, h, id_objeto, etiqueta) in enumerate(objetos_rastreado):
                if etiqueta == "person":
                    frontal = False
                    agachada = False
                    if "poses" in detecciones and idx < len(detecciones["poses"]):
                        kp_data = detecciones["poses"][idx]
                        if isinstance(kp_data, list) and len(kp_data) > 0:
                            keypoints = kp_data  # Lista de 17 pares [x, y]
                            if len(keypoints) >= 5:
                                frontal = es_frontal(keypoints[:5])
                            if len(keypoints) >= 17:
                                agachada = persona_agachada(keypoints)
                    if frontal:
                        contador_frontal[id_objeto] = contador_frontal.get(id_objeto, 0) + 1

                    if frontal and agachada:
                        color = (0, 0, 255)  # Rojo para frontal y agachado
                        texto = "SOSPECHOSO: Frontal y Agachado"
                        ids_sospechosos.add(id_objeto)
                        ruta = os.path.join(CAPTURES_DIR, f"persona_{id_objeto}.jpg")
                        cv2.imwrite(ruta, frame)
                    elif frontal:
                        color = (255, 0, 255)  # Púrpura para frontal
                        texto = "SOSPECHOSO MIRANDO A LA CAMARA"
                        if contador_frontal.get(id_objeto, 0) >= umbral_frontal:
                            ids_sospechosos.add(id_objeto)
                            #log_detection(video_id, "es_frontal", t_alerta)
                            ruta = os.path.join(CAPTURES_DIR, f"persona_{id_objeto}.jpg")
                            cv2.imwrite(ruta, frame)
                    elif agachada:
                        color = (255, 165, 0)  # Naranja para agachado
                        texto = "AGACHADO"
                        ids_sospechosos.add(id_objeto)
                        razones_finales.add(f"La persona {id_objeto} se ha agachado en el entorno de la propiedad.")
                        #log_detection(video_id, "es_agachado", t_alerta)
                        ruta = os.path.join(CAPTURES_DIR, f"persona_{id_objeto}.jpg")
                        cv2.imwrite(ruta, frame)
                    else:
                        color = (0, 255, 0)  # Verde por defecto
                        texto = f"Persona {id_objeto}"

                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(frame, texto, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    if id_objeto in ids_sospechosos:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 4)
                        cv2.putText(frame, "SOSPECHOSO", (x, y - 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                else:
                    color = (0, 0, 255)
                    texto = "Phone"
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(frame, texto, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Dibujar cajas para teléfonos rastreados
            for x, y, w, h, id_telefono, etiqueta in telefonos_rastreado:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, f"Phone {id_telefono}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Dibujar cajas para coches rastreados
            for x, y, w, h, id_coche, etiqueta in coches_rastreado:
                if id_coche in conteo_coche_estatico and conteo_coche_estatico[id_coche] >= 5:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 4)
                    cv2.putText(frame, "COCHE PARADO", (x, y - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                else:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                    cv2.putText(frame, f"Car {id_coche}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Dibujar keypoints de pose y esqueleto
            if "poses" in detecciones:
                esqueleto = [
                    (0, 1), (0, 2), (1, 3), (2, 4),
                    (0, 5), (0, 6), (5, 7), (7, 9),
                    (6, 8), (8, 10), (5, 6), (5, 11),
                    (6, 12), (11, 12), (11, 13), (13, 15),
                    (12, 14), (14, 16)
                ]
                for pose in detecciones["poses"]:
                    if isinstance(pose, list) and len(pose) > 0:
                        keypoints = pose  # Cada pose es una lista de 17 pares [x, y]
                        puntos = []
                        for kp in keypoints:
                            kp_flat = np.array(kp).flatten()
                            if kp_flat.shape[0] >= 2:
                                x_kp = int(kp_flat[0])
                                y_kp = int(kp_flat[1])
                                if x_kp == 0 and y_kp == 0:
                                    puntos.append(None)
                                else:
                                    puntos.append((x_kp, y_kp))
                                    cv2.circle(frame, (x_kp, y_kp), radius=3,
                                               color=(255, 0, 0), thickness=-1)
                            else:
                                puntos.append(None)
                        for (i, j) in esqueleto:
                            if i < len(puntos) and j < len(puntos):
                                pt1 = puntos[i]
                                pt2 = puntos[j]
                                if pt1 is not None and pt2 is not None:
                                    cv2.arrowedLine(frame, pt1, pt2,
                                                    color=(255, 0, 0), thickness=2, tipLength=0.03)

            video_writer.write(frame)

        cap.release()
        video_writer.release()
        time.sleep(2)

        # Umbral dinámico para detección frontal: 1.5 segundos en términos de fps
        umbral_frontal = int(1.5 * fps)
        for id_objeto, conteo in contador_frontal.items():
            if conteo >= umbral_frontal:
                razones_finales.add(f"La persona {id_objeto} ha aparecido mirando a la cámara más de 1.5 segundos.")
                ids_sospechosos.add(id_objeto)

                ruta = os.path.join(CAPTURES_DIR, f"persona_{id_objeto}.jpg")
                cv2.imwrite(ruta, frame)

        # Comprobar que el tiempo total en escena > 15 segundos para personas
        tiempo_actual_segundos = contador_frames / fps
        for id_objeto, datos in memoria_comportamiento.items():
            if datos['tiempo_maximo'] >= 15 and not datos['alerta_final_mostrada']:
                razones_finales.add(f"La persona {id_objeto} ha estado en la escena un total de {round(datos['tiempo_maximo'],2)} segundos (final).")
                datos['alerta_final_mostrada'] = True
                ids_sospechosos.add(id_objeto)
                ruta = os.path.join(CAPTURES_DIR, f"persona_{id_objeto}.jpg")
                cv2.imwrite(ruta, frame)

        for id_objeto, total in conteo_frames_persona_mask.items():
            con_mask = conteo_mask_detectada.get(id_objeto, 0)
            
            sin_mask = total - con_mask
            if total < 35:
                prob_sin = 1
            else:
                prob_sin = sin_mask / total
            print(f"[DEBUG] Persona {id_objeto}: sin mascarilla en {prob_sin:.2f} de sus frames frontales")
            print(total)
            if prob_sin < 0.5:
                razones_finales.add(f"La persona {id_objeto} ha estado frontal con la parte inferior del rostro oculta durante >50% del tiempo.")
                ids_sospechosos.add(id_objeto)
                ruta = os.path.join(CAPTURES_DIR, f"persona_{id_objeto}.jpg")
                cv2.imwrite(ruta, frame)
        if not os.path.exists(ruta_video_procesado):
            return jsonify({"error": "No se generó el video procesado."}), 500
        
        eval_comp.stop()
        results = eval_comp.get_results()
        eval_comp.print_report()

        if razones_finales:
            vid_path = os.path.join(DIRECTORIO_STATIC, "output_video.mp4")
            destinatario = "hugosantosdefelipe@gmail.com"
            send_suspicious_alert(destinatario, list(razones_finales), captures_dir=CAPTURES_DIR)

        

        return jsonify({
            "mensaje": "Video procesado sin alertas." if not razones_finales else "Video procesado con alertas.",
            "razones": list(razones_finales),
            "video_url": f"http://127.0.0.1:5101/static/output_video.mp4?t={int(time.time())}",
            "captured_frame": frame_capturado
        })

    except Exception as e:
        print("ERROR INTERNO:", e)
        print(traceback.format_exc())
        return jsonify({"error": f"Error en el servidor: {str(e)}"}), 500

@app.route("/static/<filename>")
def obtener_video_procesado(filename):
    ruta_archivo = os.path.join(DIRECTORIO_STATIC, filename)
    if os.path.exists(ruta_archivo):
        return send_file(ruta_archivo, mimetype="video/mp4")
    return "Archivo no encontrado", 404

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5101)
