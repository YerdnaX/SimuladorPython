from typing import List
from modelos.proceso import Proceso
from modelos.segmento_ejecucion import SegmentoEjecucion
from planificadores.planificador_base import PlanificadorBase


# Algoritmo MLQ (Multi-Level Queue / Cola Multinivel).
# Divide los procesos en tres colas según su prioridad:
#   - Cola Alta   (prioridad 1-2): se atiende primero
#   - Cola Media  (prioridad 3):   se atiende segunda
#   - Cola Baja   (prioridad 4-5): se atiende última
# Cada cola puede usar un algoritmo distinto (FIFO, SJF o Round Robin).
# Los procesos de cola alta tienen prioridad absoluta sobre las demás colas.
class PlanificadorMLQ(PlanificadorBase):

    # Inicializa el MLQ con los tres planificadores de cola.
    def __init__(self, planificador_alta: PlanificadorBase,
                 planificador_media: PlanificadorBase,
                 planificador_baja: PlanificadorBase):
        self._planificador_alta = planificador_alta
        self._planificador_media = planificador_media
        self._planificador_baja = planificador_baja

    # Ejecuta el MLQ: procesa las tres colas en orden de prioridad (alta → media → baja).
    # Los tiempos de cada cola se encadenan respetando los tiempos de llegada reales.
    def ejecutar(self, procesos: List[Proceso]) -> List[SegmentoEjecucion]:
        segmentos_finales: List[SegmentoEjecucion] = []

        # Separar procesos en sus colas según prioridad
        cola_alta = [p for p in procesos if p.prioridad <= 2]
        cola_media = [p for p in procesos if p.prioridad == 3]
        cola_baja = [p for p in procesos if p.prioridad >= 4]

        # El tiempo inicial del sistema es el primer arribo global
        tiempo_actual = min(p.tiempo_llegada for p in procesos) if procesos else 0

        # ── Cola Alta ──────────────────────────────────────────────────
        if cola_alta:
            primer_llegada_alta = min(p.tiempo_llegada for p in cola_alta)
            if tiempo_actual < primer_llegada_alta:
                tiempo_actual = primer_llegada_alta

            seg_alta = self._planificador_alta.ejecutar(cola_alta)
            self._ajustar_tiempos(seg_alta, cola_alta, tiempo_actual)
            if seg_alta:
                tiempo_actual = max(s.fin for s in seg_alta)
            segmentos_finales.extend(seg_alta)

        # ── Cola Media ─────────────────────────────────────────────────
        if cola_media:
            primer_llegada_media = min(p.tiempo_llegada for p in cola_media)
            if tiempo_actual < primer_llegada_media:
                tiempo_actual = primer_llegada_media

            seg_media = self._planificador_media.ejecutar(cola_media)
            self._ajustar_tiempos(seg_media, cola_media, tiempo_actual)
            if seg_media:
                tiempo_actual = max(s.fin for s in seg_media)
            segmentos_finales.extend(seg_media)

        # ── Cola Baja ──────────────────────────────────────────────────
        if cola_baja:
            primer_llegada_baja = min(p.tiempo_llegada for p in cola_baja)
            if tiempo_actual < primer_llegada_baja:
                tiempo_actual = primer_llegada_baja

            seg_baja = self._planificador_baja.ejecutar(cola_baja)
            self._ajustar_tiempos(seg_baja, cola_baja, tiempo_actual)
            segmentos_finales.extend(seg_baja)

        return sorted(segmentos_finales, key=lambda s: s.inicio)

    # Reajusta los tiempos de inicio/fin de los segmentos de una cola
    # para que continúen a partir del tiempo actual del sistema,
    # respetando el tiempo de llegada real de cada proceso.
    def _ajustar_tiempos(self, segmentos: List[SegmentoEjecucion],
                         procesos_en_cola: List[Proceso],
                         tiempo_inicial: int) -> None:
        # Construir lookup de llegada real por nombre de proceso
        llegadas = {p.nombre: p.tiempo_llegada for p in procesos_en_cola}
        tiempo_actual = tiempo_inicial

        for seg in segmentos:
            duracion = seg.fin - seg.inicio

            # Respetar tiempo de llegada real del proceso
            llegada_real = llegadas.get(seg.nombre_proceso, 0)
            if tiempo_actual < llegada_real:
                tiempo_actual = llegada_real

            seg.inicio = tiempo_actual
            seg.fin = tiempo_actual + duracion
            seg.tiempo_llegada = llegada_real  # Preservar llegada real para el reporte
            tiempo_actual = seg.fin
