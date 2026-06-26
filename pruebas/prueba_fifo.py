import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from modelos.proceso import Proceso
from planificadores.planificador_fifo import PlanificadorFIFO


class PruebaFIFO(unittest.TestCase):

    @staticmethod
    def _resumen(segmentos):
        return " | ".join(f"{s.nombre_proceso}[{s.inicio}-{s.fin}]" for s in segmentos)

    # Verifica que FIFO ordene los segmentos por tiempo de llegada.
    def test_orden_llegada(self):
        """FIFO en triage debe respetar el orden de llegada de pacientes."""
        procesos = [
            Proceso(1, 0, 5, 3, "PAC-ROJO-01"),
            Proceso(2, 2, 3, 4, "PAC-VERDE-02"),
            Proceso(3, 4, 2, 5, "PAC-CITA-03"),
        ]
        planificador = PlanificadorFIFO()
        segmentos = planificador.ejecutar(procesos)
        print(f"\n[FIFO][Orden llegada] {self._resumen(segmentos)}")
        self.assertEqual(len(segmentos), 3)
        self.assertEqual(segmentos[0].nombre_proceso, "PAC-ROJO-01")
        self.assertEqual(segmentos[1].nombre_proceso, "PAC-VERDE-02")
        self.assertEqual(segmentos[2].nombre_proceso, "PAC-CITA-03")

    # Verifica que los tiempos de inicio y fin sean correctos para FIFO sin huecos.
    def test_tiempos_sin_huecos(self):
        """FIFO debe encadenar atenciones cuando siempre hay pacientes disponibles."""
        procesos = [
            Proceso(1, 0, 5, 2, "PAC-AMARILLO-01"),
            Proceso(2, 2, 3, 3, "PAC-EMBARAZADA-02"),
        ]
        planificador = PlanificadorFIFO()
        segmentos = planificador.ejecutar(procesos)
        print(f"\n[FIFO][Sin huecos] {self._resumen(segmentos)}")
        self.assertEqual(segmentos[0].inicio, 0, "El primer paciente debe iniciar en t=0")
        self.assertEqual(segmentos[0].fin, 5, "El primer paciente debe finalizar en t=5")
        self.assertEqual(segmentos[1].inicio, 5, "El segundo paciente debe iniciar justo tras el primero")
        self.assertEqual(segmentos[1].fin, 8, "El segundo paciente debe finalizar en t=8")

    # Verifica que FIFO adelante el reloj si hay hueco entre procesos.
    def test_hueco_entre_procesos(self):
        """FIFO debe esperar al siguiente paciente cuando la sala queda vacía."""
        procesos = [
            Proceso(1, 0, 3, 2, "PAC-CRITICO-01"),
            Proceso(2, 8, 2, 4, "PAC-VERDE-02"),
        ]
        planificador = PlanificadorFIFO()
        segmentos = planificador.ejecutar(procesos)
        print(f"\n[FIFO][Con hueco] {self._resumen(segmentos)}")
        # P1 termina en t=3, P2 llega en t=8: debe empezar en t=8
        self.assertEqual(segmentos[1].inicio, 8, "Debe existir espera hasta que llegue el segundo paciente")
        self.assertEqual(segmentos[1].fin, 10, "El segundo paciente debe terminar en t=10")

    # Verifica el tiempo de finalización que actualiza el proceso.
    def test_tiempo_finalizacion_proceso(self):
        """FIFO debe actualizar correctamente el tiempo final de cada paciente."""
        p1 = Proceso(1, 0, 5, 1, "PAC-ROJO-01")
        p2 = Proceso(2, 2, 3, 3, "PAC-EMBARAZADA-02")
        planificador = PlanificadorFIFO()
        segmentos = planificador.ejecutar([p1, p2])
        print(f"\n[FIFO][Finalización] {self._resumen(segmentos)}")
        self.assertEqual(p1.tiempo_finalizacion, 5, "Paciente crítico debe terminar en t=5")
        self.assertEqual(p2.tiempo_finalizacion, 8, "Segundo paciente debe terminar en t=8")

    # Verifica que FIFO con un solo proceso produce un único segmento correcto.
    def test_un_proceso(self):
        """Con un solo paciente, FIFO debe generar una única atención continua."""
        procesos = [Proceso(1, 3, 7, 2, "PAC-AMARILLO-UNICO")]
        segmentos = PlanificadorFIFO().ejecutar(procesos)
        print(f"\n[FIFO][Paciente único] {self._resumen(segmentos)}")
        self.assertEqual(len(segmentos), 1)
        self.assertEqual(segmentos[0].inicio, 3)
        self.assertEqual(segmentos[0].fin, 10)

    # Verifica el cálculo de espera y retorno para FIFO con los datos de demostración.
    def test_estadisticas_demo(self):
        """Escenario de guardia: validar que la línea de tiempo total sea consistente."""
        procesos = [
            Proceso(1, 0, 5, 1, "PAC-ROJO-01"),
            Proceso(2, 2, 3, 2, "PAC-AMARILLO-02"),
            Proceso(3, 4, 8, 3, "PAC-EMBARAZADA-03"),
            Proceso(4, 6, 2, 4, "PAC-VERDE-04"),
            Proceso(5, 8, 4, 5, "PAC-CITA-05"),
        ]
        segmentos = PlanificadorFIFO().ejecutar(procesos)
        print(f"\n[FIFO][Guardia completa] {self._resumen(segmentos)}")
        # El último proceso termina en t=0+5+3+8+2+4=22
        self.assertEqual(max(s.fin for s in segmentos), 22, "La guardia completa debe finalizar en t=22")


if __name__ == "__main__":
    unittest.main(verbosity=2)
