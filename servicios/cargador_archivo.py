from typing import List, Tuple
from modelos.proceso import Proceso


# Lee procesos desde un archivo de texto con formato CSV.
# Cada línea representa un proceso con los campos: ID, TiempoLlegada, TiempoRafaga, Prioridad
# Ejemplo de línea: 1,0,5,2
# Las líneas vacías o mal formadas se omiten y se reporta el error.
def cargar_procesos_desde_archivo(ruta: str) -> Tuple[List[Proceso], List[str]]:
    procesos: List[Proceso] = []
    advertencias: List[str] = []

    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            lineas = archivo.readlines()
    except FileNotFoundError:
        return [], [f"No se encontró el archivo: {ruta}"]
    except OSError as error:
        return [], [f"Error al leer el archivo: {error}"]

    numero_linea = 0
    for linea in lineas:
        numero_linea += 1
        linea = linea.strip()

        # Omitir líneas vacías o comentarios (#)
        if not linea or linea.startswith("#"):
            continue

        datos = linea.split(",")

        # Validar que la línea tenga exactamente 4 campos
        if len(datos) < 4:
            advertencias.append(f"Línea {numero_linea} ignorada (formato incorrecto): \"{linea}\"")
            continue

        try:
            id_proceso = int(datos[0].strip())
            tiempo_llegada = int(datos[1].strip())
            tiempo_rafaga = int(datos[2].strip())
            prioridad = int(datos[3].strip())
        except ValueError:
            advertencias.append(f"Línea {numero_linea} ignorada (valores no numéricos): \"{linea}\"")
            continue

        # Validar valores mínimos lógicos
        if tiempo_rafaga <= 0:
            advertencias.append(f"Línea {numero_linea}: ráfaga debe ser > 0. Proceso ignorado.")
            continue

        if tiempo_llegada < 0:
            advertencias.append(f"Línea {numero_linea}: tiempo de llegada debe ser >= 0. Proceso ignorado.")
            continue

        procesos.append(Proceso(
            id_proceso=id_proceso,
            tiempo_llegada=tiempo_llegada,
            tiempo_rafaga=tiempo_rafaga,
            prioridad=prioridad,
        ))

    return procesos, advertencias
