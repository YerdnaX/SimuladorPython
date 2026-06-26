import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from modelos.proceso import Proceso
from planificadores.planificador_round_robin import PlanificadorRoundRobin


class PruebaRoundRobin(unittest.TestCase):

    @staticmethod
    def _resumen(segmentos):
        return " | ".join(f"{s.nombre_proceso}[{s.inicio}-{s.fin}]" for s in segmentos)

    # Verifica que Round Robin genera múltiples segmentos para procesos que superan el quantum.
    def test_multiples_segmentos(self):
        """Round Robin debe alternar turnos cuando un paciente supera el quantum."""
        procesos = [
            Proceso(1, 0, 5, 1, "PAC-ROJO-ESTABILIZACION"),
            Proceso(2, 0, 3, 2, "PAC-AMARILLO-OBSERVACION"),
        ]
        rr = PlanificadorRoundRobin(2)
        segmentos = rr.ejecutar(procesos)
        print(f"\n[RR][Múltiples segmentos] {self._resumen(segmentos)}")
        # P1 tiene ráfaga=5 y quantum=2 → al menos 2 segmentos para P1
        nombres_p1 = [s for s in segmentos if s.nombre_proceso == "PAC-ROJO-ESTABILIZACION"]
        self.assertGreaterEqual(len(nombres_p1), 2, "Paciente largo debe dividirse en varios turnos")

    # Verifica que el quantum sea respetado en cada turno.
    def test_duracion_quantum(self):
        """Ningún turno de RR debe exceder el quantum configurado."""
        procesos = [
            Proceso(1, 0, 6, 2, "PAC-AMARILLO-A"),
            Proceso(2, 0, 4, 3, "PAC-EMBARAZADA-B"),
        ]
        quantum = 3
        rr = PlanificadorRoundRobin(quantum)
        segmentos = rr.ejecutar(procesos)
        print(f"\n[RR][Quantum={quantum}] {self._resumen(segmentos)}")
        for seg in segmentos:
            self.assertLessEqual(seg.duracion, quantum, f"Turno inválido de {seg.nombre_proceso}: {seg.duracion}")

    # Verifica que Round Robin con quantum >= ráfaga produce un único segmento por proceso.
    def test_quantum_mayor_que_rafaga(self):
        """Con quantum amplio, cada paciente debe completarse en un solo turno."""
        procesos = [
            Proceso(1, 0, 3, 4, "PAC-VERDE-01"),
            Proceso(2, 0, 2, 5, "PAC-CITA-02"),
        ]
        rr = PlanificadorRoundRobin(10)
        segmentos = rr.ejecutar(procesos)
        print(f"\n[RR][Quantum amplio] {self._resumen(segmentos)}")
        self.assertEqual(len(segmentos), 2, "Cada paciente debería aparecer una sola vez")

    # Verifica que el tiempo de finalización sea correcto con datos simples.
    def test_tiempo_finalizacion(self):
        """RR debe actualizar tiempos finales correctamente en alternancia simétrica."""
        p1 = Proceso(1, 0, 4, 1, "PAC-ROJO-01")
        p2 = Proceso(2, 0, 4, 2, "PAC-AMARILLO-02")
        rr = PlanificadorRoundRobin(2)
        segmentos = rr.ejecutar([p1, p2])
        print(f"\n[RR][Finalización] {self._resumen(segmentos)}")
        # P1: t=0-2, P2: t=2-4, P1: t=4-6, P2: t=6-8
        self.assertEqual(p1.tiempo_finalizacion, 6, "Primer paciente debe finalizar en t=6")
        self.assertEqual(p2.tiempo_finalizacion, 8, "Segundo paciente debe finalizar en t=8")

    # Verifica que Round Robin encola los procesos que llegan durante la ejecución.
    def test_llegada_durante_ejecucion(self):
        """RR debe incorporar pacientes que arriban mientras otro está siendo atendido."""
        procesos = [
            Proceso(1, 0, 4, 1, "PAC-ROJO-INICIAL"),
            Proceso(2, 3, 2, 3, "PAC-EMBARAZADA-TARDIO"),  # llega durante la ejecución de P1
        ]
        rr = PlanificadorRoundRobin(2)
        segmentos = rr.ejecutar(procesos)
        print(f"\n[RR][Llegada dinámica] {self._resumen(segmentos)}")
        nombres = [s.nombre_proceso for s in segmentos]
        # P2 debe aparecer en los segmentos
        self.assertIn("PAC-EMBARAZADA-TARDIO", nombres, "Paciente tardío debe ser atendido por RR")

    # Verifica el quantum mínimo de 1 cuando se pasa 0 o negativo.
    def test_quantum_minimo(self):
        """RR debe protegerse con quantum mínimo de 1 ante entradas inválidas."""
        rr = PlanificadorRoundRobin(0)
        self.assertEqual(rr.quantum, 1)

        rr2 = PlanificadorRoundRobin(-5)
        self.assertEqual(rr2.quantum, 1)

    # Verifica que la suma de duraciones de segmentos iguala la ráfaga total.
    def test_suma_duraciones_igual_rafaga(self):
        """La suma de turnos por paciente debe coincidir con su tiempo de atención total."""
        procesos = [
            Proceso(1, 0, 5, 1, "PAC-ROJO-01"),
            Proceso(2, 1, 3, 4, "PAC-VERDE-02"),
            Proceso(3, 2, 7, 5, "PAC-CITA-03"),
        ]
        rr = PlanificadorRoundRobin(2)
        segmentos = rr.ejecutar([p.clonar() for p in procesos])
        print(f"\n[RR][Cobertura de ráfaga] {self._resumen(segmentos)}")

        for p in procesos:
            segs_p = [s for s in segmentos if s.nombre_proceso == p.nombre]
            total_dur = sum(s.duracion for s in segs_p)
            self.assertEqual(total_dur, p.tiempo_rafaga, f"{p.nombre}: duracion acumulada incorrecta")


if __name__ == "__main__":
    unittest.main(verbosity=2)
