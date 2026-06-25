# Representa un cliente bancario con su tipo, prioridad y tiempo de llegada.
# Se usa en el Sistema de Tickets para mapear a un Proceso del planificador.
class Cliente:
    # Mapeo fijo de tipos de cliente a prioridad para el MLQ.
    # Cola Alta (1-2): VIP, ADULTOMAYOR
    # Cola Media (3): EMBARAZADA
    # Cola Baja (4-5): REGULAR, FORANEO
    TIPOS_VALIDOS = ["VIP", "ADULTOMAYOR", "EMBARAZADA", "REGULAR", "FORANEO"]

    TIEMPOS_ATENCION = {
        "VIP": 2,
        "ADULTOMAYOR": 3,
        "EMBARAZADA": 3,
        "REGULAR": 4,
        "FORANEO": 5,
    }

    # Inicializa el cliente y calcula su prioridad automáticamente según el tipo.
    def __init__(self, nombre: str, tipo: str, tiempo_llegada: int):
        self.nombre = nombre
        self.tipo = tipo.upper().strip()
        self.tiempo_llegada = tiempo_llegada
        self.prioridad = self._obtener_prioridad(self.tipo)

    # Asigna prioridad única a cada tipo de cliente para el MLQ.
    def _obtener_prioridad(self, tipo: str) -> int:
        prioridades = {
            "VIP": 1,
            "ADULTOMAYOR": 2,
            "EMBARAZADA": 3,
            "REGULAR": 4,
            "FORANEO": 5,
        }
        return prioridades.get(tipo, 4)

    # Devuelve el tiempo de atención estándar en minutos según el tipo de cliente.
    def obtener_tiempo_atencion(self) -> int:
        return self.TIEMPOS_ATENCION.get(self.tipo, 4)

    def __repr__(self) -> str:
        return f"Cliente({self.nombre}, {self.tipo}, llegada={self.tiempo_llegada}, prioridad={self.prioridad})"
