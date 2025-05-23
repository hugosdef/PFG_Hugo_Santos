/Backend/

				Contiene los scripts del sistema.

				- "alerta_email.py"

				- "APP.py"

				- "detecciones.py"

				- "evaluacion_computacional.py"

				- "R_agachado.py"

				- "R_Fotografia.py"

				- "R_Mirada.py"

				- "R_Rostro.py"

				- "R_Tiempo_En_Escena.py"

				- "Tracker_Objetos.py"

				- "Yolo_Detecciones.py"

/Frontend/
				
				Interfaz web del sistema.

				- "analisis.html"

				- "miapptfg.html"

				- "Video1.mp4"

				- "Vivienda.html"

/Haar Cascade/

				- "mouth.xml"

- "yolo11n.pt"
- "yolo11n-pose.pt"
  

Cómo usar el sistema
---------------------

1. Descarga el directorio, asegurándote de mantener la estructura de subcarpetas tal como aparece (Backend, Frontend, Haar Cascade y modelos YOLO).
2. Ejecutar "APP.py" (ver más abajo Requisitos).
3. Ejecutar "análisis.html" y subir un vídeo.
4. El sistema procesará el vídeo, generará el vídeo procesado y los resultados en la interfaz web.
5. En caso de comportamiento sospechoso, se enviará una alerta por correo electrónico al correo detallado en la línea 394 de "APP.py" en la variable "destinatario" del código (El destinatario puede cambiarse modificando dicha línea en el código fuente).


Requisitos
-----------

- Python 3.9.13
- Paquetes: flask, flask-cors, opencv-python, numpy, ultralytics y psutil.
- En R_Rostro.py cambiar la ruta de la variable "mouth_cascade" con la ruta local al archivo "mouth.xml" del ordenador del usuario.
- Conexión a Internet (para envío de correos desde `alerta_email.py`).

  
Autor
------
Hugo Santos de Felipe  
Grado en Ingeniería Matemática y Título Propio en Quantum Computing – Universidad Francisco de Vitoria  
Año: 2025

   
