import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from modelos.proceso import Proceso
from modelos.cliente import Cliente
from planificadores.planificador_fifo import PlanificadorFIFO
from planificadores.planificador_sjf import PlanificadorSJF
from planificadores.planificador_round_robin import PlanificadorRoundRobin
from planificadores.planificador_mlq import PlanificadorMLQ


class PruebaMLQ(unittest.TestCase):

    # Crea el MLQ bancario estándar: Alta→RR(q=2), Media→FIFO, Baja→SJF.
    def _crear_mlq_bancario(self) -> PlanificadorMLQ:
        return PlanificadorMLQ(
            PlanificadorRoundRobin(2),
            PlanificadorFIFO(),
            PlanificadorSJF(),
        )

    # Verifica que la cola alta se procese antes que la cola baja.
    def test_prioridad_alta_antes_baja(self):
        procesos = [
            Proceso(1, 0, 3, 1),  # Alta (prioridad 1)
            Proceso(2, 0, 3, 4),  # Baja (prioridad 4)
        ]
        mlq = self._crear_mlq_bancario()
        segmentos = mlq.ejecutar([p.clonar() for p in procesos])

        # Los segmentos de P1 deben comenzar antes que los de P2
        segs_p1 = [s for s in segmentos if s.nombre_proceso == "P1"]
        segs_p2 = [s for s in segmentos if s.nombre_proceso == "P2"]
        self.assertLess(segs_p1[0].inicio, segs_p2[0].inicio)

    # Verifica que los procesos de prioridad 3 (media) se atienden entre alta y baja.
    def test_orden_colas(self):
        procesos = [
            Proceso(1, 0, 2, 1),  # Alta
            Proceso(2, 0, 2, 3),  # Media
            Proceso(3, 0, 2, 5),  # Baja
        ]
        mlq = self._crear_mlq_bancario()
        segmentos = mlq.ejecutar([p.clonar() for p in procesos])

        inicio_p1 = min(s.inicio for s in segmentos if s.nombre_proceso == "P1")
        inicio_p2 = min(s.inicio for s in segmentos if s.nombre_proceso == "P2")
        inicio_p3 = min(s.inicio for s in segmentos if s.nombre_proceso == "P3")

        self.assertLess(inicio_p1, inicio_p2)
        self.assertLess(inicio_p2, inicio_p3)

    # Verifica que todos los procesos reciben tiempo de CPU.
    def test_todos_los_procesos_ejecutados(self):
        procesos = [
            Proceso(1, 0, 3, 1),
            Proceso(2, 1, 3, 2),
            Proceso(3, 0, 3, 3),
            Proceso(4, 2, 3, 4),
            Proceso(5, 1, 3, 5),
        ]
        mlq = self._crear_mlq_bancario()
        segmentos = mlq.ejecutar([p.clonar() for p in procesos])
        nombres_ejecutados = set(s.nombre_proceso for s in segmentos)
        for p in procesos:
            self.assertIn(p.nombre, nombres_ejecutados)

    # Verifica el escenario de demostración equivalente al WinForms (clientes bancarios).
    def test_escenario_bancario_demo(self):
        clientes = [
            Cliente("Ana",    "VIP",         0),
            Cliente("Carlos", "ADULTOMAYOR", 1),
            Cliente("María",  "EMBARAZADA",  2),
            Cliente("Luis",   "REGULAR",     3),
            Cliente("Pedro",  "FORANEO",     4),
        ]

        procesos = []
        for idx, c in enumerate(sorted(clientes, key=lambda x: x.tiempo_llegada), start=1):
            procesos.append(Proceso(
                id_proceso=idx,
                tiempo_llegada=c.tiempo_llegada,
                tiempo_rafaga=c.obtener_tiempo_atencion(),
                prioridad=c.prioridad,
                nombre=c.nombre,
            ))

        mlq = self._crear_mlq_bancario()
        segmentos = mlq.ejecutar([p.clonar() for p in procesos])

        nombres = set(s.nombre_proceso for s in segmentos)
        self.assertIn("Ana", nombres)
        self.assertIn("Carlos", nombres)
        self.assertIn("María", nombres)
        self.assertIn("Luis", nombres)
        self.assertIn("Pedro", nombres)

    # Verifica que la suma de duraciones de segmentos iguala la ráfaga de cada proceso.
    def test_cobertura_total_rafagas(self):
        procesos = [
            Proceso(1, 0, 2, 1),
            Proceso(2, 0, 3, 3),
            Proceso(3, 0, 4, 5),
        ]
        mlq = self._crear_mlq_bancario()
        segmentos = mlq.ejecutar([p.clonar() for p in procesos])

        for p in procesos:
            segs_p = [s for s in segmentos if s.nombre_proceso == p.nombre]
            total_dur = sum(s.duracion for s in segs_p)
            self.assertEqual(total_dur, p.tiempo_rafaga,
                             f"{p.nombre}: duración total {total_dur} != ráfaga {p.tiempo_rafaga}")

    # Verifica que el MLQ respeta el tiempo de llegada real de los procesos.
    def test_respeta_tiempo_llegada(self):
        procesos = [
            Proceso(1, 10, 2, 1),  # Alta, llega tarde
        ]
        mlq = self._crear_mlq_bancario()
        segmentos = mlq.ejecutar([p.clonar() for p in procesos])
        self.assertGreaterEqual(segmentos[0].inicio, 10)


if __name__ == "__main__":
    unittest.main()
