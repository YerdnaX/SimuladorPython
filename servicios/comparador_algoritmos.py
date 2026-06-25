from typing import List
from modelos.proceso import Proceso
from modelos.estadisticas import calcular_estadisticas_desde_segmentos, calcular_resumen_global
from planificadores.planificador_fifo import PlanificadorFIFO
from planificadores.planificador_sjf import PlanificadorSJF
from planificadores.planificador_round_robin import PlanificadorRoundRobin


# Compara el rendimiento de los tres algoritmos principales (FIFO, SJF, Round Robin)
# sobre el mismo conjunto de procesos y retorna una tabla comparativa.
def comparar_algoritmos(procesos_originales: List[Proceso], quantum: int = 2) -> List[dict]:
    algoritmos = [
        ("FIFO", PlanificadorFIFO()),
        ("SJF", PlanificadorSJF()),
        (f"Round Robin (q={quantum})", PlanificadorRoundRobin(quantum)),
    ]

    resultados = []
    for nombre, planificador in algoritmos:
        # Clonar procesos para que cada algoritmo parta del estado original
        copias = [p.clonar() for p in procesos_originales]
        segmentos = planificador.ejecutar(copias)
        resumen = calcular_resumen_global(segmentos)

        resultados.append({
            "algoritmo": nombre,
            "promedio_espera": resumen["promedio_espera"],
            "promedio_retorno": resumen["promedio_retorno"],
            "uso_cpu": resumen["uso_cpu"],
        })

    return resultados
