from dataclasses import dataclass


# Representa un bloque de ejecución continua de un proceso en el Gantt.
# Un mismo proceso puede generar múltiples segmentos (p.ej. en Round Robin).
@dataclass
class SegmentoEjecucion:
    # Nombre del proceso que ocupó la CPU en este bloque.
    nombre_proceso: str

    # Tick de inicio del bloque.
    inicio: int

    # Tick de fin del bloque (exclusivo).
    fin: int

    # Tiempo de llegada original del proceso (para cálculo de espera).
    tiempo_llegada: int

    # Duración calculada del segmento.
    @property
    def duracion(self) -> int:
        return self.fin - self.inicio

    def __repr__(self) -> str:
        return f"Segmento({self.nombre_proceso}, t={self.inicio}→{self.fin})"
