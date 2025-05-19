import math
import time
import numpy as np

class EuclideanDistTracker:
    """
    Explicación:
        Esta clase implementa un rastreador basado en la distancia euclídea para asignar y mantener
        identificadores únicos a objetos detectados a lo largo de frames consecutivos. Se utiliza para
        realizar el seguimiento de objetos en video, actualizando su posición, controlando su desaparición y
        fusionando cajas delimitadoras solapadas.
    
    Entrada (parámetros del constructor):
        max_desaparecidos:
            Número máximo de frames en que un objeto puede no ser detectado antes de eliminarlo.
        max_distancia:
            Distancia máxima permitida para considerar que dos detecciones corresponden al mismo objeto.
        variacion_tamano:
            Variación máxima permitida en el área del objeto para mantener su asignación.
        umbral_solapamiento:
            Porcentaje mínimo de solapamiento entre cajas para fusionarlas.
        distancia_minima:
            Distancia mínima que, si se cumple, asigna de inmediato el mismo ID a una detección.
    
    Salida:
        Una instancia del rastreador configurada para actualizar las detecciones y asignar identificadores.
    """
    def __init__(self, max_desaparecidos=125, max_distancia=650, variacion_tamano=float('inf'),
                 umbral_solapamiento=0.3, distancia_minima=150):
        self.puntos_centrales = {}     # Almacena el centro (x, y) de cada objeto detectado.
        self.desaparecidos = {}        # Cuenta los frames en que cada objeto no ha sido detectado.
        self.contador_ids = 0          # Contador para asignar nuevos identificadores.
        self.max_desaparecidos = max_desaparecidos
        self.tiempo_aparicion = {}     # Almacena el tiempo de aparición inicial de cada objeto.
        self.areas = {}                # Almacena el área (w*h) de la caja delimitadora de cada objeto.
        self.etiquetas = {}            # Almacena la etiqueta o clase asociada a cada objeto.
        self.max_distancia = max_distancia
        self.variacion_tamano = variacion_tamano
        self.umbral_solapamiento = umbral_solapamiento
        self.distancia_minima = distancia_minima

    def update(self, rectangulos_objetos):
        """
        Explicación:
            Actualiza el rastreador con las nuevas detecciones de objetos, asignando o actualizando IDs
            basándose en la posición y el tamaño de las cajas delimitadoras. También fusiona cajas solapadas.
        
        Entrada:
            rectangulos_objetos:
                Lista de detecciones, donde cada elemento es una lista con el formato [x, y, w, h, etiqueta].
        
        Salida:
            Retorna una lista de cajas con sus respectivos IDs y etiqueta, con el formato:
            [x, y, w, h, id_objeto, etiqueta].
        """
        # Fusionar cajas solapadas antes de asignar IDs
        rectangulos_objetos = self.merge_overlapping_boxes(rectangulos_objetos)
        cajas_ids_objetos = []
        ids_usados = set()

        if len(rectangulos_objetos) == 0:
            # Actualizar el contador de frames desaparecidos para todos los objetos
            for id_objeto in list(self.puntos_centrales.keys()):
                self.desaparecidos[id_objeto] += 1
                if self.desaparecidos[id_objeto] > self.max_desaparecidos:
                    self._eliminar_objeto(id_objeto)
            return cajas_ids_objetos

        for rect in rectangulos_objetos:
            x, y, w, h, etiqueta = rect
            centro_x = (x + x + w) // 2
            centro_y = (y + y + h) // 2
            area = w * h

            id_objeto_cercano = None
            distancia_minima_local = self.max_distancia

            for id_objeto, punto in self.puntos_centrales.items():
                distancia = math.hypot(centro_x - punto[0], centro_y - punto[1])
                area_previa = self.areas.get(id_objeto, 0)
                cambio_tamano = abs(area - area_previa) / area_previa if area_previa > 0 else 0

                # Asignación directa si la distancia es menor que distancia_minima y las etiquetas coinciden
                if distancia < self.distancia_minima and self.etiquetas.get(id_objeto) == etiqueta:
                    id_objeto_cercano = id_objeto
                    distancia_minima_local = distancia
                    break

                if (distancia < distancia_minima_local and cambio_tamano < self.variacion_tamano and
                    id_objeto not in ids_usados and self.etiquetas.get(id_objeto) == etiqueta):
                    id_objeto_cercano = id_objeto
                    distancia_minima_local = distancia

            if id_objeto_cercano is not None:
                self.puntos_centrales[id_objeto_cercano] = (centro_x, centro_y)
                self.desaparecidos[id_objeto_cercano] = 0
                self.areas[id_objeto_cercano] = area
                cajas_ids_objetos.append([x, y, w, h, id_objeto_cercano, etiqueta])
                ids_usados.add(id_objeto_cercano)
            else:
                nuevo_id = self.contador_ids
                self.contador_ids += 1

                motivo = "distancia o variación de tamaño excedida"
                if not self.puntos_centrales:
                    motivo = "no hay objetos anteriores"
                elif all(self.etiquetas.get(id_objeto) != etiqueta for id_objeto in self.puntos_centrales):
                    motivo = "ningún ID coincide en clase"
                elif all(math.hypot(centro_x - punto[0], centro_y - punto[1]) >= self.max_distancia
                         for punto in self.puntos_centrales.values()):
                    motivo = f"todas las distancias mayores que max_distancia={self.max_distancia}"
                print(f"Asignado nuevo ID {nuevo_id} -> motivo: {motivo}")

                self.puntos_centrales[nuevo_id] = (centro_x, centro_y)
                self.desaparecidos[nuevo_id] = 0
                self.tiempo_aparicion[nuevo_id] = time.time()
                self.areas[nuevo_id] = area
                self.etiquetas[nuevo_id] = etiqueta
                cajas_ids_objetos.append([x, y, w, h, nuevo_id, etiqueta])
                ids_usados.add(nuevo_id)

        # Incrementar contador de desaparecidos para los objetos no actualizados
        for id_objeto in list(self.puntos_centrales.keys()):
            if id_objeto not in ids_usados:
                self.desaparecidos[id_objeto] += 1
                if self.desaparecidos[id_objeto] > self.max_desaparecidos:
                    self._eliminar_objeto(id_objeto)

        return cajas_ids_objetos

    def _eliminar_objeto(self, id_objeto):
        """
        Explicación:
            Elimina el objeto del rastreador y borra su información asociada.
        
        Entrada:
            id_objeto:
                Identificador del objeto a eliminar.
        
        Salida:
            No retorna valor.
        """
        del self.puntos_centrales[id_objeto]
        del self.desaparecidos[id_objeto]
        del self.tiempo_aparicion[id_objeto]
        del self.areas[id_objeto]
        del self.etiquetas[id_objeto]

    def merge_overlapping_boxes(self, cajas):
        """
        Explicación:
            Fusiona cajas delimitadoras solapadas que pertenecen a la misma clase, basándose en un
            umbral de solapamiento definido.
        
        Entrada:
            cajas:
                Lista de cajas, donde cada caja tiene el formato [x, y, w, h, etiqueta].
        
        Salida:
            Retorna una lista de cajas fusionadas con el mismo formato.
        """
        if len(cajas) == 0:
            return []

        cajas_fusionadas = []
        cajas = np.array(cajas, dtype=object)

        for i in range(len(cajas)):
            x1, y1, w1, h1, etiqueta1 = cajas[i]
            caja1 = (x1, y1, x1 + w1, y1 + h1)
            fusionada = False

            for j, caja_fusionada in enumerate(cajas_fusionadas):
                x2, y2, w2, h2, etiqueta2 = caja_fusionada
                caja2 = (x2, y2, x2 + w2, y2 + h2)

                if etiqueta1 != etiqueta2:
                    continue

                xi1 = max(caja1[0], caja2[0])
                yi1 = max(caja1[1], caja2[1])
                xi2 = min(caja1[2], caja2[2])
                yi2 = min(caja1[3], caja2[3])
                area_interseccion = max(0, xi2 - xi1) * max(0, yi2 - yi1)

                area1 = w1 * h1
                area2 = w2 * h2
                area_union = area1 + area2 - area_interseccion
                solapamiento = area_interseccion / float(area_union)

                if solapamiento > self.umbral_solapamiento:
                    nuevo_x = min(x1, x2)
                    nuevo_y = min(y1, y2)
                    nuevo_w = max(caja1[2], caja2[2]) - nuevo_x
                    nuevo_h = max(caja1[3], caja2[3]) - nuevo_y
                    cajas_fusionadas[j] = [nuevo_x, nuevo_y, nuevo_w, nuevo_h, etiqueta1]
                    fusionada = True
                    break

            if not fusionada:
                cajas_fusionadas.append([x1, y1, w1, h1, etiqueta1])

        #print(f"[MERGE] Total tras fusión: {len(cajas_fusionadas)} cajas.")
        return cajas_fusionadas

# Inicializar un rastreador global
tracker = EuclideanDistTracker()








