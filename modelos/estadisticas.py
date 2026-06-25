from typing import List
from modelos.proceso import Proceso
from modelos.segmento_ejecucion import SegmentoEjecucion


# Calcula el tiempo promedio de espera de una lista de procesos.
# Fórmula: espera_i = (fin_i - llegada_i) - ráfaga_i
def calcular_tiempo_promedio_espera(procesos: List[Proceso]) -> float:
    if not procesos:
        return 0.0
    total = sum(
        (p.tiempo_finalizacion - p.tiempo_llegada - p.tiempo_rafaga)
        for p in procesos
    )
    return total / len(procesos)


# Calcula el tiempo promedio de retorno (turnaround) de una lista de procesos.
# Fórmula: retorno_i = fin_i - llegada_i
def calcular_tiempo_promedio_retorno(procesos: List[Proceso]) -> float:
    if not procesos:
        return 0.0
    total = sum(
        (p.tiempo_finalizacion - p.tiempo_llegada)
        for p in procesos
    )
    return total / len(procesos)


# Suma total de ráfagas = tiempo productivo de CPU.
def calcular_tiempo_total_cpu(procesos: List[Proceso]) -> int:
    return sum(p.tiempo_rafaga for p in procesos)


# Porcentaje de tiempo que la CPU estuvo ocupada respecto al tiempo total del sistema.
def calcular_utilizacion_cpu(procesos: List[Proceso]) -> float:
    if not procesos:
        return 0.0
    tiempo_cpu = calcular_tiempo_total_cpu(procesos)
    tiempo_inicial = min(p.tiempo_llegada for p in procesos)
    tiempo_final = max(p.tiempo_finalizacion for p in procesos)
    tiempo_sistema = tiempo_final - tiempo_inicial
    if tiempo_sistema == 0:
        return 0.0
    return (tiempo_cpu / tiempo_sistema) * 100.0


# Calcula las estadísticas agrupadas desde segmentos de ejecución.
# Retorna una lista de dicts con: nombre, llegada, fin, rafaga, espera, retorno.
def calcular_estadisticas_desde_segmentos(segmentos: List[SegmentoEjecucion]) -> List[dict]:
    if not segmentos:
        return []

    grupos: dict = {}
    for seg in segmentos:
        nombre = seg.nombre_proceso
        if nombre not in grupos:
            grupos[nombre] = {
                "nombre": nombre,
                "llegada": seg.tiempo_llegada,
                "fin": seg.fin,
                "rafaga": seg.duracion,
            }
        else:
            grupos[nombre]["fin"] = max(grupos[nombre]["fin"], seg.fin)
            grupos[nombre]["rafaga"] += seg.duracion

    resultado = []
    for datos in grupos.values():
        espera = max(0, (datos["fin"] - datos["llegada"]) - datos["rafaga"])
        retorno = datos["fin"] - datos["llegada"]
        resultado.append({
            "nombre": datos["nombre"],
            "llegada": datos["llegada"],
            "fin": datos["fin"],
            "rafaga": datos["rafaga"],
            "espera": espera,
            "retorno": retorno,
        })
    return resultado


# Calcula el resumen global (promedio espera, retorno, uso CPU) desde segmentos.
def calcular_resumen_global(segmentos: List[SegmentoEjecucion]) -> dict:
    estadisticas = calcular_estadisticas_desde_segmentos(segmentos)
    if not estadisticas:
        return {"promedio_espera": 0.0, "promedio_retorno": 0.0, "uso_cpu": 0.0}

    n = len(estadisticas)
    total_espera = sum(e["espera"] for e in estadisticas)
    total_retorno = sum(e["retorno"] for e in estadisticas)

    tiempo_cpu = sum(seg.duracion for seg in segmentos)
    tiempo_llegada_min = min(seg.tiempo_llegada for seg in segmentos)
    tiempo_fin_max = max(seg.fin for seg in segmentos)
    tiempo_sistema = tiempo_fin_max - tiempo_llegada_min
    uso_cpu = (tiempo_cpu / tiempo_sistema * 100.0) if tiempo_sistema > 0 else 0.0

    return {
        "promedio_espera": total_espera / n,
        "promedio_retorno": total_retorno / n,
        "uso_cpu": uso_cpu,
        "tiempo_total_cpu": tiempo_cpu,
        "tiempo_sistema": tiempo_sistema,
    }
