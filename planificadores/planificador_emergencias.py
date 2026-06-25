from typing import List
from modelos.proceso import Proceso
from modelos.segmento_ejecucion import SegmentoEjecucion
from planificadores.planificador_base import PlanificadorBase


class PlanificadorEmergencias(PlanificadorBase):
    """
    MLQ adaptado al Centro de Emergencias con tres colas de prioridad:

        Cola CRÍTICA  (prioridad 1-2): ROJO, AMARILLO       — se atiende primero
        Cola URGENTE  (prioridad 3-4): EMBARAZADA, VERDE     — se atiende segundo
        Cola NORMAL   (prioridad 5-6): CITA, SEGUIMIENTO     — se atiende última

    Cada cola puede usar FIFO, SJF o Round Robin de forma independiente.
    Las colas de mayor prioridad se procesan antes que las de menor prioridad.
    """

    def __init__(self, planificador_critica: PlanificadorBase,
                 planificador_urgente: PlanificadorBase,
                 planificador_normal: PlanificadorBase):
        self._planificador_critica = planificador_critica
        self._planificador_urgente = planificador_urgente
        self._planificador_normal  = planificador_normal

    def ejecutar(self, procesos: List[Proceso]) -> List[SegmentoEjecucion]:
        if not procesos:
            return []

        segmentos_finales: List[SegmentoEjecucion] = []

        cola_critica = [p for p in procesos if p.prioridad <= 2]
        cola_urgente = [p for p in procesos if 3 <= p.prioridad <= 4]
        cola_normal  = [p for p in procesos if p.prioridad >= 5]

        tiempo_actual = min(p.tiempo_llegada for p in procesos)

        # ── Cola Crítica ──────────────────────────────────────────────────────
        if cola_critica:
            primer_llegada = min(p.tiempo_llegada for p in cola_critica)
            tiempo_actual = max(tiempo_actual, primer_llegada)

            seg_critica = self._planificador_critica.ejecutar(cola_critica)
            self._ajustar_tiempos(seg_critica, cola_critica, tiempo_actual)
            if seg_critica:
                tiempo_actual = max(s.fin for s in seg_critica)
            segmentos_finales.extend(seg_critica)

        # ── Cola Urgente ──────────────────────────────────────────────────────
        if cola_urgente:
            primer_llegada = min(p.tiempo_llegada for p in cola_urgente)
            tiempo_actual = max(tiempo_actual, primer_llegada)

            seg_urgente = self._planificador_urgente.ejecutar(cola_urgente)
            self._ajustar_tiempos(seg_urgente, cola_urgente, tiempo_actual)
            if seg_urgente:
                tiempo_actual = max(s.fin for s in seg_urgente)
            segmentos_finales.extend(seg_urgente)

        # ── Cola Normal ───────────────────────────────────────────────────────
        if cola_normal:
            primer_llegada = min(p.tiempo_llegada for p in cola_normal)
            tiempo_actual = max(tiempo_actual, primer_llegada)

            seg_normal = self._planificador_normal.ejecutar(cola_normal)
            self._ajustar_tiempos(seg_normal, cola_normal, tiempo_actual)
            segmentos_finales.extend(seg_normal)

        return sorted(segmentos_finales, key=lambda s: s.inicio)

    def _ajustar_tiempos(self, segmentos: List[SegmentoEjecucion],
                         procesos: List[Proceso],
                         tiempo_inicial: int) -> None:
        llegadas = {p.nombre: p.tiempo_llegada for p in procesos}
        tiempo_actual = tiempo_inicial

        for seg in segmentos:
            duracion = seg.fin - seg.inicio
            llegada_real = llegadas.get(seg.nombre_proceso, 0)
            if tiempo_actual < llegada_real:
                tiempo_actual = llegada_real
            seg.inicio = tiempo_actual
            seg.fin = tiempo_actual + duracion
            seg.tiempo_llegada = llegada_real
            tiempo_actual = seg.fin
