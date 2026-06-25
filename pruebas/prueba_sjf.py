import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from modelos.proceso import Proceso
from planificadores.planificador_sjf import PlanificadorSJF


class PruebaSJF(unittest.TestCase):

    # Verifica que SJF seleccione primero el proceso con menor ráfaga.
    def test_seleccion_menor_rafaga(self):
        procesos = [
            Proceso(1, 0, 8, 1),
            Proceso(2, 1, 4, 1),
            Proceso(3, 2, 2, 1),
        ]
        planificador = PlanificadorSJF()
        segmentos = planificador.ejecutar(procesos)
        # t=0: solo P1 disponible → P1 primero
        # Luego P3 (ráfaga=2) antes que P2 (ráfaga=4)
        self.assertEqual(segmentos[0].nombre_proceso, "P1")
        # Después de P1 termina en t=8, P2 y P3 disponibles → P3 (ráfaga=2)
        self.assertEqual(segmentos[1].nombre_proceso, "P3")
        self.assertEqual(segmentos[2].nombre_proceso, "P2")

    # Verifica que SJF produce el tiempo de finalización correcto.
    def test_tiempos_correctos(self):
        procesos = [
            Proceso(1, 0, 6, 1),
            Proceso(2, 0, 3, 1),
            Proceso(3, 0, 1, 1),
        ]
        segmentos = PlanificadorSJF().ejecutar(procesos)
        # P3(1), P2(3), P1(6) → fins: 1, 4, 10
        fins = [s.fin for s in segmentos]
        self.assertEqual(fins, [1, 4, 10])

    # Verifica que SJF adelanta el reloj cuando no hay procesos disponibles.
    def test_avance_reloj_sin_procesos(self):
        procesos = [
            Proceso(1, 5, 3, 1),
        ]
        segmentos = PlanificadorSJF().ejecutar(procesos)
        self.assertEqual(segmentos[0].inicio, 5)
        self.assertEqual(segmentos[0].fin, 8)

    # Verifica los tiempos de finalización de procesos en SJF.
    def test_finalizacion_procesos(self):
        p1 = Proceso(1, 0, 3, 1)
        p2 = Proceso(2, 0, 1, 1)
        PlanificadorSJF().ejecutar([p1, p2])
        self.assertEqual(p2.tiempo_finalizacion, 1)  # P2 se ejecuta primero (ráfaga=1)
        self.assertEqual(p1.tiempo_finalizacion, 4)  # P1 se ejecuta después

    # Verifica que SJF minimiza la espera promedio respecto a FIFO en un caso estándar.
    def test_mejor_que_fifo(self):
        from planificadores.planificador_fifo import PlanificadorFIFO
        from modelos.estadisticas import calcular_resumen_global

        procesos_base = [
            Proceso(1, 0, 8, 1),
            Proceso(2, 1, 4, 1),
            Proceso(3, 2, 2, 1),
        ]

        segs_fifo = PlanificadorFIFO().ejecutar([p.clonar() for p in procesos_base])
        segs_sjf = PlanificadorSJF().ejecutar([p.clonar() for p in procesos_base])

        espera_fifo = calcular_resumen_global(segs_fifo)["promedio_espera"]
        espera_sjf = calcular_resumen_global(segs_sjf)["promedio_espera"]

        self.assertLessEqual(espera_sjf, espera_fifo)


if __name__ == "__main__":
    unittest.main()
