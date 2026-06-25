from dataclasses import dataclass, field
from typing import Optional


# Representa un proceso del sistema operativo con todos sus atributos
# necesarios para los algoritmos de planificación.
@dataclass
class Proceso:
    # Identificador único del proceso.
    id_proceso: int

    # Momento en que el proceso entra al sistema (tick de reloj).
    tiempo_llegada: int

    # Duración total de CPU que requiere el proceso.
    tiempo_rafaga: int

    # Nivel de prioridad del proceso (1 = más alta prioridad).
    prioridad: int

    # Nombre para mostrar en el diagrama de Gantt.
    nombre: str = ""

    # CPU restante por consumir; se decrementa en Round Robin.
    tiempo_restante: int = field(init=False)

    # Tick en que el proceso usó la CPU por primera vez.
    tiempo_inicio: Optional[int] = field(default=None, init=False)

    # Tick en que el proceso terminó su ejecución completamente.
    tiempo_finalizacion: int = field(default=0, init=False)

    def __post_init__(self):
        # Inicializar tiempo restante igual a la ráfaga y nombre si no se dio.
        self.tiempo_restante = self.tiempo_rafaga
        if not self.nombre:
            self.nombre = f"P{self.id_proceso}"

    # Crea una copia independiente del proceso con estado limpio.
    def clonar(self) -> "Proceso":
        return Proceso(
            id_proceso=self.id_proceso,
            tiempo_llegada=self.tiempo_llegada,
            tiempo_rafaga=self.tiempo_rafaga,
            prioridad=self.prioridad,
            nombre=self.nombre,
        )
