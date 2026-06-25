"""
Cargador de pacientes desde archivo TXT.

Formato esperado (primera línea puede ser cabecera o comentario con #):
    ID,NOMBRE,TIPO,MOTIVO,LLEGADA,RAFAGA
    P001,Ana Solano,ROJO,Accidente de tránsito,0,8
    P002,Carlos Mora,VERDE,Herida leve,1,4
    P003,María Vargas,EMBARAZADA,Parto,2,6

Reglas:
  - Las líneas vacías y las que empiezan con '#' se ignoran.
  - El tipo se valida contra: ROJO AMARILLO EMBARAZADA VERDE CITA SEGUIMIENTO
  - LLEGADA y RAFAGA deben ser enteros >= 0 y >= 1 respectivamente.
  - Si una línea tiene error se reporta como advertencia y se omite.
"""

from typing import Tuple, List
from modelos.paciente import Paciente, TIPOS_VALIDOS


def cargar_pacientes_desde_archivo(ruta: str) -> Tuple[List[Paciente], List[str]]:
    """
    Lee el archivo TXT y retorna (pacientes_válidos, lista_de_advertencias).
    """
    pacientes: List[Paciente] = []
    advertencias: List[str] = []

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            lineas = f.readlines()
    except (IOError, OSError) as e:
        return [], [f"No se pudo abrir el archivo: {e}"]

    ids_vistos: set[str] = set()

    for num_linea, linea in enumerate(lineas, start=1):
        linea = linea.strip()

        # Ignorar líneas vacías, comentarios y cabecera
        if not linea or linea.startswith("#"):
            continue
        if linea.upper().startswith("ID"):
            continue

        partes = [p.strip() for p in linea.split(",")]

        if len(partes) < 6:
            advertencias.append(
                f"Línea {num_linea}: se esperaban 6 campos (ID,NOMBRE,TIPO,MOTIVO,LLEGADA,RAFAGA), "
                f"se encontraron {len(partes)}. Línea omitida."
            )
            continue

        id_pac, nombre, tipo, motivo, llegada_str, rafaga_str = partes[:6]

        # Validar ID
        if not id_pac:
            advertencias.append(f"Línea {num_linea}: ID vacío. Línea omitida.")
            continue
        if id_pac in ids_vistos:
            advertencias.append(f"Línea {num_linea}: ID duplicado '{id_pac}'. Línea omitida.")
            continue

        # Validar nombre
        if not nombre:
            advertencias.append(f"Línea {num_linea}: nombre vacío. Línea omitida.")
            continue

        # Validar tipo
        tipo_up = tipo.upper()
        if tipo_up not in TIPOS_VALIDOS:
            advertencias.append(
                f"Línea {num_linea}: tipo '{tipo}' inválido. "
                f"Válidos: {', '.join(TIPOS_VALIDOS)}. Línea omitida."
            )
            continue

        # Validar tiempos
        try:
            llegada = int(llegada_str)
            if llegada < 0:
                raise ValueError("negativo")
        except ValueError:
            advertencias.append(
                f"Línea {num_linea}: LLEGADA '{llegada_str}' inválida (debe ser entero >= 0). "
                f"Línea omitida."
            )
            continue

        try:
            rafaga = int(rafaga_str)
            if rafaga <= 0:
                raise ValueError("debe ser > 0")
        except ValueError:
            advertencias.append(
                f"Línea {num_linea}: RAFAGA '{rafaga_str}' inválida (debe ser entero > 0). "
                f"Línea omitida."
            )
            continue

        ids_vistos.add(id_pac)
        pacientes.append(Paciente(
            id_paciente=id_pac,
            nombre=nombre,
            tipo=tipo_up,
            motivo=motivo if motivo else "No especificado",
            tiempo_llegada=llegada,
            tiempo_rafaga=rafaga,
        ))

    if not pacientes and not advertencias:
        advertencias.append("El archivo no contiene pacientes válidos.")

    return pacientes, advertencias
