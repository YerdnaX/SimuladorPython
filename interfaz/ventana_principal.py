from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QComboBox, QSpinBox, QFrame,
    QScrollArea, QFileDialog, QMessageBox, QTableWidgetItem,
    QStackedWidget, QSizePolicy, QProgressBar,
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QColor, QFont

from interfaz.tema import (
    COLOR_FONDO_PRIMARIO, COLOR_FONDO_SECUNDARIO, COLOR_SUPERFICIE,
    COLOR_SUPERFICIE_ELEV, COLOR_BORDE, COLOR_ACENTO, COLOR_ACENTO_BRILLANTE,
    COLOR_ACENTO_CYAN, COLOR_TEXTO_PRIMARIO, COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_MUTED, COLOR_EXITO, COLOR_EXITO_OSCURO, COLOR_PELIGRO,
    COLOR_PELIGRO_OSCURO, COLOR_ADVERTENCIA, COLOR_PURPURA, COLOR_PURPURA_OSCURO,
    COLORES_PROCESOS, fuente_h1, fuente_h2, fuente_base, fuente_pequena,
    fuente_seccion, fuente_mono_grande, fuente_mono, css_boton, a_css, aclarar,
)
from interfaz.controles_personalizados import (
    TarjetaTema, ItemNavegacion, crear_boton, crear_tabla,
    agregar_fila_tabla, crear_etiqueta_campo, crear_spinbox, crear_combo,
)
from interfaz.vista_gantt import VistaGantt
from interfaz.dialogo_proceso import DialogoProceso
from interfaz.dialogo_cliente import DialogoCliente

from modelos.proceso import Proceso
from modelos.cliente import Cliente
from modelos.segmento_ejecucion import SegmentoEjecucion
from modelos.estadisticas import calcular_estadisticas_desde_segmentos, calcular_resumen_global

from planificadores.planificador_fifo import PlanificadorFIFO
from planificadores.planificador_sjf import PlanificadorSJF
from planificadores.planificador_round_robin import PlanificadorRoundRobin
from planificadores.planificador_mlq import PlanificadorMLQ
from planificadores.planificador_base import PlanificadorBase

from servicios.cargador_archivo import cargar_procesos_desde_archivo
from servicios.comparador_algoritmos import comparar_algoritmos
from servicios.gestor_archivos import guardar_clientes_atendidos


class VentanaPrincipal(QMainWindow):

    def __init__(self):
        super().__init__()
        self._procesos_actuales: List[Proceso] = []
        self._segmentos_actuales: List[SegmentoEjecucion] = []
        self._simulacion_en_curso = False
        self._timer_animacion = QTimer()
        self._timer_animacion.timeout.connect(self._tick_animacion)
        self._segmentos_pendientes: List[SegmentoEjecucion] = []
        self._tick_actual = 0
        self._tick_total = 0
        self._mapa_colores: Dict[str, QColor] = {}

        self._construir_ventana()
        self._cargar_datos_demostracion()

    # ─────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ─────────────────────────────────────────────────────────────────────

    # Construye la estructura principal de la ventana.
    def _construir_ventana(self):
        self.setWindowTitle("Simulador de Planificación de Procesos del SO")
        self.resize(1380, 950)
        self.setMinimumSize(1080, 700)
        self.setStyleSheet(f"QMainWindow {{ background-color: {a_css(COLOR_FONDO_PRIMARIO)}; }}")

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_central = QVBoxLayout(widget_central)
        layout_central.setContentsMargins(0, 0, 0, 0)
        layout_central.setSpacing(0)

        # ── Cabecera superior ─────────────────────────────────────────────
        cabecera = self._crear_cabecera()
        layout_central.addWidget(cabecera)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_central.addWidget(sep)

        # ── Cuerpo principal (sidebar + contenido) ────────────────────────
        cuerpo = QWidget()
        cuerpo.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout_cuerpo = QHBoxLayout(cuerpo)
        layout_cuerpo.setContentsMargins(0, 0, 0, 0)
        layout_cuerpo.setSpacing(0)

        # Sidebar de navegación
        sidebar = self._crear_sidebar()
        layout_cuerpo.addWidget(sidebar)

        sep_v = QFrame()
        sep_v.setFrameShape(QFrame.VLine)
        sep_v.setFixedWidth(1)
        sep_v.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_cuerpo.addWidget(sep_v)

        # Área de contenido con stack
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout_cuerpo.addWidget(self._stack)

        # Construir los tres paneles
        self._panel_simulador = self._construir_panel_simulador()
        self._panel_comparacion = self._construir_panel_comparacion()
        self._panel_bancario = self._construir_panel_bancario()

        self._stack.addWidget(self._panel_simulador)
        self._stack.addWidget(self._panel_comparacion)
        self._stack.addWidget(self._panel_bancario)
        self._stack.setCurrentIndex(0)

        layout_central.addWidget(cuerpo)

    # Crea la cabecera superior de la ventana.
    def _crear_cabecera(self) -> QWidget:
        cabecera = QWidget()
        cabecera.setFixedHeight(58)
        cabecera.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_SECUNDARIO)};")

        layout = QVBoxLayout(cabecera)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(2)

        titulo = QLabel("Simulador de Planificación de Procesos")
        titulo.setFont(fuente_h1())
        titulo.setStyleSheet(f"color: {a_css(COLOR_ACENTO_BRILLANTE)}; background: transparent;")

        subtitulo = QLabel("FIFO  ·  SJF  ·  Round Robin  ·  MLQ  —  Diagrama de Gantt en Tiempo Real")
        subtitulo.setFont(fuente_pequena())
        subtitulo.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        return cabecera

    # Crea el sidebar de navegación lateral.
    def _crear_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(192)
        sidebar.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_SECUNDARIO)};")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        lbl_modulos = QLabel("MÓDULOS")
        lbl_modulos.setFont(fuente_pequena())
        lbl_modulos.setStyleSheet(
            f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent; padding: 8px 16px 4px 16px;"
        )
        layout.addWidget(lbl_modulos)

        self._nav_simulador = ItemNavegacion("⚙", "Simulador")
        self._nav_comparacion = ItemNavegacion("📊", "Comparación")
        self._nav_bancario = ItemNavegacion("🏦", "Sist. Bancario")

        self._nav_simulador.seleccionado = True
        self._nav_simulador.clic.connect(lambda: self._cambiar_panel(0))
        self._nav_comparacion.clic.connect(lambda: self._cambiar_panel(1))
        self._nav_bancario.clic.connect(lambda: self._cambiar_panel(2))

        self._items_nav = [self._nav_simulador, self._nav_comparacion, self._nav_bancario]

        for item in self._items_nav:
            layout.addWidget(item)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout.addWidget(sep)
        layout.addStretch()
        return sidebar

    # Cambia el panel visible y actualiza el estado de los ítems de navegación.
    def _cambiar_panel(self, indice: int):
        self._stack.setCurrentIndex(indice)
        for i, item in enumerate(self._items_nav):
            item.seleccionado = (i == indice)

    # ─────────────────────────────────────────────────────────────────────
    # PANEL SIMULADOR
    # ─────────────────────────────────────────────────────────────────────

    # Construye el panel principal de simulación con configuración y Gantt.
    def _construir_panel_simulador(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {a_css(COLOR_BORDE)}; width: 2px; }}")

        # Panel izquierdo: configuración
        panel_config = self._construir_config_simulador()
        splitter.addWidget(panel_config)

        # Panel derecho: Gantt + estadísticas
        panel_gantt_stats = self._construir_area_gantt_simulador()
        splitter.addWidget(panel_gantt_stats)

        splitter.setSizes([342, 900])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        return panel

    # Construye el área de configuración izquierda del simulador.
    def _construir_config_simulador(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {a_css(COLOR_FONDO_PRIMARIO)}; border: none; }}")

        contenido = QWidget()
        contenido.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        lbl_sec = QLabel("CONFIGURACIÓN")
        lbl_sec.setFont(fuente_pequena())
        lbl_sec.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")
        layout.addWidget(lbl_sec)

        # ── Tarjeta: Procesos ─────────────────────────────────────────────
        tarjeta_proc = TarjetaTema("Procesos")
        tarjeta_proc.setFixedHeight(228)
        layout_proc = QVBoxLayout(tarjeta_proc)
        layout_proc.setContentsMargins(0, 0, 0, 0)
        layout_proc.setSpacing(0)

        self._tabla_procesos = crear_tabla(["Llegada", "Ráfaga", "Prioridad"])
        self._tabla_procesos.setColumnWidth(0, 82)
        self._tabla_procesos.setColumnWidth(1, 82)
        self._tabla_procesos.setColumnWidth(2, 98)
        layout_proc.addWidget(self._tabla_procesos)

        sep_proc = QFrame()
        sep_proc.setFrameShape(QFrame.HLine)
        sep_proc.setFixedHeight(1)
        sep_proc.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_proc.addWidget(sep_proc)

        fila_botones_proc = QWidget()
        fila_botones_proc.setFixedHeight(36)
        fila_botones_proc.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        layout_btn_proc = QHBoxLayout(fila_botones_proc)
        layout_btn_proc.setContentsMargins(3, 3, 3, 3)
        layout_btn_proc.setSpacing(4)

        self._btn_agregar_proceso = crear_boton("➕ Agregar", COLOR_EXITO_OSCURO, 92, 28)
        self._btn_eliminar_proceso = crear_boton("🗑 Eliminar", COLOR_PELIGRO_OSCURO, 92, 28)
        self._btn_cargar_archivo = crear_boton("📂 Archivo", QColor(30, 60, 100), 88, 28)

        self._btn_agregar_proceso.clicked.connect(self._al_agregar_proceso)
        self._btn_eliminar_proceso.clicked.connect(self._al_eliminar_proceso)
        self._btn_cargar_archivo.clicked.connect(self._al_cargar_archivo)

        layout_btn_proc.addWidget(self._btn_agregar_proceso)
        layout_btn_proc.addWidget(self._btn_eliminar_proceso)
        layout_btn_proc.addWidget(self._btn_cargar_archivo)
        layout_btn_proc.addStretch()
        layout_proc.addWidget(fila_botones_proc)
        layout.addWidget(tarjeta_proc)

        # ── Tarjeta: Algoritmo ────────────────────────────────────────────
        tarjeta_alg = TarjetaTema("Algoritmo de Planificación")
        tarjeta_alg.setFixedHeight(118)
        inner_alg = QWidget(tarjeta_alg)
        inner_alg.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 84)
        inner_alg.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")

        layout_alg = QVBoxLayout(inner_alg)
        layout_alg.setContentsMargins(8, 6, 8, 6)
        layout_alg.setSpacing(8)

        fila_alg = QHBoxLayout()
        lbl_alg = crear_etiqueta_campo("Algoritmo:")
        lbl_alg.setFixedWidth(90)
        self._combo_algoritmo = crear_combo(["FIFO", "SJF", "Round Robin", "MLQ"])
        self._combo_algoritmo.currentIndexChanged.connect(self._al_cambiar_algoritmo)
        fila_alg.addWidget(lbl_alg)
        fila_alg.addWidget(self._combo_algoritmo)
        fila_alg.addStretch()
        layout_alg.addLayout(fila_alg)

        fila_quantum = QHBoxLayout()
        self._lbl_quantum = crear_etiqueta_campo("Quantum:")
        self._lbl_quantum.setFixedWidth(90)
        self._spin_quantum = crear_spinbox(1, 100, 2)
        self._spin_quantum.setFixedWidth(72)
        fila_quantum.addWidget(self._lbl_quantum)
        fila_quantum.addWidget(self._spin_quantum)
        fila_quantum.addStretch()
        layout_alg.addLayout(fila_quantum)

        layout.addWidget(tarjeta_alg)

        # ── Tarjeta: Config MLQ (oculta inicialmente) ─────────────────────
        self._tarjeta_mlq = TarjetaTema("Configuración MLQ")
        self._tarjeta_mlq.setFixedHeight(165)
        self._tarjeta_mlq.setVisible(False)
        inner_mlq = QWidget(self._tarjeta_mlq)
        inner_mlq.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 131)
        inner_mlq.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")

        layout_mlq = QVBoxLayout(inner_mlq)
        layout_mlq.setContentsMargins(8, 6, 8, 6)
        layout_mlq.setSpacing(4)

        algs = ["FIFO", "SJF", "Round Robin"]
        etiquetas_colas = ["Cola ALTA:", "Cola MEDIA:", "Cola BAJA:"]
        self._combo_cola_alta = crear_combo(algs, indice=2)
        self._combo_cola_media = crear_combo(algs, indice=0)
        self._combo_cola_baja = crear_combo(algs, indice=1)
        self._spin_quantum_alta = crear_spinbox(1, 100, 2)
        self._spin_quantum_media = crear_spinbox(1, 100, 2)
        self._spin_quantum_baja = crear_spinbox(1, 100, 2)
        self._spin_quantum_media.setVisible(False)
        self._spin_quantum_baja.setVisible(False)

        self._combo_cola_alta.currentIndexChanged.connect(
            lambda i: self._spin_quantum_alta.setVisible(i == 2))
        self._combo_cola_media.currentIndexChanged.connect(
            lambda i: self._spin_quantum_media.setVisible(i == 2))
        self._combo_cola_baja.currentIndexChanged.connect(
            lambda i: self._spin_quantum_baja.setVisible(i == 2))

        for lbl_txt, combo, spin in [
            (etiquetas_colas[0], self._combo_cola_alta, self._spin_quantum_alta),
            (etiquetas_colas[1], self._combo_cola_media, self._spin_quantum_media),
            (etiquetas_colas[2], self._combo_cola_baja, self._spin_quantum_baja),
        ]:
            fila = QHBoxLayout()
            lbl = crear_etiqueta_campo(lbl_txt)
            lbl.setFixedWidth(82)
            combo.setFixedWidth(122)
            spin.setFixedWidth(65)
            fila.addWidget(lbl)
            fila.addWidget(combo)
            fila.addWidget(spin)
            fila.addStretch()
            layout_mlq.addLayout(fila)

        layout.addWidget(self._tarjeta_mlq)

        # ── Tarjeta: Control de ejecución ─────────────────────────────────
        tarjeta_ctrl = TarjetaTema("Control de Ejecución")
        tarjeta_ctrl.setFixedHeight(116)
        inner_ctrl = QWidget(tarjeta_ctrl)
        inner_ctrl.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 82)
        inner_ctrl.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")

        layout_ctrl = QVBoxLayout(inner_ctrl)
        layout_ctrl.setContentsMargins(6, 6, 6, 6)
        layout_ctrl.setSpacing(6)

        fila_botones_ctrl = QHBoxLayout()
        self._btn_ejecutar = crear_boton("▶  Ejecutar", COLOR_EXITO_OSCURO, 100, 34)
        self._btn_pausar = crear_boton("⏸  Pausar", QColor(160, 100, 0), 90, 34)
        self._btn_reset = crear_boton("↺  Reset", COLOR_PURPURA_OSCURO, 80, 34)
        self._btn_pausar.setEnabled(False)

        self._btn_ejecutar.clicked.connect(self._al_ejecutar)
        self._btn_pausar.clicked.connect(self._al_pausar)
        self._btn_reset.clicked.connect(self._al_reset)

        fila_botones_ctrl.addWidget(self._btn_ejecutar)
        fila_botones_ctrl.addWidget(self._btn_pausar)
        fila_botones_ctrl.addWidget(self._btn_reset)
        fila_botones_ctrl.addStretch()
        layout_ctrl.addLayout(fila_botones_ctrl)

        fila_vel = QHBoxLayout()
        lbl_vel = crear_etiqueta_campo("Velocidad (ms):")
        lbl_vel.setFixedWidth(115)
        self._spin_velocidad = crear_spinbox(50, 2000, 500)
        self._spin_velocidad.setSingleStep(50)
        self._spin_velocidad.setFixedWidth(82)
        fila_vel.addWidget(lbl_vel)
        fila_vel.addWidget(self._spin_velocidad)
        fila_vel.addStretch()
        layout_ctrl.addLayout(fila_vel)

        layout.addWidget(tarjeta_ctrl)
        layout.addStretch()

        scroll.setWidget(contenido)
        return scroll

    # Construye el área derecha del simulador (Gantt + estadísticas).
    def _construir_area_gantt_simulador(self) -> QSplitter:
        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.setStyleSheet(
            f"QSplitter::handle {{ background-color: {a_css(COLOR_BORDE)}; height: 2px; }}"
        )

        # ── Tarjeta Gantt ─────────────────────────────────────────────────
        tarjeta_gantt = TarjetaTema("Diagrama de Gantt en Tiempo Real")
        layout_gantt = QVBoxLayout(tarjeta_gantt)
        layout_gantt.setContentsMargins(0, 0, 0, 0)
        layout_gantt.setSpacing(0)

        barra_estado = QWidget()
        barra_estado.setFixedHeight(36)
        barra_estado.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_SECUNDARIO)};")
        layout_barra = QHBoxLayout(barra_estado)
        layout_barra.setContentsMargins(10, 6, 10, 6)
        layout_barra.setSpacing(10)

        self._lbl_reloj = QLabel("⏱  t = 0")
        self._lbl_reloj.setFont(fuente_mono_grande())
        self._lbl_reloj.setStyleSheet(f"color: {a_css(COLOR_ACENTO_CYAN)}; background: transparent;")

        self._barra_progreso = QProgressBar()
        self._barra_progreso.setTextVisible(False)
        self._barra_progreso.setFixedHeight(14)
        self._barra_progreso.setStyleSheet(f"""
            QProgressBar {{
                background-color: {a_css(COLOR_SUPERFICIE_ELEV)};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {a_css(COLOR_ACENTO_CYAN)};
                border-radius: 3px;
            }}
        """)

        layout_barra.addWidget(self._lbl_reloj)
        layout_barra.addWidget(self._barra_progreso, 1)
        layout_gantt.addWidget(barra_estado)

        self._gantt_simulador = VistaGantt()
        layout_gantt.addWidget(self._gantt_simulador)
        splitter_v.addWidget(tarjeta_gantt)

        # ── Tarjeta Estadísticas ──────────────────────────────────────────
        tarjeta_stats = TarjetaTema("Estadísticas de Ejecución")
        layout_stats = QVBoxLayout(tarjeta_stats)
        layout_stats.setContentsMargins(0, 0, 0, 0)
        layout_stats.setSpacing(0)

        self._tabla_estadisticas_sim = crear_tabla(
            ["Proceso", "Llegada", "Fin", "T. Espera", "T. Retorno"]
        )
        layout_stats.addWidget(self._tabla_estadisticas_sim)

        barra_resumen = QWidget()
        barra_resumen.setFixedHeight(36)
        barra_resumen.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE_ELEV)};")
        layout_resumen = QHBoxLayout(barra_resumen)
        layout_resumen.setContentsMargins(10, 6, 10, 6)
        layout_resumen.setSpacing(20)

        self._lbl_prom_espera_sim = self._crear_lbl_resumen("Prom. Espera: —")
        self._lbl_prom_retorno_sim = self._crear_lbl_resumen("Prom. Retorno: —")
        self._lbl_uso_cpu_sim = self._crear_lbl_resumen("Uso CPU: —")

        layout_resumen.addWidget(self._lbl_prom_espera_sim)
        layout_resumen.addWidget(self._lbl_prom_retorno_sim)
        layout_resumen.addWidget(self._lbl_uso_cpu_sim)
        layout_resumen.addStretch()

        sep_stats = QFrame()
        sep_stats.setFrameShape(QFrame.HLine)
        sep_stats.setFixedHeight(1)
        sep_stats.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_stats.addWidget(sep_stats)
        layout_stats.addWidget(barra_resumen)
        splitter_v.addWidget(tarjeta_stats)

        splitter_v.setSizes([400, 200])
        return splitter_v

    # ─────────────────────────────────────────────────────────────────────
    # PANEL COMPARACIÓN
    # ─────────────────────────────────────────────────────────────────────

    # Construye el panel de comparación automática de algoritmos.
    def _construir_panel_comparacion(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)

        tarjeta = TarjetaTema("Comparación Automática — FIFO vs SJF vs Round Robin")
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(0, 0, 0, 0)
        layout_tarjeta.setSpacing(0)

        # Barra superior con descripción y botón
        barra_top = QWidget()
        barra_top.setFixedHeight(66)
        barra_top.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        layout_top = QVBoxLayout(barra_top)
        layout_top.setContentsMargins(10, 6, 10, 6)
        layout_top.setSpacing(4)

        desc = QLabel("Usa los procesos actuales del Simulador para comparar los tres algoritmos con las mismas entradas.")
        desc.setFont(fuente_base())
        desc.setStyleSheet(f"color: {a_css(COLOR_TEXTO_SECUNDARIO)}; background: transparent;")
        layout_top.addWidget(desc)

        self._btn_comparar = crear_boton("🔄  Comparar con procesos actuales",
                                          QColor(25, 60, 110), 280, 36)
        self._btn_comparar.clicked.connect(self._al_comparar)
        layout_top.addWidget(self._btn_comparar)

        layout_tarjeta.addWidget(barra_top)

        self._tabla_comparacion = crear_tabla(
            ["Algoritmo", "Prom. Espera", "Prom. Retorno", "Uso CPU (%)"]
        )
        self._tabla_comparacion.setColumnWidth(0, 240)
        self._tabla_comparacion.setColumnWidth(1, 150)
        self._tabla_comparacion.setColumnWidth(2, 150)
        self._tabla_comparacion.setColumnWidth(3, 150)
        layout_tarjeta.addWidget(self._tabla_comparacion)

        layout.addWidget(tarjeta)
        return panel

    # ─────────────────────────────────────────────────────────────────────
    # PANEL SISTEMA BANCARIO
    # ─────────────────────────────────────────────────────────────────────

    # Construye el panel del sistema bancario con clientes y MLQ.
    def _construir_panel_bancario(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {a_css(COLOR_BORDE)}; width: 2px; }}")

        # Panel izquierdo: configuración clientes
        panel_clientes = self._construir_config_bancario()
        splitter.addWidget(panel_clientes)

        # Panel derecho: Gantt + estadísticas bancarias
        panel_gantt_bco = self._construir_area_gantt_bancario()
        splitter.addWidget(panel_gantt_bco)

        splitter.setSizes([342, 900])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        return panel

    # Construye el área de configuración de clientes bancarios.
    def _construir_config_bancario(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {a_css(COLOR_FONDO_PRIMARIO)}; border: none; }}")

        contenido = QWidget()
        contenido.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        lbl_sec = QLabel("CLIENTES BANCARIOS")
        lbl_sec.setFont(fuente_pequena())
        lbl_sec.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")
        layout.addWidget(lbl_sec)

        # ── Tarjeta: Clientes ─────────────────────────────────────────────
        tarjeta_cli = TarjetaTema("Registrar Clientes")
        tarjeta_cli.setFixedHeight(228)
        layout_cli = QVBoxLayout(tarjeta_cli)
        layout_cli.setContentsMargins(0, 0, 0, 0)
        layout_cli.setSpacing(0)

        self._tabla_clientes = crear_tabla(["Nombre", "Tipo", "Llegada"])
        self._tabla_clientes.setColumnWidth(0, 100)
        self._tabla_clientes.setColumnWidth(1, 114)
        self._tabla_clientes.setColumnWidth(2, 72)
        layout_cli.addWidget(self._tabla_clientes)

        sep_cli = QFrame()
        sep_cli.setFrameShape(QFrame.HLine)
        sep_cli.setFixedHeight(1)
        sep_cli.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_cli.addWidget(sep_cli)

        fila_btn_cli = QWidget()
        fila_btn_cli.setFixedHeight(36)
        fila_btn_cli.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        layout_btn_cli = QHBoxLayout(fila_btn_cli)
        layout_btn_cli.setContentsMargins(3, 3, 3, 3)
        layout_btn_cli.setSpacing(4)

        self._btn_agregar_cliente = crear_boton("➕ Agregar", COLOR_EXITO_OSCURO, 92, 28)
        self._btn_eliminar_cliente = crear_boton("🗑 Eliminar", COLOR_PELIGRO_OSCURO, 92, 28)
        self._btn_agregar_cliente.clicked.connect(self._al_agregar_cliente)
        self._btn_eliminar_cliente.clicked.connect(self._al_eliminar_cliente)

        layout_btn_cli.addWidget(self._btn_agregar_cliente)
        layout_btn_cli.addWidget(self._btn_eliminar_cliente)
        layout_btn_cli.addStretch()
        layout_cli.addWidget(fila_btn_cli)
        layout.addWidget(tarjeta_cli)

        # ── Tarjeta: Info tipos ───────────────────────────────────────────
        tarjeta_info = TarjetaTema("Tipos & Tiempos de Atención")
        tarjeta_info.setFixedHeight(152)
        inner_info = QWidget(tarjeta_info)
        inner_info.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 118)
        inner_info.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")

        layout_info = QVBoxLayout(inner_info)
        layout_info.setContentsMargins(8, 4, 8, 4)
        layout_info.setSpacing(2)

        tipos_info = [
            ("VIP",         "2 min", "Prioridad 1 — Cola Alta",  COLORES_PROCESOS[0]),
            ("ADULTOMAYOR", "3 min", "Prioridad 2 — Cola Alta",  COLORES_PROCESOS[1]),
            ("EMBARAZADA",  "3 min", "Prioridad 3 — Cola Media", COLORES_PROCESOS[2]),
            ("REGULAR",     "4 min", "Prioridad 4 — Cola Baja",  COLORES_PROCESOS[3]),
            ("FORANEO",     "5 min", "Prioridad 5 — Cola Baja",  COLORES_PROCESOS[4]),
        ]
        for tipo, tiempo, desc, color in tipos_info:
            lbl = QLabel(f"● {tipo:<12}  {tiempo:<7}  {desc}")
            lbl.setFont(QFont("Consolas", 7))
            lbl.setStyleSheet(
                f"color: rgb({aclarar(color, 28).red()},{aclarar(color, 28).green()},{aclarar(color, 28).blue()}); "
                f"background: transparent;"
            )
            layout_info.addWidget(lbl)

        layout.addWidget(tarjeta_info)

        # ── Botón ejecutar MLQ ────────────────────────────────────────────
        self._btn_ejecutar_bco = crear_boton("▶  Ejecutar MLQ Bancario",
                                              COLOR_EXITO_OSCURO, 240, 38)
        self._btn_ejecutar_bco.clicked.connect(self._al_ejecutar_bancario)
        layout.addWidget(self._btn_ejecutar_bco)
        layout.addStretch()

        scroll.setWidget(contenido)
        return scroll

    # Construye el área de Gantt y estadísticas del sistema bancario.
    def _construir_area_gantt_bancario(self) -> QSplitter:
        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.setStyleSheet(
            f"QSplitter::handle {{ background-color: {a_css(COLOR_BORDE)}; height: 2px; }}"
        )

        tarjeta_gantt = TarjetaTema("Gantt — Sistema Bancario")
        layout_gantt = QVBoxLayout(tarjeta_gantt)
        layout_gantt.setContentsMargins(0, 0, 0, 0)

        self._gantt_bancario = VistaGantt()
        layout_gantt.addWidget(self._gantt_bancario)
        splitter_v.addWidget(tarjeta_gantt)

        tarjeta_stats = TarjetaTema("Estadísticas del Sistema Bancario")
        layout_stats = QVBoxLayout(tarjeta_stats)
        layout_stats.setContentsMargins(0, 0, 0, 0)
        layout_stats.setSpacing(0)

        self._tabla_estadisticas_bco = crear_tabla(
            ["Cliente", "Tipo", "Llegada", "Fin", "T. Espera", "T. Retorno"]
        )
        layout_stats.addWidget(self._tabla_estadisticas_bco)

        barra_resumen_bco = QWidget()
        barra_resumen_bco.setFixedHeight(36)
        barra_resumen_bco.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE_ELEV)};")
        layout_res_bco = QHBoxLayout(barra_resumen_bco)
        layout_res_bco.setContentsMargins(10, 6, 10, 6)
        layout_res_bco.setSpacing(20)

        self._lbl_prom_espera_bco = self._crear_lbl_resumen("Prom. Espera: —")
        self._lbl_prom_retorno_bco = self._crear_lbl_resumen("Prom. Retorno: —")
        self._lbl_uso_cpu_bco = self._crear_lbl_resumen("Uso CPU: —")
        layout_res_bco.addWidget(self._lbl_prom_espera_bco)
        layout_res_bco.addWidget(self._lbl_prom_retorno_bco)
        layout_res_bco.addWidget(self._lbl_uso_cpu_bco)
        layout_res_bco.addStretch()

        sep_bco = QFrame()
        sep_bco.setFrameShape(QFrame.HLine)
        sep_bco.setFixedHeight(1)
        sep_bco.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_stats.addWidget(sep_bco)
        layout_stats.addWidget(barra_resumen_bco)
        splitter_v.addWidget(tarjeta_stats)

        splitter_v.setSizes([400, 200])
        return splitter_v

    # ─────────────────────────────────────────────────────────────────────
    # DATOS DE DEMOSTRACIÓN
    # ─────────────────────────────────────────────────────────────────────

    # Carga los datos de demostración equivalentes al proyecto WinForms.
    def _cargar_datos_demostracion(self):
        datos_demo_procesos = [
            (0, 5, 1), (2, 3, 2), (4, 8, 1), (6, 2, 3), (8, 4, 2),
        ]
        for llegada, rafaga, prioridad in datos_demo_procesos:
            agregar_fila_tabla(self._tabla_procesos, [llegada, rafaga, prioridad])

        datos_demo_clientes = [
            ("Ana",    "VIP",         0),
            ("Carlos", "ADULTOMAYOR", 1),
            ("María",  "EMBARAZADA",  2),
            ("Luis",   "REGULAR",     3),
            ("Pedro",  "FORANEO",     4),
        ]
        for nombre, tipo, llegada in datos_demo_clientes:
            agregar_fila_tabla(self._tabla_clientes, [nombre, tipo, llegada])

    # ─────────────────────────────────────────────────────────────────────
    # EVENTOS — SIMULADOR
    # ─────────────────────────────────────────────────────────────────────

    # Muestra/oculta campos de quantum y configuración MLQ según el algoritmo.
    def _al_cambiar_algoritmo(self, indice: int):
        es_rr = (indice == 2)
        es_mlq = (indice == 3)
        self._lbl_quantum.setVisible(es_rr)
        self._spin_quantum.setVisible(es_rr)
        self._tarjeta_mlq.setVisible(es_mlq)

    # Abre el diálogo y agrega el nuevo proceso a la tabla.
    def _al_agregar_proceso(self):
        dialogo = DialogoProceso(self)
        if dialogo.exec() == DialogoProceso.Accepted:
            agregar_fila_tabla(
                self._tabla_procesos,
                [dialogo.llegada, dialogo.rafaga, dialogo.prioridad],
            )

    # Elimina las filas seleccionadas de la tabla de procesos.
    def _al_eliminar_proceso(self):
        filas = sorted(
            set(item.row() for item in self._tabla_procesos.selectedItems()),
            reverse=True,
        )
        for fila in filas:
            self._tabla_procesos.removeRow(fila)

    # Carga procesos desde un archivo .txt seleccionado por el usuario.
    def _al_cargar_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Cargar procesos", "",
            "Archivos de texto (*.txt);;Todos los archivos (*.*)"
        )
        if not ruta:
            return
        procesos, advertencias = cargar_procesos_desde_archivo(ruta)
        if advertencias:
            QMessageBox.warning(self, "Advertencias al cargar", "\n".join(advertencias))
        if not procesos:
            QMessageBox.warning(self, "Aviso", "No se encontraron procesos válidos.")
            return
        self._tabla_procesos.setRowCount(0)
        for p in procesos:
            agregar_fila_tabla(self._tabla_procesos, [p.tiempo_llegada, p.tiempo_rafaga, p.prioridad])

    # Inicia la simulación del algoritmo seleccionado.
    def _al_ejecutar(self):
        if self._simulacion_en_curso:
            return
        procesos = self._leer_procesos_de_tabla()
        if not procesos:
            QMessageBox.warning(self, "Aviso", "Ingrese al menos un proceso.")
            return

        self._al_reset()
        self._procesos_actuales = procesos
        planificador = self._construir_planificador()
        copias = [p.clonar() for p in procesos]
        self._segmentos_actuales = planificador.ejecutar(copias)

        if not self._segmentos_actuales:
            QMessageBox.warning(self, "Aviso", "No se generaron segmentos de ejecución.")
            return

        nombres_unicos = list(dict.fromkeys(s.nombre_proceso for s in self._segmentos_actuales))
        self._mapa_colores = {
            nombre: COLORES_PROCESOS[i % len(COLORES_PROCESOS)]
            for i, nombre in enumerate(nombres_unicos)
        }

        self._gantt_simulador.inicializar(self._segmentos_actuales, self._mapa_colores)
        self._barra_progreso.setMaximum(max(s.fin for s in self._segmentos_actuales))
        self._barra_progreso.setValue(0)

        # Preparar la animación tick a tick
        self._segmentos_pendientes = sorted(self._segmentos_actuales, key=lambda s: s.inicio)
        self._indice_seg = 0
        self._tick_en_seg = 0
        self._simulacion_en_curso = True
        self._btn_ejecutar.setEnabled(False)
        self._btn_pausar.setEnabled(True)

        delay = self._spin_velocidad.value()
        self._timer_animacion.start(delay)

    # Pausa o reanuda la simulación en curso.
    def _al_pausar(self):
        if self._simulacion_en_curso:
            self._timer_animacion.stop()
            self._simulacion_en_curso = False
            self._btn_pausar.setText("▶ Continuar")
            self._btn_pausar.setStyleSheet(css_boton(QColor(0, 120, 60)))
            self._btn_ejecutar.setEnabled(True)
        else:
            # Reanudar
            self._simulacion_en_curso = True
            self._btn_pausar.setText("⏸  Pausar")
            self._btn_pausar.setStyleSheet(css_boton(QColor(160, 100, 0)))
            self._btn_ejecutar.setEnabled(False)
            delay = self._spin_velocidad.value()
            self._timer_animacion.start(delay)

    # Detiene la simulación y limpia el Gantt.
    def _al_reset(self):
        self._timer_animacion.stop()
        self._simulacion_en_curso = False
        self._btn_ejecutar.setEnabled(True)
        self._btn_pausar.setEnabled(False)
        self._btn_pausar.setText("⏸  Pausar")
        self._btn_pausar.setStyleSheet(css_boton(QColor(160, 100, 0)))
        self._lbl_reloj.setText("⏱  t = 0")
        self._barra_progreso.setValue(0)
        self._gantt_simulador.resetear()
        self._tabla_estadisticas_sim.setRowCount(0)
        self._lbl_prom_espera_sim.setText("Prom. Espera: —")
        self._lbl_prom_retorno_sim.setText("Prom. Retorno: —")
        self._lbl_uso_cpu_sim.setText("Uso CPU: —")

    # Tick de animación: avanza un unidad de tiempo en el Gantt.
    def _tick_animacion(self):
        if self._indice_seg >= len(self._segmentos_pendientes):
            self._timer_animacion.stop()
            self._simulacion_en_curso = False
            self._btn_ejecutar.setEnabled(True)
            self._btn_pausar.setEnabled(False)
            self._mostrar_estadisticas_simulador()
            return

        seg = self._segmentos_pendientes[self._indice_seg]
        t_actual = seg.inicio + self._tick_en_seg
        t_fin = t_actual + 1
        color = self._mapa_colores.get(seg.nombre_proceso, QColor(128, 128, 128))

        self._gantt_simulador.avanzar_tick(seg.nombre_proceso, t_fin, color)
        self._lbl_reloj.setText(f"⏱  t = {t_fin}")
        self._barra_progreso.setValue(min(t_fin, self._barra_progreso.maximum()))

        self._tick_en_seg += 1
        if self._tick_en_seg >= (seg.fin - seg.inicio):
            self._indice_seg += 1
            self._tick_en_seg = 0

        # Ajustar velocidad dinámicamente
        nuevo_delay = self._spin_velocidad.value()
        if self._timer_animacion.interval() != nuevo_delay:
            self._timer_animacion.setInterval(nuevo_delay)

    # ─────────────────────────────────────────────────────────────────────
    # EVENTOS — COMPARACIÓN
    # ─────────────────────────────────────────────────────────────────────

    # Ejecuta la comparación de algoritmos con los procesos actuales.
    def _al_comparar(self):
        procesos = self._leer_procesos_de_tabla()
        if not procesos:
            QMessageBox.warning(self, "Aviso", "Ingrese al menos un proceso.")
            return

        self._tabla_comparacion.setRowCount(0)
        quantum = self._spin_quantum.value()
        resultados = comparar_algoritmos(procesos, quantum)

        for resultado in resultados:
            agregar_fila_tabla(self._tabla_comparacion, [
                resultado["algoritmo"],
                f"{resultado['promedio_espera']:.2f}",
                f"{resultado['promedio_retorno']:.2f}",
                f"{resultado['uso_cpu']:.1f}%",
            ], centrado=True)

        # Resaltar la mejor fila en columnas 1 (menor espera) y 2 (menor retorno) y 3 (mayor uso)
        self._colorear_mejor(self._tabla_comparacion, 1, mayor_es_mejor=False)
        self._colorear_mejor(self._tabla_comparacion, 2, mayor_es_mejor=False)
        self._colorear_mejor(self._tabla_comparacion, 3, mayor_es_mejor=True)

    # ─────────────────────────────────────────────────────────────────────
    # EVENTOS — SISTEMA BANCARIO
    # ─────────────────────────────────────────────────────────────────────

    # Abre el diálogo y agrega el nuevo cliente a la tabla.
    def _al_agregar_cliente(self):
        dialogo = DialogoCliente(self)
        if dialogo.exec() == DialogoCliente.Accepted:
            agregar_fila_tabla(
                self._tabla_clientes,
                [dialogo.nombre, dialogo.tipo, dialogo.llegada],
            )

    # Elimina las filas seleccionadas de la tabla de clientes.
    def _al_eliminar_cliente(self):
        filas = sorted(
            set(item.row() for item in self._tabla_clientes.selectedItems()),
            reverse=True,
        )
        for fila in filas:
            self._tabla_clientes.removeRow(fila)

    # Ejecuta el MLQ bancario con los clientes registrados.
    def _al_ejecutar_bancario(self):
        clientes = self._leer_clientes_de_tabla()
        if not clientes:
            QMessageBox.warning(self, "Aviso", "Registre al menos un cliente.")
            return

        self._tabla_estadisticas_bco.setRowCount(0)
        self._gantt_bancario.resetear()

        clientes_ordenados = sorted(clientes, key=lambda c: c.tiempo_llegada)
        procesos: List[Proceso] = []
        for idx, cliente in enumerate(clientes_ordenados, start=1):
            procesos.append(Proceso(
                id_proceso=idx,
                tiempo_llegada=cliente.tiempo_llegada,
                tiempo_rafaga=cliente.obtener_tiempo_atencion(),
                prioridad=cliente.prioridad,
                nombre=cliente.nombre,
            ))

        # MLQ con configuración fija: Alta→RR(q=2), Media→FIFO, Baja→SJF
        mlq = PlanificadorMLQ(
            PlanificadorRoundRobin(2),
            PlanificadorFIFO(),
            PlanificadorSJF(),
        )
        copias = [p.clonar() for p in procesos]
        segmentos = mlq.ejecutar(copias)

        if not segmentos:
            QMessageBox.warning(self, "Aviso", "No se generaron segmentos.")
            return

        nombres_unicos = list(dict.fromkeys(s.nombre_proceso for s in segmentos))
        mapa_colores = {
            nombre: COLORES_PROCESOS[i % len(COLORES_PROCESOS)]
            for i, nombre in enumerate(nombres_unicos)
        }

        self._gantt_bancario.inicializar(segmentos, mapa_colores)

        # Animación instantánea (sin delay) para el bancario
        for seg in sorted(segmentos, key=lambda s: s.inicio):
            for t in range(seg.inicio, seg.fin + 1):
                color = mapa_colores.get(seg.nombre_proceso, QColor(128, 128, 128))
                self._gantt_bancario.avanzar_tick(seg.nombre_proceso, t, color)

        self._mostrar_estadisticas_bancario(segmentos, clientes_ordenados)

        # Persistir clientes atendidos
        estadisticas = calcular_estadisticas_desde_segmentos(segmentos)
        guardar_clientes_atendidos(clientes_ordenados, estadisticas)

    # ─────────────────────────────────────────────────────────────────────
    # LECTURA DE TABLAS
    # ─────────────────────────────────────────────────────────────────────

    # Lee y convierte las filas de la tabla de procesos en objetos Proceso.
    def _leer_procesos_de_tabla(self) -> List[Proceso]:
        procesos = []
        for fila in range(self._tabla_procesos.rowCount()):
            try:
                llegada = int(self._tabla_procesos.item(fila, 0).text())
                rafaga = int(self._tabla_procesos.item(fila, 1).text())
                prioridad = int(self._tabla_procesos.item(fila, 2).text())
                if rafaga <= 0:
                    continue
                procesos.append(Proceso(
                    id_proceso=fila + 1,
                    tiempo_llegada=llegada,
                    tiempo_rafaga=rafaga,
                    prioridad=prioridad,
                ))
            except (AttributeError, ValueError):
                continue
        return procesos

    # Lee y convierte las filas de la tabla de clientes en objetos Cliente.
    def _leer_clientes_de_tabla(self) -> List[Cliente]:
        clientes = []
        for fila in range(self._tabla_clientes.rowCount()):
            try:
                nombre = self._tabla_clientes.item(fila, 0).text().strip()
                tipo = self._tabla_clientes.item(fila, 1).text().strip().upper()
                llegada = int(self._tabla_clientes.item(fila, 2).text())
                if not nombre or not tipo:
                    continue
                clientes.append(Cliente(nombre, tipo, llegada))
            except (AttributeError, ValueError):
                continue
        return clientes

    # ─────────────────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE PLANIFICADORES
    # ─────────────────────────────────────────────────────────────────────

    # Instancia el planificador correcto según el algoritmo seleccionado.
    def _construir_planificador(self) -> PlanificadorBase:
        idx = self._combo_algoritmo.currentIndex()
        if idx == 0:
            return PlanificadorFIFO()
        if idx == 1:
            return PlanificadorSJF()
        if idx == 2:
            return PlanificadorRoundRobin(self._spin_quantum.value())
        if idx == 3:
            return PlanificadorMLQ(
                self._crear_planificador_cola(self._combo_cola_alta, self._spin_quantum_alta),
                self._crear_planificador_cola(self._combo_cola_media, self._spin_quantum_media),
                self._crear_planificador_cola(self._combo_cola_baja, self._spin_quantum_baja),
            )
        return PlanificadorFIFO()

    # Crea el planificador de una cola MLQ según el combo y spinbox dados.
    def _crear_planificador_cola(self, combo: QComboBox,
                                  spin: QSpinBox) -> PlanificadorBase:
        idx = combo.currentIndex()
        if idx == 0:
            return PlanificadorFIFO()
        if idx == 1:
            return PlanificadorSJF()
        if idx == 2:
            return PlanificadorRoundRobin(spin.value())
        return PlanificadorFIFO()

    # ─────────────────────────────────────────────────────────────────────
    # MOSTRAR ESTADÍSTICAS
    # ─────────────────────────────────────────────────────────────────────

    # Rellena la tabla y etiquetas de resumen del simulador.
    def _mostrar_estadisticas_simulador(self):
        if not self._segmentos_actuales:
            return
        estadisticas = calcular_estadisticas_desde_segmentos(self._segmentos_actuales)
        resumen = calcular_resumen_global(self._segmentos_actuales)

        self._tabla_estadisticas_sim.setRowCount(0)
        for est in estadisticas:
            agregar_fila_tabla(self._tabla_estadisticas_sim, [
                est["nombre"], est["llegada"], est["fin"],
                est["espera"], est["retorno"],
            ])

        self._lbl_prom_espera_sim.setText(f"Prom. Espera: {resumen['promedio_espera']:.2f}")
        self._lbl_prom_retorno_sim.setText(f"Prom. Retorno: {resumen['promedio_retorno']:.2f}")
        self._lbl_uso_cpu_sim.setText(f"Uso CPU: {resumen['uso_cpu']:.1f}%")

    # Rellena la tabla y etiquetas de resumen del sistema bancario.
    def _mostrar_estadisticas_bancario(self, segmentos: List[SegmentoEjecucion],
                                        clientes: List[Cliente]):
        estadisticas = calcular_estadisticas_desde_segmentos(segmentos)
        resumen = calcular_resumen_global(segmentos)

        mapa_tipos = {c.nombre: c.tipo for c in clientes}
        self._tabla_estadisticas_bco.setRowCount(0)
        for est in estadisticas:
            tipo = mapa_tipos.get(est["nombre"], "—")
            agregar_fila_tabla(self._tabla_estadisticas_bco, [
                est["nombre"], tipo, est["llegada"], est["fin"],
                est["espera"], est["retorno"],
            ])

        self._lbl_prom_espera_bco.setText(f"Prom. Espera: {resumen['promedio_espera']:.2f}")
        self._lbl_prom_retorno_bco.setText(f"Prom. Retorno: {resumen['promedio_retorno']:.2f}")
        self._lbl_uso_cpu_bco.setText(f"Uso CPU: {resumen['uso_cpu']:.1f}%")

    # ─────────────────────────────────────────────────────────────────────
    # UTILIDADES DE INTERFAZ
    # ─────────────────────────────────────────────────────────────────────

    # Crea una etiqueta de resumen con el estilo de acento cyan.
    def _crear_lbl_resumen(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setFont(fuente_seccion())
        lbl.setStyleSheet(f"color: {a_css(COLOR_ACENTO_CYAN)}; background: transparent;")
        return lbl

    # Resalta la celda con el mejor valor (menor o mayor) en una columna de la tabla.
    def _colorear_mejor(self, tabla, col_idx: int, mayor_es_mejor: bool):
        n = tabla.rowCount()
        if n == 0:
            return
        mejor_valor = None
        mejor_fila = 0
        for fila in range(n):
            item = tabla.item(fila, col_idx)
            if item is None:
                continue
            try:
                valor = float(item.text().replace("%", ""))
            except ValueError:
                continue
            if mejor_valor is None:
                mejor_valor = valor
                mejor_fila = fila
            elif mayor_es_mejor and valor > mejor_valor:
                mejor_valor = valor
                mejor_fila = fila
            elif not mayor_es_mejor and valor < mejor_valor:
                mejor_valor = valor
                mejor_fila = fila

        if tabla.item(mejor_fila, col_idx) is not None:
            tabla.item(mejor_fila, col_idx).setBackground(COLOR_EXITO_OSCURO)
            tabla.item(mejor_fila, col_idx).setForeground(COLOR_ACENTO_CYAN)
