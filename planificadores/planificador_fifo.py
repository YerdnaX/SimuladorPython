from typing import List
from modelos.proceso import Proceso
from modelos.segmento_ejecucion import SegmentoEjecucion
from planificadores.planificador_base import PlanificadorBase


# Algoritmo FIFO (First In, First Out) / FCFS (First Come, First Served).
# Los procesos se atienden en estricto orden de llegada.
# Es no-expropiativo: una vez que un proceso toma la CPU, la retiene hasta terminar.
class PlanificadorFIFO(PlanificadorBase):

    # Ejecuta la planificación FIFO.
    # Ordena los procesos por tiempo de llegada y los ejecuta de forma consecutiva.
    # Si la CPU está libre antes de que llegue el siguiente proceso, avanza el reloj.
    def ejecutar(self, procesos: List[Proceso]) -> List[SegmentoEjecucion]:
        tiempo_actual = 0
        segmentos: List[SegmentoEjecucion] = []

        # Ordenar por tiempo de llegada (orden FIFO)
        for proceso in sorted(procesos, key=lambda p: p.tiempo_llegada):
            # Si la CPU está ociosa, avanzar al momento de llegada del siguiente proceso
            if tiempo_actual < proceso.tiempo_llegada:
                tiempo_actual = proceso.tiempo_llegada

            # Registrar el primer instante en que el proceso usó la CPU
            if proceso.tiempo_inicio is None:
                proceso.tiempo_inicio = tiempo_actual

            inicio = tiempo_actual
            tiempo_actual += proceso.tiempo_rafaga  # Ejecutar completamente (no expropiativo)
            proceso.tiempo_finalizacion = tiempo_actual

            segmentos.append(SegmentoEjecucion(
                nombre_proceso=proceso.nombre,
                inicio=inicio,
                fin=tiempo_actual,
                tiempo_llegada=proceso.tiempo_llegada,
            ))

        return segmentos
