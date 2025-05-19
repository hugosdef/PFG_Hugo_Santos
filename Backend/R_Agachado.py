import numpy as np
import math

def calcular_angulo(a, b, c):
    """
    Explicación:
        Calcula el ángulo en el vértice 'b' formado por los puntos a, b y c utilizando el producto
        escalar y la norma de los vectores resultantes. Se convierte el ángulo a grados.
    
    Entradas:
        a, b, c:
            Arrays (o listas convertibles a array de numpy) que representan las coordenadas (x, y)
            de cada uno de los tres puntos.
    
    Salida:
        angulo:
            Ángulo en grados formado en el vértice 'b'.
    """
    ba = a - b
    bc = c - b
    cos_angulo = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    cos_angulo = np.clip(cos_angulo, -1.0, 1.0)
    angulo = np.degrees(np.arccos(cos_angulo))
    return angulo


def persona_agachada(keypoints, angulo_umbral=90):
    """
    Explicación:
        Determina si una persona se encuentra agachada analizando el ángulo formado en la rodilla.
        Utiliza la convención COCO para identificar los keypoints relevantes:
          - Lado izquierdo: cadera (índice 11), rodilla (índice 13) y tobillo (índice 15)
          - Lado derecho: cadera (índice 12), rodilla (índice 14) y tobillo (índice 16)
        Si alguno de estos ángulos es menor que el umbral establecido, se asume que la persona está agachada.
    
    Entradas:
        keypoints:
            Lista de keypoints de la persona. Cada keypoint debe contener al menos dos valores (x, y).
        angulo_umbral:
            Umbral en grados para el ángulo de la rodilla (por defecto 90°). Si el ángulo es menor, se
            considera que la persona está agachada.
    
    Salida:
        Retorna:
            - True, si alguno de los ángulos en las rodillas (izquierda o derecha) es menor que el umbral.
            - False, en caso contrario o si la detección de los keypoints no es válida.
    """
    
    if len(keypoints) < 8:
        return False
    try:
        cadera_izquierda = np.array(keypoints[11][:2], dtype="double")
        rodilla_izquierda = np.array(keypoints[13][:2], dtype="double")
        tobillo_izquierdo = np.array(keypoints[15][:2], dtype="double")
        
        cadera_derecha = np.array(keypoints[12][:2], dtype="double")
        rodilla_derecha = np.array(keypoints[14][:2], dtype="double")
        tobillo_derecho = np.array(keypoints[16][:2], dtype="double")
    except Exception:
        return False

    if (cadera_izquierda[0] == 0 and cadera_izquierda[1] == 0) or \
       (rodilla_izquierda[0] == 0 and rodilla_izquierda[1] == 0) or \
       (tobillo_izquierdo[0] == 0 and tobillo_izquierdo[1] == 0) or \
       (cadera_derecha[0] == 0 and cadera_derecha[1] == 0) or \
       (rodilla_derecha[0] == 0 and rodilla_derecha[1] == 0) or \
       (tobillo_derecho[0] == 0 and tobillo_derecho[1] == 0):
        return False

    angulo_pierna_izquierda = calcular_angulo(cadera_izquierda, rodilla_izquierda, tobillo_izquierdo)
    angulo_pierna_derecha = calcular_angulo(cadera_derecha, rodilla_derecha, tobillo_derecho)

    if angulo_pierna_izquierda < angulo_umbral or angulo_pierna_derecha < angulo_umbral:
        return True
    return False
