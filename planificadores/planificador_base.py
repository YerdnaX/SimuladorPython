from abc import ABC, abstractmethod
from typing import List
from modelos.proceso import Proceso
from modelos.segmento_ejecucion import SegmentoEjecucion


# Interfaz común que deben implementar todos los algoritmos de planificación.
# Recibe una lista de procesos y devuelve la secuencia de ejecución como segmentos de Gantt.
class PlanificadorBase(ABC):

    # Ejecuta el algoritmo de planificación sobre los procesos dados.
    @abstractmethod
    def ejecutar(self, procesos: List[Proceso]) -> List[SegmentoEjecucion]:
        ...
