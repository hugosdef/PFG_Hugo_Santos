import numpy as np
import math

def es_frontal(keypoints, tolerancia_angulo=40, tolerancia_centralidad=0.35, tolerancia_simetria=0.35):
    """
    Explicación:
        Determina si la orientación de una cara es frontal evaluando la posición de los keypoints faciales:
        la nariz, los ojos y las orejas. La función verifica que la línea que une los ojos tenga una inclinación
        dentro de un rango tolerado, que la nariz esté centrada entre ellos y que la distancia de la nariz a cada
        oreja sea similar (simetría).
    
    Entrada:
        keypoints:
            Lista de puntos clave faciales, donde se espera que:
              - keypoints[0]: Nariz (coordenadas x, y)
              - keypoints[1]: Ojo izquierdo (coordenadas x, y)
              - keypoints[2]: Ojo derecho (coordenadas x, y)
              - keypoints[3]: Oreja izquierda (coordenadas x, y)
              - keypoints[4]: Oreja derecha (coordenadas x, y)
        tolerancia_angulo:
            Valor máximo (en grados) permitido para la inclinación de la línea que une los ojos.
        tolerancia_centralidad:
            Valor máximo permitido para la diferencia horizontal relativa entre la nariz y el punto medio de los ojos.
        tolerancia_simetria:
            Valor máximo permitido para la diferencia relativa entre las distancias de la nariz a cada oreja.
    
    Salida:
        Retorna True si se considera que la cara está orientada de forma frontal según los parámetros definidos,
        y False en caso contrario.
    """
    try:
        nariz = np.array(keypoints[0][:2], dtype="double")
        ojo_izq = np.array(keypoints[1][:2], dtype="double")
        ojo_der = np.array(keypoints[2][:2], dtype="double")
        oreja_izq = np.array(keypoints[3][:2], dtype="double")
        oreja_der = np.array(keypoints[4][:2], dtype="double")
    except Exception as e:
        return False

    # Asegurarse de que el ojo izquierdo esté a la izquierda del ojo derecho
    if ojo_izq[0] > ojo_der[0]:
        ojo_izq, ojo_der = ojo_der, ojo_izq

    # Calcular el ángulo de la línea que une los ojos
    delta_x = ojo_der[0] - ojo_izq[0]
    delta_y = ojo_der[1] - ojo_izq[1]
    angulo = math.degrees(math.atan2(delta_y, delta_x))
    if abs(angulo) > tolerancia_angulo:
        return False

    # Verificar que la nariz esté centrada entre los ojos
    punto_medio = (ojo_izq + ojo_der) / 2.0
    diferencia_horizontal = abs(nariz[0] - punto_medio[0])
    distancia_ojos = np.linalg.norm(ojo_der - ojo_izq)
    if distancia_ojos == 0:
        return False
    rel_centralidad = diferencia_horizontal / distancia_ojos
    if rel_centralidad > tolerancia_centralidad:
        return False

    # Evaluar la simetría comparando las distancias de la nariz a cada oreja
    d1 = np.linalg.norm(nariz - oreja_izq)
    d2 = np.linalg.norm(nariz - oreja_der)
    if (d1 + d2) == 0:
        return False
    diff_relativa = abs(d1 - d2) / ((d1 + d2) / 2.0)
    if diff_relativa > tolerancia_simetria:
        return False

    return True

