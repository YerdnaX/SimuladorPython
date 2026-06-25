from dataclasses import dataclass, field
from typing import Optional

# ── Constantes del dominio médico ─────────────────────────────────────────────
TIPOS_VALIDOS = ["ROJO", "AMARILLO", "EMBARAZADA", "VERDE", "CITA", "SEGUIMIENTO"]

# Prioridad interna para el planificador MLQ:
#   1-2 → Cola Crítica (ROJO, AMARILLO)
#   3-4 → Cola Urgente (EMBARAZADA, VERDE)
#   5-6 → Cola Normal  (CITA, SEGUIMIENTO)
PRIORIDAD_SCHEDULER: dict[str, int] = {
    "ROJO":        1,
    "AMARILLO":    2,
    "EMBARAZADA":  3,
    "VERDE":       4,
    "CITA":        5,
    "SEGUIMIENTO": 6,
}

COLA_POR_TIPO: dict[str, str] = {
    "ROJO":        "CRÍTICA",
    "AMARILLO":    "CRÍTICA",
    "EMBARAZADA":  "URGENTE",
    "VERDE":       "URGENTE",
    "CITA":        "NORMAL",
    "SEGUIMIENTO": "NORMAL",
}

ETIQUETA_PRIORIDAD: dict[str, str] = {
    "ROJO":        "1 — Crítica",
    "AMARILLO":    "2 — Alta",
    "EMBARAZADA":  "3 — Alta",
    "VERDE":       "4 — Media",
    "CITA":        "5 — Baja",
    "SEGUIMIENTO": "6 — Muy baja",
}

# Tiempos de ráfaga por defecto (unidades de tiempo de atención) — solo para referencia
RAFAGA_DEFAULT: dict[str, int] = {
    "ROJO":        8,
    "AMARILLO":    6,
    "EMBARAZADA":  6,
    "VERDE":       4,
    "CITA":        3,
    "SEGUIMIENTO": 2,
}


@dataclass
class Paciente:
    id_paciente: str          # P001, P002, ...
    nombre: str               # Nombre completo del paciente
    tipo: str                 # ROJO | AMARILLO | EMBARAZADA | VERDE | CITA | SEGUIMIENTO
    motivo: str               # Motivo de atención
    tiempo_llegada: int       # Tick en que el paciente ingresa al sistema
    tiempo_rafaga: int        # Duración total de atención requerida
    identificacion: str = ""  # Cédula o número de identificación
    edad: int = 0
    telefono: str = ""
    numero_tiquete: str = ""  # T-0001 — se genera automáticamente
    estado: str = "EN_ESPERA" # EN_ESPERA | EN_ATENCION | FINALIZADO | CANCELADO
    prioridad: int = 0        # Se calcula desde el tipo si no se indica
    tiempo_restante: int = 0  # CPU pendiente (relevante en Round Robin)
    tiempo_inicio: int = -1
    tiempo_finalizacion: int = -1
    tiempo_espera: int = 0
    tiempo_retorno: int = 0

    def __post_init__(self):
        self.tipo = self.tipo.upper()
        if self.prioridad == 0:
            self.prioridad = PRIORIDAD_SCHEDULER.get(self.tipo, 6)
        if self.tiempo_restante == 0:
            self.tiempo_restante = self.tiempo_rafaga
        if not self.numero_tiquete:
            num = "".join(c for c in self.id_paciente if c.isdigit()).zfill(4)
            self.numero_tiquete = f"T-{num}"

    @property
    def nombre_corto(self) -> str:
        partes = self.nombre.split()
        if not partes:
            return self.id_paciente
        if len(partes) >= 2:
            return f"{partes[0]} {partes[1][0]}."
        return partes[0]

    def obtener_cola(self) -> str:
        return COLA_POR_TIPO.get(self.tipo, "NORMAL")

    def clonar(self) -> "Paciente":
        from copy import deepcopy
        return deepcopy(self)

    def a_proceso(self, id_num: int = 0):
        """Convierte el paciente a Proceso para reutilizar los planificadores existentes."""
        from modelos.proceso import Proceso
        return Proceso(
            id_proceso=id_num,
            tiempo_llegada=self.tiempo_llegada,
            tiempo_rafaga=self.tiempo_rafaga,
            prioridad=self.prioridad,
            nombre=self.id_paciente,  # ID del paciente como etiqueta en el Gantt
        )
