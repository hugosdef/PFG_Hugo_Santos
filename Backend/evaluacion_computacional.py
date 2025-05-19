# evaluacion_computacional.py
"""
Módulo para medir el rendimiento computacional del sistema.
Incluye tiempo real transcurrido, tiempo de CPU, uso de memoria,
FPS reales y latencia media por frame.
"""
import time
import psutil
import os

class EvaluacionComputacional:
    def __init__(self):
        # Referencia al proceso actual
        self.process = psutil.Process(os.getpid())
        self.start_time = None
        self.start_cpu_times = None
        self.start_memory = None
        self.end_time = None
        self.end_cpu_times = None
        self.end_memory = None
        self.frame_count = 0

    def start(self):
        """
        Inicia la medición: guarda tiempo de inicio,
        tiempos de CPU y uso de memoria inicial.
        """
        self.start_time = time.time()
        self.start_cpu_times = self.process.cpu_times()
        self.start_memory = self.process.memory_info().rss
        self.frame_count = 0

    def frame_processed(self):
        """
        Debe llamarse cada vez que se procesa un frame
        para contar fotogramas.
        """
        self.frame_count += 1

    def stop(self):
        """
        Detiene la medición: guarda tiempo de fin,
        tiempos de CPU y uso de memoria final.
        """
        self.end_time = time.time()
        self.end_cpu_times = self.process.cpu_times()
        self.end_memory = self.process.memory_info().rss

    def get_results(self):
        """
        Calcula y devuelve un diccionario con:
          - elapsed_time_sec: tiempo real transcurrido (segundos)
          - cpu_user_sec: tiempo de CPU en modo usuario (segundos)
          - cpu_system_sec: tiempo de CPU en modo sistema (segundos)
          - memory_usage_bytes: memoria adicional consumida (bytes)
          - frames: fotogramas procesados
          - fps_real: fotogramas reales por segundo
          - latency_ms: latencia media por frame en milisegundos
        """
        elapsed = self.end_time - self.start_time
        cpu_user = self.end_cpu_times.user - self.start_cpu_times.user
        cpu_system = self.end_cpu_times.system - self.start_cpu_times.system
        mem_used = self.end_memory - self.start_memory
        fps_real = self.frame_count / elapsed if elapsed > 0 else 0
        latency_ms = (elapsed * 1000 / self.frame_count) if self.frame_count > 0 else 0

        return {
            "elapsed_time_sec": elapsed,
            "cpu_user_sec": cpu_user,
            "cpu_system_sec": cpu_system,
            "memory_usage_bytes": mem_used,
            "frames": self.frame_count,
            "fps_real": fps_real,
            "latency_ms": latency_ms
        }

    def print_report(self):
        """
        Muestra por pantalla un informe formateado de los resultados.
        """
        results = self.get_results()
        print(f"Tiempo transcurrido: {results['elapsed_time_sec']:.3f} s")
        print(f"Frames procesados: {results['frames']}")
        print(f"FPS real: {results['fps_real']:.2f}")
        print(f"Latencia media por frame: {results['latency_ms']:.2f} ms")
        print(f"Tiempo CPU [user]: {results['cpu_user_sec']:.3f} s")
        print(f"Tiempo CPU [system]: {results['cpu_system_sec']:.3f} s")
        print(f"Memoria usada: {results['memory_usage_bytes'] / 1024 / 1024:.3f} MB")