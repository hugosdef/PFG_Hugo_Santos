import numpy as np

def regla_fotografia(keypoints):
    """
    Explicación:
        Evalúa una regla para determinar si la persona está realizando una fotografía.
        La lógica se basa en comparar la posición vertical de la muñeca con la del codo:
        se asume que, al tomar una fotografía, la muñeca estará más arriba (menor valor en Y)
        que el codo, tanto en el lado izquierdo como en el derecho.
    
    Entrada:
        keypoints:
            Lista de puntos clave (keypoints) de la persona, donde cada punto es una lista o array
            que contiene al menos dos elementos representando las coordenadas (x, y). Se espera que
            los índices relevantes sean:
                - Codo izquierdo: índice 7
                - Muñeca izquierda: índice 9
                - Codo derecho: índice 8
                - Muñeca derecha: índice 10
    
    Salida:
        Retorna True si se cumple que, para alguno de los lados (izquierdo o derecho), la muñeca está
        situada por encima del codo (es decir, el valor Y de la muñeca es menor que el del codo), lo que
        se interpreta como una indicación de que se está realizando una fotografía. En caso contrario, o si ocurre
        algún error al acceder a los keypoints, retorna False.
    """
    try:
        codo_izquierdo = keypoints[7][:2] if len(keypoints) > 7 else None
        muñeca_izquierda = keypoints[9][:2] if len(keypoints) > 9 else None
        codo_derecho = keypoints[8][:2] if len(keypoints) > 8 else None
        muñeca_derecha = keypoints[10][:2] if len(keypoints) > 10 else None
    except Exception as e:
        # En caso de error al acceder a los keypoints, retorna False.
        return False

    # La muñeca está más alta si su coordenada Y es menor que la del codo.
    if codo_izquierdo is not None and muñeca_izquierda is not None:
        if muñeca_izquierda[1] < codo_izquierdo[1]:
            return True

    # Misma lógica para el lado derecho.
    if codo_derecho is not None and muñeca_derecha is not None:
        if muñeca_derecha[1] < codo_derecho[1]:
            return True

    return False
