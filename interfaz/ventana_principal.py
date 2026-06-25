from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QComboBox, QSpinBox, QFrame,
    QScrollArea, QFileDialog, QMessageBox, QTableWidgetItem,
    QStackedWidget, QSizePolicy, QProgressBar,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen

from interfaz.tema import (
    COLOR_FONDO_PRIMARIO, COLOR_FONDO_SECUNDARIO, COLOR_SUPERFICIE,
    COLOR_SUPERFICIE_ALT, COLOR_SUPERFICIE_ELEV, COLOR_SUPERFICIE_HOVER,
    COLOR_BORDE, COLOR_BORDE_FUERTE,
    COLOR_ACENTO, COLOR_ACENTO_BRILLANTE, COLOR_ACENTO_CYAN,
    COLOR_TEXTO_PRIMARIO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_MUTED,
    COLOR_EXITO, COLOR_EXITO_OSCURO,
    COLOR_PELIGRO, COLOR_PELIGRO_OSCURO,
    COLOR_ADVERTENCIA, COLOR_PURPURA,
    COLORES_PROCESOS,
    fuente_h1, fuente_h2, fuente_base, fuente_pequena,
    fuente_seccion, fuente_mono_grande, fuente_mono,
    css_boton, a_css, aclarar, oscurecer,
)
from interfaz.controles_personalizados import (
    TarjetaTema, ItemNavegacion, crear_boton, crear_tabla,
    agregar_fila_tabla, crear_etiqueta_campo, crear_spinbox, crear_combo,
)
from interfaz.vista_gantt import VistaGantt, tick_a_hora, tick_a_duracion
from interfaz.dialogo_proceso import DialogoProceso
from interfaz.dialogo_cliente import DialogoCliente
from interfaz.panel_emergencias import PanelEmergencias

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


# ── Colores semánticos de botones ─────────────────────────────────────────────
_BTN_ACCION   = COLOR_EXITO            # Verde para ejecutar / agregar
_BTN_PELIGRO  = COLOR_PELIGRO          # Rojo para eliminar / cancelar
_BTN_NEUTRO   = COLOR_ACENTO           # Azul para archivo / comparar
_BTN_PAUSA    = QColor(180, 110,  0)   # Ámbar para pausa
_BTN_RESET    = COLOR_PURPURA          # Púrpura para reset
_COLOR_MEJOR_BG  = QColor(210, 248, 220)  # Fondo verde suave (resaltado)
_COLOR_MEJOR_FG  = QColor(25,  90,  45)   # Texto verde oscuro


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

    # ── CONSTRUCCIÓN DE LA INTERFAZ ───────────────────────────────────────────

    def _construir_ventana(self):
        self.setWindowTitle("Simulador de Planificación de Procesos del SO")
        self.resize(1420, 960)
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(f"QMainWindow {{ background-color: {a_css(COLOR_FONDO_PRIMARIO)}; }}")

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_central = QVBoxLayout(widget_central)
        layout_central.setContentsMargins(0, 0, 0, 0)
        layout_central.setSpacing(0)

        layout_central.addWidget(self._crear_cabecera())
        layout_central.addWidget(self._crear_barra_navegacion())

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_central.addWidget(sep)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout_central.addWidget(self._stack)

        self._panel_simulador   = self._construir_panel_simulador()
        self._panel_comparacion = self._construir_panel_comparacion()
        self._panel_emergencias = PanelEmergencias()

        self._stack.addWidget(self._panel_simulador)
        self._stack.addWidget(self._panel_comparacion)
        self._stack.addWidget(self._panel_emergencias)
        self._stack.setCurrentIndex(0)

    def _crear_cabecera(self) -> QWidget:
        cabecera = QWidget()
        cabecera.setFixedHeight(68)
        cabecera.setStyleSheet(f"""
            background-color: {a_css(COLOR_SUPERFICIE)};
            border-bottom: 3px solid {a_css(COLOR_ACENTO)};
        """)

        layout = QHBoxLayout(cabecera)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(14)

        # Bloque de texto izquierdo
        bloque_texto = QWidget()
        bloque_texto.setStyleSheet("background: transparent;")
        col = QVBoxLayout(bloque_texto)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(3)

        titulo = QLabel("Simulador de Planificación de Procesos del SO")
        f_tit = QFont("Segoe UI", 13)
        f_tit.setBold(True)
        titulo.setFont(f_tit)
        titulo.setStyleSheet(f"color: {a_css(COLOR_TEXTO_PRIMARIO)}; background: transparent;")

        col.addWidget(titulo)
        layout.addWidget(bloque_texto)
        layout.addStretch()

        # Badges de algoritmos disponibles
        for alg in ["FIFO", "SJF", "Round Robin", "MLQ"]:
            badge = QLabel(alg)
            badge.setFont(QFont("Segoe UI", 7, QFont.Bold))
            badge.setAlignment(Qt.AlignCenter)
            badge.setFixedHeight(22)
            badge.setContentsMargins(8, 0, 8, 0)
            badge.setStyleSheet(f"""
                color: {a_css(COLOR_ACENTO)};
                background-color: rgb(237, 241, 252);
                border: 1px solid {a_css(QColor(196, 210, 248))};
                border-radius: 11px;
                padding: 0 6px;
            """)
            layout.addWidget(badge)

        return cabecera

    def _crear_barra_navegacion(self) -> QWidget:
        barra = QWidget()
        barra.setFixedHeight(48)
        barra.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")

        layout = QHBoxLayout(barra)
        layout.setContentsMargins(8, 0, 20, 0)
        layout.setSpacing(0)

        # Etiqueta "MÓDULOS"
        lbl = QLabel("MÓDULOS")
        f_lbl = QFont("Segoe UI", 7)
        f_lbl.setBold(True)
        f_lbl.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        lbl.setFont(f_lbl)
        lbl.setStyleSheet(
            f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent; padding: 0 14px 0 10px;"
        )
        layout.addWidget(lbl)

        # Separador vertical decorativo
        sep_v = QFrame()
        sep_v.setFrameShape(QFrame.VLine)
        sep_v.setFixedWidth(1)
        sep_v.setFixedHeight(26)
        sep_v.setStyleSheet(f"background: {a_css(COLOR_BORDE)};")
        layout.addWidget(sep_v)

        self._nav_simulador    = ItemNavegacion("⚙", "Simulador")
        self._nav_comparacion  = ItemNavegacion("📊", "Comparación")
        self._nav_emergencias  = ItemNavegacion("🏥", "Emergencias")

        for nav in [self._nav_simulador, self._nav_comparacion, self._nav_emergencias]:
            nav.setFixedWidth(158)

        self._nav_simulador.seleccionado = True
        self._nav_simulador.clic.connect(lambda: self._cambiar_panel(0))
        self._nav_comparacion.clic.connect(lambda: self._cambiar_panel(1))
        self._nav_emergencias.clic.connect(lambda: self._cambiar_panel(2))

        self._items_nav = [self._nav_simulador, self._nav_comparacion, self._nav_emergencias]

        for item in self._items_nav:
            layout.addWidget(item)

        layout.addStretch()

        lbl_ver = QLabel("Arquitectura y Sistemas Operativos - CUC 2026")
        lbl_ver.setFont(QFont("Segoe UI", 7))
        lbl_ver.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_ver.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")
        layout.addWidget(lbl_ver)

        return barra

    def _cambiar_panel(self, indice: int):
        self._stack.setCurrentIndex(indice)
        for i, item in enumerate(self._items_nav):
            item.seleccionado = (i == indice)

    # ── PANEL SIMULADOR ───────────────────────────────────────────────────────

    def _construir_panel_simulador(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background-color: {a_css(COLOR_BORDE)}; width: 1px; }}"
        )

        splitter.addWidget(self._construir_config_simulador())
        splitter.addWidget(self._construir_area_gantt_simulador())
        splitter.setSizes([348, 960])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        return panel

    def _construir_config_simulador(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {a_css(COLOR_SUPERFICIE)}; border: none; }}"
        )

        contenido = QWidget()
        contenido.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        lbl_sec = QLabel("CONFIGURACIÓN")
        f_sec = QFont("Segoe UI", 7)
        f_sec.setBold(True)
        f_sec.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        lbl_sec.setFont(f_sec)
        lbl_sec.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent; margin-bottom: 2px;")
        layout.addWidget(lbl_sec)

        # ── Tarjeta: Procesos ─────────────────────────────────────────────────
        tarjeta_proc = TarjetaTema("Procesos de entrada")
        tarjeta_proc.setFixedHeight(232)
        layout_proc = QVBoxLayout(tarjeta_proc)
        layout_proc.setContentsMargins(0, 0, 0, 0)
        layout_proc.setSpacing(0)

        self._tabla_procesos = crear_tabla(["Proceso", "Llegada", "Ráfaga", "Prioridad"])
        layout_proc.addWidget(self._tabla_procesos)

        sep_proc = QFrame()
        sep_proc.setFrameShape(QFrame.HLine)
        sep_proc.setFixedHeight(1)
        sep_proc.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_proc.addWidget(sep_proc)

        fila_btn_proc = QWidget()
        fila_btn_proc.setFixedHeight(38)
        fila_btn_proc.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout_btn = QHBoxLayout(fila_btn_proc)
        layout_btn.setContentsMargins(6, 5, 6, 5)
        layout_btn.setSpacing(5)

        self._btn_agregar_proceso = crear_boton("+ Agregar", _BTN_ACCION, 88, 28)
        self._btn_eliminar_proceso = crear_boton("Eliminar", _BTN_PELIGRO, 82, 28)
        self._btn_cargar_archivo = crear_boton("Cargar TXT", _BTN_NEUTRO, 78, 28)

        self._btn_agregar_proceso.clicked.connect(self._al_agregar_proceso)
        self._btn_eliminar_proceso.clicked.connect(self._al_eliminar_proceso)
        self._btn_cargar_archivo.clicked.connect(self._al_cargar_archivo)

        layout_btn.addWidget(self._btn_agregar_proceso)
        layout_btn.addWidget(self._btn_eliminar_proceso)
        layout_btn.addWidget(self._btn_cargar_archivo)
        layout_btn.addStretch()
        layout_proc.addWidget(fila_btn_proc)
        layout.addWidget(tarjeta_proc)

        # ── Tarjeta: Algoritmo ────────────────────────────────────────────────
        tarjeta_alg = TarjetaTema("Algoritmo de planificación")
        tarjeta_alg.setFixedHeight(124)
        inner_alg = QWidget(tarjeta_alg)
        inner_alg.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 88)
        inner_alg.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")

        layout_alg = QVBoxLayout(inner_alg)
        layout_alg.setContentsMargins(10, 8, 10, 8)
        layout_alg.setSpacing(10)

        fila_alg = QHBoxLayout()
        lbl_alg = crear_etiqueta_campo("Algoritmo:")
        lbl_alg.setFixedWidth(88)
        self._combo_algoritmo = crear_combo(["FIFO", "SJF", "Round Robin", "MLQ"])
        self._combo_algoritmo.currentIndexChanged.connect(self._al_cambiar_algoritmo)
        fila_alg.addWidget(lbl_alg)
        fila_alg.addWidget(self._combo_algoritmo)
        fila_alg.addStretch()
        layout_alg.addLayout(fila_alg)

        fila_quantum = QHBoxLayout()
        self._lbl_quantum = crear_etiqueta_campo("Quantum:")
        self._lbl_quantum.setFixedWidth(88)
        self._spin_quantum = crear_spinbox(1, 100, 2)
        self._spin_quantum.setFixedWidth(76)
        fila_quantum.addWidget(self._lbl_quantum)
        fila_quantum.addWidget(self._spin_quantum)
        fila_quantum.addStretch()
        layout_alg.addLayout(fila_quantum)

        layout.addWidget(tarjeta_alg)

        # ── Tarjeta: Config MLQ ───────────────────────────────────────────────
        self._tarjeta_mlq = TarjetaTema("Configuración MLQ")
        self._tarjeta_mlq.setFixedHeight(170)
        self._tarjeta_mlq.setVisible(False)
        inner_mlq = QWidget(self._tarjeta_mlq)
        inner_mlq.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 134)
        inner_mlq.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")

        layout_mlq = QVBoxLayout(inner_mlq)
        layout_mlq.setContentsMargins(10, 8, 10, 8)
        layout_mlq.setSpacing(6)

        algs = ["FIFO", "SJF", "Round Robin"]
        self._combo_cola_alta  = crear_combo(algs, indice=2)
        self._combo_cola_media = crear_combo(algs, indice=0)
        self._combo_cola_baja  = crear_combo(algs, indice=1)
        self._spin_quantum_alta  = crear_spinbox(1, 100, 2)
        self._spin_quantum_media = crear_spinbox(1, 100, 2)
        self._spin_quantum_baja  = crear_spinbox(1, 100, 2)
        self._spin_quantum_media.setVisible(False)
        self._spin_quantum_baja.setVisible(False)

        self._combo_cola_alta.currentIndexChanged.connect(
            lambda i: self._spin_quantum_alta.setVisible(i == 2))
        self._combo_cola_media.currentIndexChanged.connect(
            lambda i: self._spin_quantum_media.setVisible(i == 2))
        self._combo_cola_baja.currentIndexChanged.connect(
            lambda i: self._spin_quantum_baja.setVisible(i == 2))

        for lbl_txt, combo, spin in [
            ("Cola ALTA:",  self._combo_cola_alta,  self._spin_quantum_alta),
            ("Cola MEDIA:", self._combo_cola_media, self._spin_quantum_media),
            ("Cola BAJA:",  self._combo_cola_baja,  self._spin_quantum_baja),
        ]:
            fila = QHBoxLayout()
            lbl = crear_etiqueta_campo(lbl_txt)
            lbl.setFixedWidth(84)
            combo.setFixedWidth(118)
            spin.setFixedWidth(68)
            fila.addWidget(lbl)
            fila.addWidget(combo)
            fila.addWidget(spin)
            fila.addStretch()
            layout_mlq.addLayout(fila)

        layout.addWidget(self._tarjeta_mlq)

        # ── Tarjeta: Control ──────────────────────────────────────────────────
        tarjeta_ctrl = TarjetaTema("Control de ejecución")
        tarjeta_ctrl.setFixedHeight(122)
        inner_ctrl = QWidget(tarjeta_ctrl)
        inner_ctrl.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 86)
        inner_ctrl.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")

        layout_ctrl = QVBoxLayout(inner_ctrl)
        layout_ctrl.setContentsMargins(8, 8, 8, 8)
        layout_ctrl.setSpacing(8)

        fila_ctrl = QHBoxLayout()
        self._btn_ejecutar = crear_boton("▶  Ejecutar", _BTN_ACCION, 104, 34)
        self._btn_pausar   = crear_boton("⏸  Pausar",  _BTN_PAUSA,   94, 34)
        self._btn_reset    = crear_boton("↺  Reset",   _BTN_RESET,   82, 34)
        self._btn_pausar.setEnabled(False)

        self._btn_ejecutar.clicked.connect(self._al_ejecutar)
        self._btn_pausar.clicked.connect(self._al_pausar)
        self._btn_reset.clicked.connect(self._al_reset)

        fila_ctrl.addWidget(self._btn_ejecutar)
        fila_ctrl.addWidget(self._btn_pausar)
        fila_ctrl.addWidget(self._btn_reset)
        fila_ctrl.addStretch()
        layout_ctrl.addLayout(fila_ctrl)

        fila_vel = QHBoxLayout()
        lbl_vel = crear_etiqueta_campo("Velocidad (ms):")
        lbl_vel.setFixedWidth(118)
        self._spin_velocidad = crear_spinbox(50, 2000, 500)
        self._spin_velocidad.setSingleStep(50)
        self._spin_velocidad.setFixedWidth(86)
        fila_vel.addWidget(lbl_vel)
        fila_vel.addWidget(self._spin_velocidad)
        fila_vel.addStretch()
        layout_ctrl.addLayout(fila_vel)

        layout.addWidget(tarjeta_ctrl)
        layout.addStretch()

        scroll.setWidget(contenido)
        return scroll

    def _construir_area_gantt_simulador(self) -> QSplitter:
        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.setStyleSheet(
            f"QSplitter::handle {{ background-color: {a_css(COLOR_BORDE)}; height: 1px; }}"
        )

        # ── Tarjeta Gantt ─────────────────────────────────────────────────────
        tarjeta_gantt = TarjetaTema("Diagrama de Gantt — Ejecución en tiempo real")
        layout_gantt = QVBoxLayout(tarjeta_gantt)
        layout_gantt.setContentsMargins(0, 0, 0, 0)
        layout_gantt.setSpacing(0)

        # Barra de estado (reloj + barra de progreso)
        barra_est = QWidget()
        barra_est.setFixedHeight(38)
        barra_est.setStyleSheet(f"""
            background-color: {a_css(COLOR_FONDO_PRIMARIO)};
            border-bottom: 1px solid {a_css(COLOR_BORDE)};
        """)
        layout_barra = QHBoxLayout(barra_est)
        layout_barra.setContentsMargins(12, 8, 12, 8)
        layout_barra.setSpacing(12)

        self._lbl_reloj = QLabel("t = 0")
        f_reloj = QFont("Consolas", 11)
        f_reloj.setBold(True)
        self._lbl_reloj.setFont(f_reloj)
        self._lbl_reloj.setFixedWidth(80)
        self._lbl_reloj.setStyleSheet(
            f"color: {a_css(COLOR_ACENTO)}; background: transparent;"
        )

        self._barra_progreso = QProgressBar()
        self._barra_progreso.setTextVisible(False)
        self._barra_progreso.setFixedHeight(10)
        self._barra_progreso.setStyleSheet(f"""
            QProgressBar {{
                background-color: {a_css(COLOR_SUPERFICIE_ELEV)};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {a_css(COLOR_ACENTO)};
                border-radius: 5px;
            }}
        """)

        layout_barra.addWidget(self._lbl_reloj)
        layout_barra.addWidget(self._barra_progreso, 1)
        layout_gantt.addWidget(barra_est)

        self._gantt_simulador = VistaGantt()
        layout_gantt.addWidget(self._gantt_simulador)
        splitter_v.addWidget(tarjeta_gantt)

        # ── Tarjeta Estadísticas ──────────────────────────────────────────────
        tarjeta_stats = TarjetaTema("Estadísticas de ejecución")
        layout_stats = QVBoxLayout(tarjeta_stats)
        layout_stats.setContentsMargins(0, 0, 0, 0)
        layout_stats.setSpacing(0)

        self._tabla_estadisticas_sim = crear_tabla(
            ["Proceso", "H. Llegada", "H. Fin", "T. Espera", "T. Retorno"]
        )
        layout_stats.addWidget(self._tabla_estadisticas_sim)

        sep_st = QFrame()
        sep_st.setFrameShape(QFrame.HLine)
        sep_st.setFixedHeight(1)
        sep_st.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_stats.addWidget(sep_st)

        barra_res = self._crear_barra_resumen_sim()
        layout_stats.addWidget(barra_res)
        splitter_v.addWidget(tarjeta_stats)

        splitter_v.setSizes([420, 200])
        return splitter_v

    def _crear_barra_resumen_sim(self) -> QWidget:
        barra = QWidget()
        barra.setFixedHeight(42)
        barra.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self._lbl_prom_espera_sim   = self._crear_chip_metrica("Prom. Espera", "—")
        self._lbl_prom_retorno_sim  = self._crear_chip_metrica("Prom. Retorno", "—")
        self._lbl_uso_cpu_sim       = self._crear_chip_metrica("Uso CPU", "—")

        layout.addWidget(self._lbl_prom_espera_sim)
        layout.addWidget(self._lbl_prom_retorno_sim)
        layout.addWidget(self._lbl_uso_cpu_sim)
        layout.addStretch()
        return barra

    # ── PANEL COMPARACIÓN ─────────────────────────────────────────────────────

    def _construir_panel_comparacion(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(0)

        tarjeta = TarjetaTema("Comparación automática de algoritmos")
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(0, 0, 0, 0)
        layout_tarjeta.setSpacing(0)

        # Banda superior con descripción + botón
        banda = QWidget()
        banda.setFixedHeight(72)
        banda.setStyleSheet(f"""
            background-color: {a_css(COLOR_SUPERFICIE)};
            border-bottom: 1px solid {a_css(COLOR_BORDE)};
        """)
        layout_banda = QVBoxLayout(banda)
        layout_banda.setContentsMargins(14, 10, 14, 10)
        layout_banda.setSpacing(5)

        desc = QLabel(
            "Ejecuta FIFO, SJF y Round Robin sobre los mismos procesos del Simulador "
            "y compara sus métricas. Los mejores valores se resaltan en verde."
        )
        desc.setFont(fuente_base())
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {a_css(COLOR_TEXTO_SECUNDARIO)}; background: transparent;")
        layout_banda.addWidget(desc)

        self._btn_comparar = crear_boton(
            "Comparar con procesos actuales", _BTN_NEUTRO, 260, 34
        )
        self._btn_comparar.clicked.connect(self._al_comparar)
        layout_banda.addWidget(self._btn_comparar)

        layout_tarjeta.addWidget(banda)

        self._tabla_comparacion = crear_tabla(
            ["Algoritmo", "Prom. Espera", "Prom. Retorno", "Uso CPU (%)"]
        )
        self._tabla_comparacion.setColumnWidth(0, 240)
        self._tabla_comparacion.setColumnWidth(1, 150)
        self._tabla_comparacion.setColumnWidth(2, 160)
        self._tabla_comparacion.setColumnWidth(3, 150)
        layout_tarjeta.addWidget(self._tabla_comparacion)

        layout.addWidget(tarjeta)
        return panel

    # ── PANEL SISTEMA BANCARIO ────────────────────────────────────────────────

    def _construir_panel_bancario(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background-color: {a_css(COLOR_BORDE)}; width: 1px; }}"
        )

        splitter.addWidget(self._construir_config_bancario())
        splitter.addWidget(self._construir_area_gantt_bancario())
        splitter.setSizes([348, 960])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        return panel

    def _construir_config_bancario(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {a_css(COLOR_SUPERFICIE)}; border: none; }}"
        )

        contenido = QWidget()
        contenido.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        lbl_sec = QLabel("CLIENTES BANCARIOS")
        f_sec = QFont("Segoe UI", 7)
        f_sec.setBold(True)
        f_sec.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        lbl_sec.setFont(f_sec)
        lbl_sec.setStyleSheet(
            f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent; margin-bottom: 2px;"
        )
        layout.addWidget(lbl_sec)

        # ── Tarjeta: Clientes ─────────────────────────────────────────────────
        tarjeta_cli = TarjetaTema("Registrar clientes")
        tarjeta_cli.setFixedHeight(232)
        layout_cli = QVBoxLayout(tarjeta_cli)
        layout_cli.setContentsMargins(0, 0, 0, 0)
        layout_cli.setSpacing(0)

        self._tabla_clientes = crear_tabla(["Nombre", "Tipo", "Llegada"])
        layout_cli.addWidget(self._tabla_clientes)

        sep_cli = QFrame()
        sep_cli.setFrameShape(QFrame.HLine)
        sep_cli.setFixedHeight(1)
        sep_cli.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_cli.addWidget(sep_cli)

        fila_btn_cli = QWidget()
        fila_btn_cli.setFixedHeight(38)
        fila_btn_cli.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout_btn_cli = QHBoxLayout(fila_btn_cli)
        layout_btn_cli.setContentsMargins(6, 5, 6, 5)
        layout_btn_cli.setSpacing(5)

        self._btn_agregar_cliente = crear_boton("+ Agregar", _BTN_ACCION, 88, 28)
        self._btn_eliminar_cliente = crear_boton("Eliminar", _BTN_PELIGRO, 82, 28)
        self._btn_agregar_cliente.clicked.connect(self._al_agregar_cliente)
        self._btn_eliminar_cliente.clicked.connect(self._al_eliminar_cliente)

        layout_btn_cli.addWidget(self._btn_agregar_cliente)
        layout_btn_cli.addWidget(self._btn_eliminar_cliente)
        layout_btn_cli.addStretch()
        layout_cli.addWidget(fila_btn_cli)
        layout.addWidget(tarjeta_cli)

        # ── Tarjeta: Tipos & Prioridades ──────────────────────────────────────
        tarjeta_info = TarjetaTema("Tipos y tiempos de atención")
        tarjeta_info.setFixedHeight(180)
        inner_info = QWidget(tarjeta_info)
        inner_info.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 144)
        inner_info.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")

        layout_info = QVBoxLayout(inner_info)
        layout_info.setContentsMargins(10, 6, 10, 6)
        layout_info.setSpacing(4)

        tipos_info = [
            ("VIP",         "2 min", "Prioridad 1 — Cola Alta",  COLORES_PROCESOS[0]),
            ("ADULTOMAYOR", "3 min", "Prioridad 2 — Cola Alta",  COLORES_PROCESOS[1]),
            ("EMBARAZADA",  "3 min", "Prioridad 3 — Cola Media", COLORES_PROCESOS[2]),
            ("REGULAR",     "4 min", "Prioridad 4 — Cola Baja",  COLORES_PROCESOS[3]),
            ("FORANEO",     "5 min", "Prioridad 5 — Cola Baja",  COLORES_PROCESOS[4]),
        ]
        for tipo, tiempo, desc, color in tipos_info:
            fila_tipo = QWidget()
            fila_tipo.setFixedHeight(22)
            fila_tipo.setStyleSheet("background: transparent;")
            h = QHBoxLayout(fila_tipo)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)

            # Chip de color
            chip = QLabel()
            chip.setFixedSize(10, 10)
            chip.setStyleSheet(
                f"background-color: {a_css(color)}; border-radius: 5px;"
            )

            lbl_tipo = QLabel(f"{tipo:<12}")
            lbl_tipo.setFont(QFont("Consolas", 7))
            lbl_tipo.setStyleSheet(
                f"color: {a_css(oscurecer(color, 30))}; background: transparent; font-weight: bold;"
            )
            lbl_tipo.setFixedWidth(88)

            lbl_tiempo = QLabel(tiempo)
            lbl_tiempo.setFont(QFont("Segoe UI", 7))
            lbl_tiempo.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")
            lbl_tiempo.setFixedWidth(38)

            lbl_desc = QLabel(desc)
            lbl_desc.setFont(QFont("Segoe UI", 7))
            lbl_desc.setStyleSheet(f"color: {a_css(COLOR_TEXTO_SECUNDARIO)}; background: transparent;")

            h.addWidget(chip)
            h.addWidget(lbl_tipo)
            h.addWidget(lbl_tiempo)
            h.addWidget(lbl_desc)
            h.addStretch()
            layout_info.addWidget(fila_tipo)

        layout.addWidget(tarjeta_info)

        # ── Botón ejecutar ────────────────────────────────────────────────────
        self._btn_ejecutar_bco = crear_boton(
            "▶  Ejecutar MLQ Bancario", _BTN_ACCION, 244, 38
        )
        self._btn_ejecutar_bco.clicked.connect(self._al_ejecutar_bancario)
        layout.addWidget(self._btn_ejecutar_bco)
        layout.addStretch()

        scroll.setWidget(contenido)
        return scroll

    def _construir_area_gantt_bancario(self) -> QSplitter:
        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.setStyleSheet(
            f"QSplitter::handle {{ background-color: {a_css(COLOR_BORDE)}; height: 1px; }}"
        )

        tarjeta_gantt = TarjetaTema("Gantt — Sistema Bancario MLQ")
        layout_gantt = QVBoxLayout(tarjeta_gantt)
        layout_gantt.setContentsMargins(0, 0, 0, 0)

        self._gantt_bancario = VistaGantt()
        layout_gantt.addWidget(self._gantt_bancario)
        splitter_v.addWidget(tarjeta_gantt)

        tarjeta_stats = TarjetaTema("Estadísticas del sistema bancario")
        layout_stats = QVBoxLayout(tarjeta_stats)
        layout_stats.setContentsMargins(0, 0, 0, 0)
        layout_stats.setSpacing(0)

        self._tabla_estadisticas_bco = crear_tabla(
            ["Cliente", "Tipo", "Llegada", "Fin", "T. Espera", "T. Retorno"]
        )
        layout_stats.addWidget(self._tabla_estadisticas_bco)

        sep_bco = QFrame()
        sep_bco.setFrameShape(QFrame.HLine)
        sep_bco.setFixedHeight(1)
        sep_bco.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_stats.addWidget(sep_bco)

        barra_res_bco = self._crear_barra_resumen_bco()
        layout_stats.addWidget(barra_res_bco)
        splitter_v.addWidget(tarjeta_stats)

        splitter_v.setSizes([420, 200])
        return splitter_v

    def _crear_barra_resumen_bco(self) -> QWidget:
        barra = QWidget()
        barra.setFixedHeight(42)
        barra.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout = QHBoxLayout(barra)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self._lbl_prom_espera_bco  = self._crear_chip_metrica("Prom. Espera", "—")
        self._lbl_prom_retorno_bco = self._crear_chip_metrica("Prom. Retorno", "—")
        self._lbl_uso_cpu_bco      = self._crear_chip_metrica("Uso CPU", "—")

        layout.addWidget(self._lbl_prom_espera_bco)
        layout.addWidget(self._lbl_prom_retorno_bco)
        layout.addWidget(self._lbl_uso_cpu_bco)
        layout.addStretch()
        return barra

    # ── DATOS DE DEMOSTRACIÓN ─────────────────────────────────────────────────

    def _cargar_datos_demostracion(self):
        for idx, (llegada, rafaga, prioridad) in enumerate(
            [(0, 5, 1), (2, 3, 2), (4, 8, 1), (6, 2, 3), (8, 4, 2)],
            start=1,
        ):
            agregar_fila_tabla(self._tabla_procesos, [f"P{idx}", llegada, rafaga, prioridad])

    # ── EVENTOS — SIMULADOR ───────────────────────────────────────────────────

    def _al_cambiar_algoritmo(self, indice: int):
        es_rr  = (indice == 2)
        es_mlq = (indice == 3)
        self._lbl_quantum.setVisible(es_rr)
        self._spin_quantum.setVisible(es_rr)
        self._tarjeta_mlq.setVisible(es_mlq)

    def _al_agregar_proceso(self):
        dlg = DialogoProceso(self)
        if dlg.exec() == DialogoProceso.Accepted:
            siguiente = self._tabla_procesos.rowCount() + 1
            agregar_fila_tabla(self._tabla_procesos,
                               [f"P{siguiente}", dlg.llegada, dlg.rafaga, dlg.prioridad])

    def _al_eliminar_proceso(self):
        filas = sorted(
            set(item.row() for item in self._tabla_procesos.selectedItems()),
            reverse=True,
        )
        for f in filas:
            self._tabla_procesos.removeRow(f)

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
            QMessageBox.warning(self, "Aviso", "No se encontraron procesos válidos en el archivo.")
            return
        self._tabla_procesos.setRowCount(0)
        for idx, p in enumerate(procesos, start=1):
            agregar_fila_tabla(self._tabla_procesos,
                               [p.nombre or f"P{idx}", p.tiempo_llegada, p.tiempo_rafaga, p.prioridad])

    def _al_ejecutar(self):
        if self._simulacion_en_curso:
            return
        procesos = self._leer_procesos_de_tabla()
        if not procesos:
            QMessageBox.warning(self, "Sin procesos", "Ingrese al menos un proceso antes de ejecutar.")
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

        self._segmentos_pendientes = sorted(self._segmentos_actuales, key=lambda s: s.inicio)
        self._indice_seg = 0
        self._tick_en_seg = 0
        self._simulacion_en_curso = True
        self._btn_ejecutar.setEnabled(False)
        self._btn_pausar.setEnabled(True)

        self._timer_animacion.start(self._spin_velocidad.value())

    def _al_pausar(self):
        if self._simulacion_en_curso:
            self._timer_animacion.stop()
            self._simulacion_en_curso = False
            self._btn_pausar.setText("▶ Continuar")
            self._btn_pausar.setStyleSheet(css_boton(COLOR_ACENTO))
            self._btn_ejecutar.setEnabled(True)
        else:
            self._simulacion_en_curso = True
            self._btn_pausar.setText("⏸  Pausar")
            self._btn_pausar.setStyleSheet(css_boton(_BTN_PAUSA))
            self._btn_ejecutar.setEnabled(False)
            self._timer_animacion.start(self._spin_velocidad.value())

    def _al_reset(self):
        self._timer_animacion.stop()
        self._simulacion_en_curso = False
        self._btn_ejecutar.setEnabled(True)
        self._btn_pausar.setEnabled(False)
        self._btn_pausar.setText("⏸  Pausar")
        self._btn_pausar.setStyleSheet(css_boton(_BTN_PAUSA))
        self._lbl_reloj.setText("07:00")
        self._barra_progreso.setValue(0)
        self._gantt_simulador.resetear()
        self._tabla_estadisticas_sim.setRowCount(0)
        self._actualizar_chip("prom_espera_sim", "—")
        self._actualizar_chip("prom_retorno_sim", "—")
        self._actualizar_chip("uso_cpu_sim", "—")

    def _tick_animacion(self):
        if self._indice_seg >= len(self._segmentos_pendientes):
            self._timer_animacion.stop()
            self._simulacion_en_curso = False
            self._btn_ejecutar.setEnabled(True)
            self._btn_pausar.setEnabled(False)
            self._mostrar_estadisticas_simulador()
            return

        seg = self._segmentos_pendientes[self._indice_seg]
        t_fin = seg.inicio + self._tick_en_seg + 1
        color = self._mapa_colores.get(seg.nombre_proceso, QColor(128, 128, 128))

        self._gantt_simulador.avanzar_tick(seg.nombre_proceso, t_fin, color)
        self._lbl_reloj.setText(tick_a_hora(t_fin))
        self._barra_progreso.setValue(min(t_fin, self._barra_progreso.maximum()))

        self._tick_en_seg += 1
        if self._tick_en_seg >= (seg.fin - seg.inicio):
            self._indice_seg += 1
            self._tick_en_seg = 0

        nuevo_delay = self._spin_velocidad.value()
        if self._timer_animacion.interval() != nuevo_delay:
            self._timer_animacion.setInterval(nuevo_delay)

    # ── EVENTOS — COMPARACIÓN ─────────────────────────────────────────────────

    def _al_comparar(self):
        procesos = self._leer_procesos_de_tabla()
        if not procesos:
            QMessageBox.warning(self, "Sin procesos",
                                "Ingrese al menos un proceso en el Simulador.")
            return

        self._tabla_comparacion.setRowCount(0)
        resultados = comparar_algoritmos(procesos, self._spin_quantum.value())

        for r in resultados:
            agregar_fila_tabla(self._tabla_comparacion, [
                r["algoritmo"],
                tick_a_duracion(r["promedio_espera"]),
                tick_a_duracion(r["promedio_retorno"]),
                f"{r['uso_cpu']:.1f}%",
            ], centrado=True)

        self._colorear_mejor(self._tabla_comparacion, 1, mayor_es_mejor=False)
        self._colorear_mejor(self._tabla_comparacion, 2, mayor_es_mejor=False)
        self._colorear_mejor(self._tabla_comparacion, 3, mayor_es_mejor=True)

    # ── EVENTOS — SISTEMA BANCARIO ────────────────────────────────────────────

    def _al_agregar_cliente(self):
        dlg = DialogoCliente(self)
        if dlg.exec() == DialogoCliente.Accepted:
            agregar_fila_tabla(self._tabla_clientes,
                               [dlg.nombre, dlg.tipo, dlg.llegada])

    def _al_eliminar_cliente(self):
        filas = sorted(
            set(item.row() for item in self._tabla_clientes.selectedItems()),
            reverse=True,
        )
        for f in filas:
            self._tabla_clientes.removeRow(f)

    def _al_ejecutar_bancario(self):
        clientes = self._leer_clientes_de_tabla()
        if not clientes:
            QMessageBox.warning(self, "Sin clientes", "Registre al menos un cliente.")
            return

        self._tabla_estadisticas_bco.setRowCount(0)
        self._gantt_bancario.resetear()

        clientes_ord = sorted(clientes, key=lambda c: c.tiempo_llegada)
        procesos: List[Proceso] = []
        for idx, c in enumerate(clientes_ord, start=1):
            procesos.append(Proceso(
                id_proceso=idx,
                tiempo_llegada=c.tiempo_llegada,
                tiempo_rafaga=c.obtener_tiempo_atencion(),
                prioridad=c.prioridad,
                nombre=c.nombre,
            ))

        mlq = PlanificadorMLQ(
            PlanificadorRoundRobin(2),
            PlanificadorFIFO(),
            PlanificadorSJF(),
        )
        segmentos = mlq.ejecutar([p.clonar() for p in procesos])

        if not segmentos:
            QMessageBox.warning(self, "Aviso", "No se generaron segmentos de ejecución.")
            return

        nombres_unicos = list(dict.fromkeys(s.nombre_proceso for s in segmentos))
        mapa_col = {
            nombre: COLORES_PROCESOS[i % len(COLORES_PROCESOS)]
            for i, nombre in enumerate(nombres_unicos)
        }

        self._gantt_bancario.inicializar(segmentos, mapa_col)

        for seg in sorted(segmentos, key=lambda s: s.inicio):
            for t in range(seg.inicio, seg.fin + 1):
                self._gantt_bancario.avanzar_tick(
                    seg.nombre_proceso, t, mapa_col.get(seg.nombre_proceso, QColor(128, 128, 128))
                )

        self._mostrar_estadisticas_bancario(segmentos, clientes_ord)
        guardar_clientes_atendidos(clientes_ord, calcular_estadisticas_desde_segmentos(segmentos))

    # ── LECTURA DE TABLAS ─────────────────────────────────────────────────────

    def _leer_procesos_de_tabla(self) -> List[Proceso]:
        procesos = []
        for fila in range(self._tabla_procesos.rowCount()):
            try:
                nombre    = self._tabla_procesos.item(fila, 0).text().strip()
                llegada   = int(self._tabla_procesos.item(fila, 1).text())
                rafaga    = int(self._tabla_procesos.item(fila, 2).text())
                prioridad = int(self._tabla_procesos.item(fila, 3).text())
                if rafaga <= 0:
                    continue
                id_proceso = fila + 1
                procesos.append(Proceso(
                    id_proceso=id_proceso,
                    tiempo_llegada=llegada,
                    tiempo_rafaga=rafaga,
                    prioridad=prioridad,
                    nombre=nombre or f"P{id_proceso}",
                ))
            except (AttributeError, ValueError):
                continue
        return procesos

    def _leer_clientes_de_tabla(self) -> List[Cliente]:
        clientes = []
        for fila in range(self._tabla_clientes.rowCount()):
            try:
                nombre  = self._tabla_clientes.item(fila, 0).text().strip()
                tipo    = self._tabla_clientes.item(fila, 1).text().strip().upper()
                llegada = int(self._tabla_clientes.item(fila, 2).text())
                if not nombre or not tipo:
                    continue
                clientes.append(Cliente(nombre, tipo, llegada))
            except (AttributeError, ValueError):
                continue
        return clientes

    # ── PLANIFICADORES ────────────────────────────────────────────────────────

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
                self._crear_planificador_cola(self._combo_cola_alta,  self._spin_quantum_alta),
                self._crear_planificador_cola(self._combo_cola_media, self._spin_quantum_media),
                self._crear_planificador_cola(self._combo_cola_baja,  self._spin_quantum_baja),
            )
        return PlanificadorFIFO()

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

    # ── MOSTRAR ESTADÍSTICAS ──────────────────────────────────────────────────

    def _mostrar_estadisticas_simulador(self):
        if not self._segmentos_actuales:
            return
        estadisticas = calcular_estadisticas_desde_segmentos(self._segmentos_actuales)
        resumen = calcular_resumen_global(self._segmentos_actuales)

        self._tabla_estadisticas_sim.setRowCount(0)
        for est in estadisticas:
            agregar_fila_tabla(self._tabla_estadisticas_sim, [
                est["nombre"],
                tick_a_hora(est["llegada"]),
                tick_a_hora(est["fin"]),
                tick_a_duracion(est["espera"]),
                tick_a_duracion(est["retorno"]),
            ])

        self._actualizar_chip("prom_espera_sim",
                              tick_a_duracion(resumen["promedio_espera"]))
        self._actualizar_chip("prom_retorno_sim",
                              tick_a_duracion(resumen["promedio_retorno"]))
        self._actualizar_chip("uso_cpu_sim", f"{resumen['uso_cpu']:.1f}%")

    def _mostrar_estadisticas_bancario(self, segmentos: List[SegmentoEjecucion],
                                        clientes: List[Cliente]):
        estadisticas = calcular_estadisticas_desde_segmentos(segmentos)
        resumen = calcular_resumen_global(segmentos)
        mapa_tipos = {c.nombre: c.tipo for c in clientes}

        self._tabla_estadisticas_bco.setRowCount(0)
        for est in estadisticas:
            agregar_fila_tabla(self._tabla_estadisticas_bco, [
                est["nombre"], mapa_tipos.get(est["nombre"], "—"),
                est["llegada"], est["fin"], est["espera"], est["retorno"],
            ])

        self._actualizar_chip("prom_espera_bco",  f"{resumen['promedio_espera']:.2f}")
        self._actualizar_chip("prom_retorno_bco", f"{resumen['promedio_retorno']:.2f}")
        self._actualizar_chip("uso_cpu_bco",      f"{resumen['uso_cpu']:.1f}%")

    # ── UTILIDADES DE INTERFAZ ────────────────────────────────────────────────

    def _crear_chip_metrica(self, etiqueta: str, valor: str) -> QWidget:
        chip = QWidget()
        chip.setFixedHeight(28)
        chip.setStyleSheet(f"""
            background-color: {a_css(COLOR_SUPERFICIE_ELEV)};
            border: 1px solid {a_css(COLOR_BORDE)};
            border-radius: 6px;
        """)
        h = QHBoxLayout(chip)
        h.setContentsMargins(10, 4, 10, 4)
        h.setSpacing(5)

        lbl_et = QLabel(etiqueta + ":")
        lbl_et.setFont(QFont("Segoe UI", 7))
        lbl_et.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")

        lbl_val = QLabel(valor)
        f_val = QFont("Segoe UI", 8)
        f_val.setBold(True)
        lbl_val.setFont(f_val)
        lbl_val.setStyleSheet(f"color: {a_css(COLOR_ACENTO)}; background: transparent;")

        h.addWidget(lbl_et)
        h.addWidget(lbl_val)

        # Guardamos el label del valor para poder actualizar el texto
        chip._lbl_valor = lbl_val
        chip._etiqueta  = etiqueta

        # Registrar el chip para actualizaciones posteriores
        if not hasattr(self, "_chips"):
            self._chips = {}
        return chip

    def _actualizar_chip(self, clave: str, valor: str):
        mapa = {
            "prom_espera_sim":  self._lbl_prom_espera_sim,
            "prom_retorno_sim": self._lbl_prom_retorno_sim,
            "uso_cpu_sim":      self._lbl_uso_cpu_sim,
        }
        chip = mapa.get(clave)
        if chip and hasattr(chip, "_lbl_valor"):
            chip._lbl_valor.setText(valor)

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
                val = float(item.text().replace("%", ""))
            except ValueError:
                continue
            if mejor_valor is None:
                mejor_valor = val
                mejor_fila = fila
            elif mayor_es_mejor and val > mejor_valor:
                mejor_valor = val
                mejor_fila = fila
            elif not mayor_es_mejor and val < mejor_valor:
                mejor_valor = val
                mejor_fila = fila

        item = tabla.item(mejor_fila, col_idx)
        if item is not None:
            item.setBackground(_COLOR_MEJOR_BG)
            item.setForeground(_COLOR_MEJOR_FG)
