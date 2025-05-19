import cv2
import numpy as np
import os

memoria_comportamiento = {}

def tiempo_en_escena(objetos_rastreados, contador_frames, fps, frame_capturado, umbral_tiempo_rastreo=15, umbral_eliminacion=1):
    """
    Explicación:
        Actualiza el tiempo de permanencia en escena para cada persona detectada y genera alertas (a través de 'reasons')
        cuando una persona ha estado en la escena por un tiempo acumulado mayor o igual al umbral de rastreo.
        Además, elimina de la memoria a las personas que han dejado de ser detectadas por un tiempo mayor al umbral de eliminación.
    
    Entrada:
        objetos_rastreados:
            Lista de objetos rastreados, donde cada objeto es una lista con el formato [x, y, w, h, id_objeto, label].
        contador_frames:
            Número total de frames procesados hasta el momento.
        fps:
            Frames por segundo del video.
        frame_capturado:
            Último frame capturado (puede ser utilizado para otras operaciones, aunque en esta función no se usa directamente).
        umbral_tiempo_rastreo:
            Tiempo (en segundos) mínimo que una persona debe haber estado en escena para que se emita una alerta final.
        umbral_eliminacion:
            Tiempo (en segundos) que determina cuándo se considera que una persona ha desaparecido de la escena.
    
    Salida:
        Retorna una tupla (suspicious, reasons):
            - suspicious (bool): True si alguna persona ha superado el umbral de tiempo en escena, False en caso contrario.
            - reasons (list): Lista de cadenas con las alertas generadas para las personas que han estado en escena.
    """
    reasons = []
    tiempo_actual = contador_frames / fps

    # Filtrar únicamente las detecciones correspondientes a personas
    personas = [obj for obj in objetos_rastreados if obj[5] == "person"]

    # Procesar cada persona detectada
    for x, y, w, h, id_objeto, etiqueta in personas:
        nueva_caja = (x, y, w, h)
        
        if id_objeto not in memoria_comportamiento:
            memoria_comportamiento[id_objeto] = {
                'tiempo_inicio': tiempo_actual,
                'ultimo_visto': tiempo_actual,
                'tiempo_maximo': 0,
                'alerta_final_mostrada': False,
                'caja': nueva_caja
            }
        else:
            memoria_comportamiento[id_objeto]['caja'] = nueva_caja
            memoria_comportamiento[id_objeto]['ultimo_visto'] = tiempo_actual

        datos = memoria_comportamiento[id_objeto]
        tiempo_total = tiempo_actual - datos['tiempo_inicio']
        if tiempo_total > datos['tiempo_maximo']:
            datos['tiempo_maximo'] = tiempo_total

    # Verificar personas que han desaparecido
    for id_objeto in list(memoria_comportamiento.keys()):
        datos = memoria_comportamiento[id_objeto]
        tiempo_desde_ultimo_visto = tiempo_actual - datos['ultimo_visto']
        if tiempo_desde_ultimo_visto > umbral_eliminacion:
            if (datos.get('tiempo_maximo') or 0) >= umbral_tiempo_rastreo and not datos['alerta_final_mostrada']:
                reasons.append(f"La persona {id_objeto} ha estado en la escena un total de {round(datos['tiempo_maximo'], 2)} segundos (final).")
                datos['alerta_final_mostrada'] = True
            if tiempo_desde_ultimo_visto > umbral_eliminacion * 5:
                del memoria_comportamiento[id_objeto]

    suspicious = any((datos.get('tiempo_maximo') or 0) >= umbral_tiempo_rastreo for datos in memoria_comportamiento.values())
    return suspicious, reasons



























































