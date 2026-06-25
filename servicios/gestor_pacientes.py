import json
import os
from datetime import datetime
from typing import List

from modelos.paciente import Paciente, COLA_POR_TIPO

_RUTA_HISTORIAL = os.path.join(
    os.path.dirname(__file__), "..", "datos", "historial_emergencias.json"
)


def guardar_pacientes_atendidos(pacientes: List[Paciente],
                                estadisticas: list,
                                algoritmos_usados: dict[str, str] | None = None) -> None:
    """Persiste los pacientes finalizados en el historial JSON."""
    ruta = os.path.abspath(_RUTA_HISTORIAL)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    historial = _cargar_json(ruta)

    mapa_est = {e["nombre"]: e for e in estadisticas}
    algoritmos_usados = algoritmos_usados or {}
    ahora = datetime.now().isoformat()

    for paciente in pacientes:
        est = mapa_est.get(paciente.id_paciente, {})
        registro = {
            "id_paciente":       paciente.id_paciente,
            "numero_tiquete":    paciente.numero_tiquete,
            "nombre":            paciente.nombre,
            "tipo":              paciente.tipo,
            "cola":              COLA_POR_TIPO.get(paciente.tipo, "NORMAL"),
            "motivo":            paciente.motivo,
            "identificacion":    paciente.identificacion,
            "edad":              paciente.edad,
            "telefono":          paciente.telefono,
            "tiempo_llegada":    paciente.tiempo_llegada,
            "tiempo_rafaga":     paciente.tiempo_rafaga,
            "prioridad":         paciente.prioridad,
            "estado":            "FINALIZADO",
            "tiempo_inicio":     est.get("inicio", -1),
            "tiempo_finalizacion": est.get("fin", -1),
            "tiempo_espera":     est.get("espera", 0),
            "tiempo_retorno":    est.get("retorno", 0),
            "algoritmo_usado":   algoritmos_usados.get(paciente.tipo, "—"),
            "fecha_atencion":    ahora,
        }
        historial.append(registro)

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


def cargar_historial() -> List[dict]:
    """Carga todos los registros del historial de pacientes atendidos."""
    ruta = os.path.abspath(_RUTA_HISTORIAL)
    return _cargar_json(ruta)


def limpiar_historial() -> None:
    """Elimina todos los registros del historial."""
    ruta = os.path.abspath(_RUTA_HISTORIAL)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump([], f)


def _cargar_json(ruta: str) -> list:
    if not os.path.exists(ruta):
        return []
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
            return datos if isinstance(datos, list) else []
    except (json.JSONDecodeError, IOError):
        return []
