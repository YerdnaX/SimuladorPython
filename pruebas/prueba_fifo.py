import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from modelos.proceso import Proceso
from planificadores.planificador_fifo import PlanificadorFIFO


class PruebaFIFO(unittest.TestCase):

    # Verifica que FIFO ordene los segmentos por tiempo de llegada.
    def test_orden_llegada(self):
        procesos = [
            Proceso(1, 0, 5, 1),
            Proceso(2, 2, 3, 1),
            Proceso(3, 4, 2, 1),
        ]
        planificador = PlanificadorFIFO()
        segmentos = planificador.ejecutar(procesos)
        self.assertEqual(len(segmentos), 3)
        self.assertEqual(segmentos[0].nombre_proceso, "P1")
        self.assertEqual(segmentos[1].nombre_proceso, "P2")
        self.assertEqual(segmentos[2].nombre_proceso, "P3")

    # Verifica que los tiempos de inicio y fin sean correctos para FIFO sin huecos.
    def test_tiempos_sin_huecos(self):
        procesos = [
            Proceso(1, 0, 5, 1),
            Proceso(2, 2, 3, 1),
        ]
        planificador = PlanificadorFIFO()
        segmentos = planificador.ejecutar(procesos)
        self.assertEqual(segmentos[0].inicio, 0)
        self.assertEqual(segmentos[0].fin, 5)
        self.assertEqual(segmentos[1].inicio, 5)
        self.assertEqual(segmentos[1].fin, 8)

    # Verifica que FIFO adelante el reloj si hay hueco entre procesos.
    def test_hueco_entre_procesos(self):
        procesos = [
            Proceso(1, 0, 3, 1),
            Proceso(2, 8, 2, 1),
        ]
        planificador = PlanificadorFIFO()
        segmentos = planificador.ejecutar(procesos)
        # P1 termina en t=3, P2 llega en t=8: debe empezar en t=8
        self.assertEqual(segmentos[1].inicio, 8)
        self.assertEqual(segmentos[1].fin, 10)

    # Verifica el tiempo de finalización que actualiza el proceso.
    def test_tiempo_finalizacion_proceso(self):
        p1 = Proceso(1, 0, 5, 1)
        p2 = Proceso(2, 2, 3, 1)
        planificador = PlanificadorFIFO()
        planificador.ejecutar([p1, p2])
        self.assertEqual(p1.tiempo_finalizacion, 5)
        self.assertEqual(p2.tiempo_finalizacion, 8)

    # Verifica que FIFO con un solo proceso produce un único segmento correcto.
    def test_un_proceso(self):
        procesos = [Proceso(1, 3, 7, 1)]
        segmentos = PlanificadorFIFO().ejecutar(procesos)
        self.assertEqual(len(segmentos), 1)
        self.assertEqual(segmentos[0].inicio, 3)
        self.assertEqual(segmentos[0].fin, 10)

    # Verifica el cálculo de espera y retorno para FIFO con los datos de demostración.
    def test_estadisticas_demo(self):
        procesos = [
            Proceso(1, 0, 5, 1),
            Proceso(2, 2, 3, 2),
            Proceso(3, 4, 8, 1),
            Proceso(4, 6, 2, 3),
            Proceso(5, 8, 4, 2),
        ]
        segmentos = PlanificadorFIFO().ejecutar(procesos)
        # El último proceso termina en t=0+5+3+8+2+4=22
        self.assertEqual(max(s.fin for s in segmentos), 22)


if __name__ == "__main__":
    unittest.main()
