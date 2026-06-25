import json
import os
from datetime import datetime
from typing import List
from modelos.cliente import Cliente


# Ruta predeterminada del archivo de persistencia de clientes atendidos.
RUTA_PACIENTES = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "datos",
    "pacientes_finalizados.json",
)


# Guarda los clientes atendidos en el archivo JSON local de persistencia.
# Agrega los nuevos registros a los existentes sin borrar el historial anterior.
def guardar_clientes_atendidos(clientes: List[Cliente], segmentos_info: List[dict]) -> bool:
    try:
        registros_existentes = cargar_historial_clientes()

        nuevos_registros = []
        ahora = datetime.now().isoformat(timespec="seconds")

        for cliente in clientes:
            info = next((s for s in segmentos_info if s.get("nombre") == cliente.nombre), {})
            nuevos_registros.append({
                "nombre": cliente.nombre,
                "tipo": cliente.tipo,
                "prioridad": cliente.prioridad,
                "tiempo_llegada": cliente.tiempo_llegada,
                "tiempo_finalizacion": info.get("fin", 0),
                "tiempo_espera": info.get("espera", 0),
                "tiempo_retorno": info.get("retorno", 0),
                "fecha_atencion": ahora,
            })

        registros_existentes.extend(nuevos_registros)

        os.makedirs(os.path.dirname(RUTA_PACIENTES), exist_ok=True)
        with open(RUTA_PACIENTES, "w", encoding="utf-8") as archivo:
            json.dump(registros_existentes, archivo, ensure_ascii=False, indent=2)

        return True
    except OSError:
        return False


# Carga el historial completo de clientes atendidos desde el archivo JSON.
def cargar_historial_clientes() -> List[dict]:
    if not os.path.exists(RUTA_PACIENTES):
        return []
    try:
        with open(RUTA_PACIENTES, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except (json.JSONDecodeError, OSError):
        return []


# Limpia el historial de clientes atendidos eliminando el archivo JSON.
def limpiar_historial_clientes() -> bool:
    try:
        if os.path.exists(RUTA_PACIENTES):
            os.remove(RUTA_PACIENTES)
        return True
    except OSError:
        return False
