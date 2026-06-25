from typing import List
from modelos.proceso import Proceso
from modelos.segmento_ejecucion import SegmentoEjecucion
from planificadores.planificador_base import PlanificadorBase


# Algoritmo SJF (Shortest Job First).
# En cada momento en que la CPU queda libre, selecciona el proceso disponible
# con la ráfaga más corta. Es no-expropiativo.
# Minimiza el tiempo promedio de espera entre los algoritmos no-expropiativos.
class PlanificadorSJF(PlanificadorBase):

    # Ejecuta la planificación SJF.
    # En cada paso selecciona el proceso de menor ráfaga entre los ya llegados.
    # Si no hay procesos disponibles, avanza el reloj hasta que llegue uno.
    def ejecutar(self, procesos: List[Proceso]) -> List[SegmentoEjecucion]:
        tiempo_actual = 0
        pendientes = list(procesos)
        segmentos: List[SegmentoEjecucion] = []

        while pendientes:
            # Filtrar los procesos que ya llegaron y ordenar por ráfaga más corta
            disponibles = sorted(
                [p for p in pendientes if p.tiempo_llegada <= tiempo_actual],
                key=lambda p: p.tiempo_rafaga,
            )

            # Si ningún proceso ha llegado aún, avanzar el reloj hasta el próximo
            if not disponibles:
                tiempo_actual = min(p.tiempo_llegada for p in pendientes)
                continue

            # Seleccionar el proceso con menor ráfaga
            proceso = disponibles[0]

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

            pendientes.remove(proceso)

        return segmentos
