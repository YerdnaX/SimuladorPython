import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from modelos.paciente import Paciente
from planificadores.planificador_fifo import PlanificadorFIFO
from planificadores.planificador_sjf import PlanificadorSJF
from planificadores.planificador_round_robin import PlanificadorRoundRobin
from planificadores.planificador_emergencias import PlanificadorEmergencias


class PruebaMLQ(unittest.TestCase):

    @staticmethod
    def _resumen(segmentos):
        return " | ".join(f"{s.nombre_proceso}[{s.inicio}-{s.fin}]" for s in segmentos)

    # Crea el planificador de emergencias: Crítica→RR(q=2), Urgente→FIFO, Normal→SJF.
    def _crear_planificador_emergencias(self) -> PlanificadorEmergencias:
        return PlanificadorEmergencias(
            PlanificadorRoundRobin(2),
            PlanificadorFIFO(),
            PlanificadorSJF(),
        )

    @staticmethod
    def _a_procesos(pacientes):
        return [p.a_proceso(id_num=i) for i, p in enumerate(pacientes, start=1)]

    # Verifica que la cola alta se procese antes que la cola baja.
    def test_cola_critica_antes_que_normal(self):
        """En emergencias, cola crítica debe ejecutarse antes que cola normal."""
        pacientes = [
            Paciente("P001", "Luis Rojas", "ROJO", "Trauma", 0, 3),
            Paciente("P002", "Marta Diaz", "CITA", "Control", 0, 3),
        ]
        planificador = self._crear_planificador_emergencias()
        segmentos = planificador.ejecutar(self._a_procesos(pacientes))
        print(f"\n[Emergencias][Crítica antes que normal] {self._resumen(segmentos)}")

        segs_p1 = [s for s in segmentos if s.nombre_proceso == "P001"]
        segs_p2 = [s for s in segmentos if s.nombre_proceso == "P002"]
        self.assertLess(segs_p1[0].inicio, segs_p2[0].inicio)

    # Verifica que los procesos de prioridad 3 (media) se atienden entre alta y baja.
    def test_orden_colas(self):
        """Orden global esperado: crítica, luego urgente, luego normal."""
        pacientes = [
            Paciente("P101", "Carlos Vega", "AMARILLO", "Dolor intenso", 0, 2),
            Paciente("P102", "Ana Torres", "EMBARAZADA", "Control urgente", 0, 2),
            Paciente("P103", "Pedro Gil", "SEGUIMIENTO", "Revision", 0, 2),
        ]
        planificador = self._crear_planificador_emergencias()
        segmentos = planificador.ejecutar(self._a_procesos(pacientes))
        print(f"\n[Emergencias][Orden de colas] {self._resumen(segmentos)}")

        inicio_p1 = min(s.inicio for s in segmentos if s.nombre_proceso == "P101")
        inicio_p2 = min(s.inicio for s in segmentos if s.nombre_proceso == "P102")
        inicio_p3 = min(s.inicio for s in segmentos if s.nombre_proceso == "P103")

        self.assertLess(inicio_p1, inicio_p2)
        self.assertLess(inicio_p2, inicio_p3)

    # Verifica que todos los procesos reciben tiempo de CPU.
    def test_todos_los_pacientes_atendidos(self):
        """Todos los pacientes cargados deben aparecer al menos una vez en la ejecución."""
        pacientes = [
            Paciente("P201", "Rocio Marin", "ROJO", "Accidente", 0, 3),
            Paciente("P202", "Saul Perez", "AMARILLO", "Fractura", 1, 3),
            Paciente("P203", "Diana Nunez", "EMBARAZADA", "Contracciones", 0, 3),
            Paciente("P204", "Ivan Soto", "VERDE", "Fiebre", 2, 3),
            Paciente("P205", "Mia Ortiz", "CITA", "Consulta", 1, 3),
        ]
        planificador = self._crear_planificador_emergencias()
        segmentos = planificador.ejecutar(self._a_procesos(pacientes))
        print(f"\n[Emergencias][Cobertura de pacientes] {self._resumen(segmentos)}")
        nombres_ejecutados = set(s.nombre_proceso for s in segmentos)
        for p in pacientes:
            self.assertIn(p.id_paciente, nombres_ejecutados, f"No se atendio {p.id_paciente}")

    # Verifica escenario representativo del panel de emergencias.
    def test_escenario_emergencias_demo(self):
        """Escenario de guardia: mezcla de triages y llegadas progresivas."""
        pacientes = [
            Paciente("P301", "Lorena Rios", "ROJO", "Politrauma", 0, 5),
            Paciente("P302", "Nicolas Ruiz", "AMARILLO", "Dolor abdominal", 1, 3),
            Paciente("P303", "Sara Leon", "EMBARAZADA", "Contracciones", 2, 4),
            Paciente("P304", "Juan Pardo", "VERDE", "Herida leve", 3, 2),
            Paciente("P305", "Elena Mora", "SEGUIMIENTO", "Control", 4, 2),
        ]

        planificador = self._crear_planificador_emergencias()
        segmentos = planificador.ejecutar(self._a_procesos(pacientes))
        print(f"\n[Emergencias][Demo guardia] {self._resumen(segmentos)}")

        nombres = set(s.nombre_proceso for s in segmentos)
        self.assertIn("P301", nombres)
        self.assertIn("P302", nombres)
        self.assertIn("P303", nombres)
        self.assertIn("P304", nombres)
        self.assertIn("P305", nombres)

    # Verifica que la suma de duraciones de segmentos iguala la ráfaga de cada proceso.
    def test_cobertura_total_rafagas(self):
        """La atención total por paciente debe cubrir exactamente su tiempo de ráfaga."""
        pacientes = [
            Paciente("P401", "Andres Mena", "ROJO", "Crisis", 0, 2),
            Paciente("P402", "Paula Roldan", "EMBARAZADA", "Revision", 0, 3),
            Paciente("P403", "Oscar Luna", "CITA", "Control", 0, 4),
        ]
        procesos = self._a_procesos(pacientes)
        planificador = self._crear_planificador_emergencias()
        segmentos = planificador.ejecutar([p.clonar() for p in procesos])
        print(f"\n[Emergencias][Cobertura de ráfaga] {self._resumen(segmentos)}")

        for p in procesos:
            segs_p = [s for s in segmentos if s.nombre_proceso == p.nombre]
            total_dur = sum(s.duracion for s in segs_p)
            self.assertEqual(total_dur, p.tiempo_rafaga,
                             f"{p.nombre}: duración total {total_dur} != ráfaga {p.tiempo_rafaga}")

    # Verifica que el MLQ respeta el tiempo de llegada real de los procesos.
    def test_respeta_tiempo_llegada(self):
        """El planificador no debe atender pacientes antes de su hora de ingreso."""
        pacientes = [
            Paciente("P501", "Mateo Paz", "ROJO", "Trauma", 10, 2),
        ]
        planificador = self._crear_planificador_emergencias()
        segmentos = planificador.ejecutar(self._a_procesos(pacientes))
        print(f"\n[Emergencias][Llegada real] {self._resumen(segmentos)}")
        self.assertGreaterEqual(segmentos[0].inicio, 10, "No puede iniciar atención antes de t=10")


if __name__ == "__main__":
    unittest.main(verbosity=2)
