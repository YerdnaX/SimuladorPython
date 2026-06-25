import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from modelos.proceso import Proceso
from planificadores.planificador_round_robin import PlanificadorRoundRobin


class PruebaRoundRobin(unittest.TestCase):

    # Verifica que Round Robin genera múltiples segmentos para procesos que superan el quantum.
    def test_multiples_segmentos(self):
        procesos = [
            Proceso(1, 0, 5, 1),
            Proceso(2, 0, 3, 1),
        ]
        rr = PlanificadorRoundRobin(2)
        segmentos = rr.ejecutar(procesos)
        # P1 tiene ráfaga=5 y quantum=2 → al menos 2 segmentos para P1
        nombres_p1 = [s for s in segmentos if s.nombre_proceso == "P1"]
        self.assertGreaterEqual(len(nombres_p1), 2)

    # Verifica que el quantum sea respetado en cada turno.
    def test_duracion_quantum(self):
        procesos = [
            Proceso(1, 0, 6, 1),
            Proceso(2, 0, 4, 1),
        ]
        quantum = 3
        rr = PlanificadorRoundRobin(quantum)
        segmentos = rr.ejecutar(procesos)
        for seg in segmentos:
            self.assertLessEqual(seg.duracion, quantum)

    # Verifica que Round Robin con quantum >= ráfaga produce un único segmento por proceso.
    def test_quantum_mayor_que_rafaga(self):
        procesos = [
            Proceso(1, 0, 3, 1),
            Proceso(2, 0, 2, 1),
        ]
        rr = PlanificadorRoundRobin(10)
        segmentos = rr.ejecutar(procesos)
        self.assertEqual(len(segmentos), 2)

    # Verifica que el tiempo de finalización sea correcto con datos simples.
    def test_tiempo_finalizacion(self):
        p1 = Proceso(1, 0, 4, 1)
        p2 = Proceso(2, 0, 4, 1)
        rr = PlanificadorRoundRobin(2)
        rr.ejecutar([p1, p2])
        # P1: t=0-2, P2: t=2-4, P1: t=4-6, P2: t=6-8
        self.assertEqual(p1.tiempo_finalizacion, 6)
        self.assertEqual(p2.tiempo_finalizacion, 8)

    # Verifica que Round Robin encola los procesos que llegan durante la ejecución.
    def test_llegada_durante_ejecucion(self):
        procesos = [
            Proceso(1, 0, 4, 1),
            Proceso(2, 3, 2, 1),  # llega durante la ejecución de P1
        ]
        rr = PlanificadorRoundRobin(2)
        segmentos = rr.ejecutar(procesos)
        nombres = [s.nombre_proceso for s in segmentos]
        # P2 debe aparecer en los segmentos
        self.assertIn("P2", nombres)

    # Verifica el quantum mínimo de 1 cuando se pasa 0 o negativo.
    def test_quantum_minimo(self):
        rr = PlanificadorRoundRobin(0)
        self.assertEqual(rr.quantum, 1)

        rr2 = PlanificadorRoundRobin(-5)
        self.assertEqual(rr2.quantum, 1)

    # Verifica que la suma de duraciones de segmentos iguala la ráfaga total.
    def test_suma_duraciones_igual_rafaga(self):
        procesos = [
            Proceso(1, 0, 5, 1),
            Proceso(2, 1, 3, 1),
            Proceso(3, 2, 7, 1),
        ]
        rr = PlanificadorRoundRobin(2)
        segmentos = rr.ejecutar([p.clonar() for p in procesos])

        for p in procesos:
            segs_p = [s for s in segmentos if s.nombre_proceso == p.nombre]
            total_dur = sum(s.duracion for s in segs_p)
            self.assertEqual(total_dur, p.tiempo_rafaga)


if __name__ == "__main__":
    unittest.main()
