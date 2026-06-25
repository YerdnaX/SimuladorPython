# Simulador de Planificación de Procesos del SO

Migración completa del proyecto original C# WinForms a una aplicación de escritorio Python con PySide6.

## Descripción

Aplicación de escritorio que simula algoritmos de planificación de procesos de sistemas operativos, modelando un centro de atención de emergencias / sistema bancario con colas de prioridad múltiple.

Incluye tres módulos:

- **Simulador**: configura y ejecuta FIFO, SJF, Round Robin o MLQ sobre procesos manuales o cargados desde archivo.
- **Comparación**: ejecuta los tres algoritmos base (FIFO, SJF, Round Robin) sobre los mismos procesos y compara sus métricas.
- **Sistema Bancario**: simula la atención de clientes bancarios con el algoritmo MLQ según su tipo (VIP, ADULTO MAYOR, EMBARAZADA, REGULAR, FORÁNEO).

## Requisitos previos

- Python 3.12 o superior
- pip

## Instalación de dependencias

```bash
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
python main.py
```

## Estructura de carpetas

```
SimuladorAlgoritmosPython/
├── main.py                          # Punto de entrada
├── requirements.txt                 # Dependencias (PySide6)
├── modelos/
│   ├── proceso.py                   # Modelo de proceso del SO
│   ├── cliente.py                   # Modelo de cliente bancario
│   ├── segmento_ejecucion.py        # Bloque de ejecución del Gantt
│   └── estadisticas.py              # Funciones de cálculo de estadísticas
├── planificadores/
│   ├── planificador_base.py         # Interfaz abstracta
│   ├── planificador_fifo.py         # Algoritmo FIFO/FCFS
│   ├── planificador_sjf.py          # Algoritmo SJF
│   ├── planificador_round_robin.py  # Algoritmo Round Robin
│   └── planificador_mlq.py          # Algoritmo MLQ (cola multinivel)
├── servicios/
│   ├── cargador_archivo.py          # Lectura de procesos desde .txt
│   ├── comparador_algoritmos.py     # Comparación automática de algoritmos
│   └── gestor_archivos.py           # Persistencia JSON de clientes atendidos
├── interfaz/
│   ├── tema.py                      # Colores, fuentes y estilos CSS
│   ├── controles_personalizados.py  # Widgets reutilizables del tema oscuro
│   ├── dialogo_proceso.py           # Diálogo para agregar un proceso
│   ├── dialogo_cliente.py           # Diálogo para registrar un cliente
│   ├── vista_gantt.py               # Widget del diagrama de Gantt
│   └── ventana_principal.py         # Ventana principal con 3 paneles
├── datos/
│   └── pacientes_finalizados.json   # Historial de clientes atendidos
└── pruebas/
    ├── prueba_fifo.py
    ├── prueba_sjf.py
    ├── prueba_round_robin.py
    └── prueba_mlq.py
```

## Algoritmos implementados

### FIFO (First In, First Out)
Los procesos se atienden en estricto orden de llegada. No expropiativo.
- Fácil de implementar y entender.
- No es óptimo en tiempo de espera promedio.

### SJF (Shortest Job First)
Selecciona siempre el proceso con menor ráfaga disponible. No expropiativo.
- Minimiza el tiempo promedio de espera entre algoritmos no-expropiativos.
- Puede producir inanición en procesos de larga duración.

### Round Robin
Asigna un quantum fijo de CPU a cada proceso en forma cíclica. Expropiativo.
- Equitativo: ningún proceso monopoliza la CPU.
- El quantum configurable afecta el rendimiento: muy pequeño aumenta el overhead, muy grande se acerca a FIFO.

### MLQ (Multi-Level Queue)
Divide los procesos en tres colas de prioridad (Alta, Media, Baja). Cada cola usa su propio algoritmo.
- Cola Alta (prioridad 1–2): Round Robin (q=2) — VIP y Adulto Mayor
- Cola Media (prioridad 3): FIFO — Embarazadas
- Cola Baja (prioridad 4–5): SJF — Regular y Foráneo
- Los procesos de cola alta tienen prioridad absoluta sobre las demás.

## Formato del archivo de procesos (.txt)

Cada línea: `ID,TiempoLlegada,TiempoRafaga,Prioridad`

```
# Ejemplo de archivo de procesos
1,0,5,1
2,2,3,2
3,4,8,1
4,6,2,3
```

## Archivo de pacientes finalizados

Ubicación: `datos/pacientes_finalizados.json`

Se actualiza automáticamente cada vez que se ejecuta el Sistema Bancario. Contiene el historial completo de todos los clientes atendidos con sus tiempos de espera, retorno y fecha de atención.

## Ejemplos de uso

1. **Simulación básica**: ingrese procesos en la tabla, seleccione FIFO, presione ▶ Ejecutar.
2. **Carga desde archivo**: presione 📂 Archivo y seleccione un `.txt` con el formato indicado.
3. **Round Robin**: seleccione Round Robin, configure el Quantum y presione ▶ Ejecutar.
4. **MLQ personalizado**: seleccione MLQ y configure el algoritmo de cada cola.
5. **Comparación**: en el módulo Comparación presione 🔄 Comparar.
6. **Sistema Bancario**: registre clientes con su tipo y tiempo de llegada, presione ▶ Ejecutar MLQ Bancario.

## Ejecutar pruebas

```bash
python -m pytest pruebas/ -v
```

O individualmente:

```bash
python pruebas/prueba_fifo.py
python pruebas/prueba_sjf.py
python pruebas/prueba_round_robin.py
python pruebas/prueba_mlq.py
```
