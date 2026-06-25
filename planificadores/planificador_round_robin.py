from collections import deque
from typing import List
from modelos.proceso import Proceso
from modelos.segmento_ejecucion import SegmentoEjecucion
from planificadores.planificador_base import PlanificadorBase


# Algoritmo Round Robin (RR).
# Asigna a cada proceso un quantum fijo de CPU de forma cíclica.
# Si el proceso no termina en ese quantum, regresa al final de la cola.
# Es expropiativo: garantiza equidad entre todos los procesos.
class PlanificadorRoundRobin(PlanificadorBase):

    # Inicializa Round Robin con el quantum especificado.
    def __init__(self, quantum: int):
        self.quantum = max(1, quantum)

    # Ejecuta la planificación Round Robin.
    # Mantiene una cola de listos y rota los procesos según el quantum.
    # Los nuevos procesos que lleguen durante la ejecución se encolan al final.
    def ejecutar(self, procesos: List[Proceso]) -> List[SegmentoEjecucion]:
        segmentos: List[SegmentoEjecucion] = []
        cola: deque = deque()
        tiempo_actual = 0

        # Ordenar procesos por tiempo de llegada para encolarlos en orden
        procesos_ordenados = sorted(procesos, key=lambda p: p.tiempo_llegada)
        indice = 0

        # Encolar los procesos que ya están disponibles en t=0
        while indice < len(procesos_ordenados) and procesos_ordenados[indice].tiempo_llegada <= tiempo_actual:
            cola.append(procesos_ordenados[indice])
            indice += 1

        while cola or indice < len(procesos_ordenados):
            # Si la cola está vacía, avanzar el reloj al próximo proceso
            if not cola:
                tiempo_actual = procesos_ordenados[indice].tiempo_llegada
                while indice < len(procesos_ordenados) and procesos_ordenados[indice].tiempo_llegada <= tiempo_actual:
                    cola.append(procesos_ordenados[indice])
                    indice += 1
                continue

            proceso = cola.popleft()

            # Registrar el primer instante de uso de CPU
            if proceso.tiempo_inicio is None:
                proceso.tiempo_inicio = tiempo_actual

            # Ejecutar por quantum o lo que quede
            tiempo_ejecucion = min(self.quantum, proceso.tiempo_restante)
            inicio = tiempo_actual
            tiempo_actual += tiempo_ejecucion
            proceso.tiempo_restante -= tiempo_ejecucion

            # Registrar el segmento ejecutado
            segmentos.append(SegmentoEjecucion(
                nombre_proceso=proceso.nombre,
                inicio=inicio,
                fin=tiempo_actual,
                tiempo_llegada=proceso.tiempo_llegada,
            ))

            # Encolar los procesos que llegaron durante este quantum
            while indice < len(procesos_ordenados) and procesos_ordenados[indice].tiempo_llegada <= tiempo_actual:
                cola.append(procesos_ordenados[indice])
                indice += 1

            if proceso.tiempo_restante > 0:
                # El proceso no terminó: vuelve al final de la cola
                cola.append(proceso)
            else:
                # Proceso completado: registrar tiempo de finalización
                proceso.tiempo_finalizacion = tiempo_actual

        return segmentos
