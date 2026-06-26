import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from modelos.proceso import Proceso
from planificadores.planificador_sjf import PlanificadorSJF


class PruebaSJF(unittest.TestCase):

    @staticmethod
    def _resumen(segmentos):
        return " | ".join(f"{s.nombre_proceso}[{s.inicio}-{s.fin}]" for s in segmentos)

    # Verifica que SJF seleccione primero el proceso con menor ráfaga.
    def test_seleccion_menor_rafaga(self):
        """SJF en emergencias debe priorizar atenciones cortas entre disponibles."""
        procesos = [
            Proceso(1, 0, 8, 2, "PAC-AMARILLO-COMPLEJO"),
            Proceso(2, 1, 4, 4, "PAC-VERDE-MODERADO"),
            Proceso(3, 2, 2, 5, "PAC-CITA-RAPIDA"),
        ]
        planificador = PlanificadorSJF()
        segmentos = planificador.ejecutar(procesos)
        print(f"\n[SJF][Selección ráfaga] {self._resumen(segmentos)}")
        # t=0: solo P1 disponible → P1 primero
        # Luego P3 (ráfaga=2) antes que P2 (ráfaga=4)
        self.assertEqual(segmentos[0].nombre_proceso, "PAC-AMARILLO-COMPLEJO")
        # Después de P1 termina en t=8, P2 y P3 disponibles → P3 (ráfaga=2)
        self.assertEqual(segmentos[1].nombre_proceso, "PAC-CITA-RAPIDA")
        self.assertEqual(segmentos[2].nombre_proceso, "PAC-VERDE-MODERADO")

    # Verifica que SJF produce el tiempo de finalización correcto.
    def test_tiempos_correctos(self):
        """SJF debe producir tiempos de finalización esperados en un lote de triaje."""
        procesos = [
            Proceso(1, 0, 6, 3, "PAC-EMBARAZADA-LARGO"),
            Proceso(2, 0, 3, 4, "PAC-VERDE-MEDIO"),
            Proceso(3, 0, 1, 5, "PAC-CITA-CORTO"),
        ]
        segmentos = PlanificadorSJF().ejecutar(procesos)
        print(f"\n[SJF][Tiempos] {self._resumen(segmentos)}")
        # P3(1), P2(3), P1(6) → fins: 1, 4, 10
        fins = [s.fin for s in segmentos]
        self.assertEqual(fins, [1, 4, 10], "SJF debe cerrar en la secuencia de tiempos [1, 4, 10]")

    # Verifica que SJF adelanta el reloj cuando no hay procesos disponibles.
    def test_avance_reloj_sin_procesos(self):
        """SJF debe esperar hasta que llegue el primer paciente si el sistema inicia vacío."""
        procesos = [
            Proceso(1, 5, 3, 2, "PAC-AMARILLO-TARDIO"),
        ]
        segmentos = PlanificadorSJF().ejecutar(procesos)
        print(f"\n[SJF][Arribo tardío] {self._resumen(segmentos)}")
        self.assertEqual(segmentos[0].inicio, 5, "La atención no debe comenzar antes de la llegada")
        self.assertEqual(segmentos[0].fin, 8, "El paciente debe finalizar en t=8")

    # Verifica los tiempos de finalización de procesos en SJF.
    def test_finalizacion_procesos(self):
        """SJF debe reflejar correctamente la finalización por menor tiempo restante total."""
        p1 = Proceso(1, 0, 3, 3, "PAC-EMBARAZADA")
        p2 = Proceso(2, 0, 1, 4, "PAC-VERDE")
        segmentos = PlanificadorSJF().ejecutar([p1, p2])
        print(f"\n[SJF][Finalización] {self._resumen(segmentos)}")
        self.assertEqual(p2.tiempo_finalizacion, 1, "El paciente con atención más corta debe salir primero")
        self.assertEqual(p1.tiempo_finalizacion, 4, "El segundo paciente debe finalizar en t=4")

    # Verifica que SJF minimiza la espera promedio respecto a FIFO en un caso estándar.
    def test_mejor_que_fifo(self):
        """SJF debe igualar o mejorar la espera promedio frente a FIFO en la misma guardia."""
        from planificadores.planificador_fifo import PlanificadorFIFO
        from modelos.estadisticas import calcular_resumen_global

        procesos_base = [
            Proceso(1, 0, 8, 2, "PAC-AMARILLO-LARGO"),
            Proceso(2, 1, 4, 4, "PAC-VERDE-MEDIO"),
            Proceso(3, 2, 2, 5, "PAC-CITA-CORTO"),
        ]

        segs_fifo = PlanificadorFIFO().ejecutar([p.clonar() for p in procesos_base])
        segs_sjf = PlanificadorSJF().ejecutar([p.clonar() for p in procesos_base])

        espera_fifo = calcular_resumen_global(segs_fifo)["promedio_espera"]
        espera_sjf = calcular_resumen_global(segs_sjf)["promedio_espera"]

        print(f"\n[SJF vs FIFO] espera_promedio_sjf={espera_sjf:.2f} | espera_promedio_fifo={espera_fifo:.2f}")

        self.assertLessEqual(espera_sjf, espera_fifo, "SJF no debería empeorar la espera promedio en este caso")


if __name__ == "__main__":
    unittest.main(verbosity=2)
