"""
Panel del Centro de Emergencias Médicas.

Estructura:
    Izquierda (380px): lista de pacientes + configuración de colas + controles
    Derecha (tabs):    Simulación | Dashboard | Estadísticas | Historial
"""

from typing import Dict, List, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QScrollArea,
    QLabel, QPushButton, QFrame, QComboBox, QSpinBox,
    QTableWidgetItem, QTabWidget, QTextEdit, QFileDialog,
    QMessageBox, QProgressBar, QGridLayout, QSizePolicy,
    QHeaderView, QLineEdit,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QTextCursor

from interfaz.tema import (
    COLOR_FONDO_PRIMARIO, COLOR_SUPERFICIE, COLOR_SUPERFICIE_ALT,
    COLOR_SUPERFICIE_ELEV, COLOR_BORDE, COLOR_BORDE_FUERTE,
    COLOR_ACENTO, COLOR_ACENTO_BRILLANTE, COLOR_ACENTO_CYAN,
    COLOR_TEXTO_PRIMARIO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_MUTED,
    COLOR_EXITO, COLOR_PELIGRO, COLOR_ADVERTENCIA, COLOR_PURPURA,
    COLORES_PROCESOS,
    fuente_h1, fuente_h2, fuente_base, fuente_pequena, fuente_seccion,
    fuente_mono, fuente_mono_grande,
    css_boton, a_css, aclarar, oscurecer,
)
from interfaz.controles_personalizados import (
    TarjetaTema, ItemNavegacion, crear_boton, crear_tabla,
    agregar_fila_tabla, crear_etiqueta_campo, crear_spinbox, crear_combo,
)
from interfaz.vista_gantt import VistaGantt, tick_a_hora, tick_a_duracion
from interfaz.dialogo_paciente import DialogoPaciente

from modelos.paciente import (
    Paciente, TIPOS_VALIDOS, COLA_POR_TIPO, ETIQUETA_PRIORIDAD,
    PRIORIDAD_SCHEDULER,
)
from modelos.segmento_ejecucion import SegmentoEjecucion
from modelos.estadisticas import calcular_estadisticas_desde_segmentos, calcular_resumen_global

from planificadores.planificador_emergencias import PlanificadorEmergencias
from planificadores.planificador_fifo import PlanificadorFIFO
from planificadores.planificador_sjf import PlanificadorSJF
from planificadores.planificador_round_robin import PlanificadorRoundRobin

from servicios.cargador_pacientes import cargar_pacientes_desde_archivo
from servicios.gestor_pacientes import (
    guardar_pacientes_atendidos, cargar_historial, limpiar_historial,
)

# ── Colores por tipo de paciente ──────────────────────────────────────────────
_COLOR_TIPO: Dict[str, QColor] = {
    "ROJO":        QColor(239,  68,  68),
    "AMARILLO":    QColor(245, 158,  11),
    "EMBARAZADA":  QColor(236,  72, 153),
    "VERDE":       QColor( 34, 197,  94),
    "CITA":        QColor( 59, 130, 246),
    "SEGUIMIENTO": QColor( 99, 102, 241),
}

_BTN_ACCION  = COLOR_EXITO
_BTN_PELIGRO = COLOR_PELIGRO
_BTN_NEUTRO  = COLOR_ACENTO
_BTN_PAUSA   = QColor(180, 110, 0)
_BTN_RESET   = COLOR_PURPURA


class PanelEmergencias(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pacientes: List[Paciente] = []
        self._segmentos: List[SegmentoEjecucion] = []
        self._mapa_colores: Dict[str, QColor] = {}
        self._simulacion_en_curso = False
        self._modo_paso = False
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick_animacion)
        self._segmentos_pendientes: List[SegmentoEjecucion] = []
        self._indice_seg = 0
        self._tick_en_seg = 0
        self._cambios_contexto = 0
        self._algoritmos_por_tipo: Dict[str, str] = {}

        self._construir_ui()
        self._cargar_demo()

    # ── CONSTRUCCIÓN UI ───────────────────────────────────────────────────────

    def _construir_ui(self):
        self.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {a_css(COLOR_BORDE)}; width: 1px; }}"
        )
        splitter.addWidget(self._panel_izquierdo())
        splitter.addWidget(self._panel_derecho())
        splitter.setSizes([390, 1000])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        layout.addWidget(splitter)

    # ── PANEL IZQUIERDO ───────────────────────────────────────────────────────

    def _panel_izquierdo(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: {a_css(COLOR_SUPERFICIE)}; border: none; }}"
        )

        cont = QWidget()
        cont.setStyleSheet(f"background: {a_css(COLOR_SUPERFICIE)};")
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        # ── Sección: Pacientes ────────────────────────────────────────────────
        lay.addWidget(self._seccion_lbl("PACIENTES REGISTRADOS"))

        tarjeta_pac = TarjetaTema("Lista de pacientes")
        tarjeta_pac.setFixedHeight(248)
        lay_pac = QVBoxLayout(tarjeta_pac)
        lay_pac.setContentsMargins(0, 0, 0, 0)
        lay_pac.setSpacing(0)

        self._tabla_pacientes = crear_tabla(
            ["Tiquete", "Nombre", "Tipo", "Llegada", "Ráfaga"]
        )
        self._tabla_pacientes.setColumnWidth(0, 60)
        self._tabla_pacientes.setColumnWidth(1, 120)
        self._tabla_pacientes.setColumnWidth(2, 80)
        self._tabla_pacientes.setColumnWidth(3, 55)
        lay_pac.addWidget(self._tabla_pacientes)

        sep0 = self._sep_h()
        lay_pac.addWidget(sep0)

        fila_btn0 = QWidget()
        fila_btn0.setFixedHeight(38)
        fila_btn0.setStyleSheet(f"background: {a_css(COLOR_FONDO_PRIMARIO)};")
        hb0 = QHBoxLayout(fila_btn0)
        hb0.setContentsMargins(6, 5, 6, 5)
        hb0.setSpacing(5)

        self._btn_registrar = crear_boton("+ Registrar", _BTN_ACCION, 94, 28)
        self._btn_elim_pac  = crear_boton("Eliminar",    _BTN_PELIGRO, 78, 28)
        self._btn_cargar_txt = crear_boton("Cargar TXT", _BTN_NEUTRO,  90, 28)

        self._btn_registrar.clicked.connect(self._al_registrar)
        self._btn_elim_pac.clicked.connect(self._al_eliminar_paciente)
        self._btn_cargar_txt.clicked.connect(self._al_cargar_txt)

        hb0.addWidget(self._btn_registrar)
        hb0.addWidget(self._btn_elim_pac)
        hb0.addWidget(self._btn_cargar_txt)
        hb0.addStretch()
        lay_pac.addWidget(fila_btn0)
        lay.addWidget(tarjeta_pac)

        # ── Sección: Configuración MLQ ────────────────────────────────────────
        lay.addWidget(self._seccion_lbl("CONFIGURACIÓN MLQ"))

        tarjeta_mlq = TarjetaTema("Algoritmos por cola de prioridad")
        tarjeta_mlq.setFixedHeight(172)
        inner_mlq = QWidget(tarjeta_mlq)
        inner_mlq.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 136)
        inner_mlq.setStyleSheet(f"background: {a_css(COLOR_SUPERFICIE)};")

        lay_mlq = QVBoxLayout(inner_mlq)
        lay_mlq.setContentsMargins(10, 8, 10, 8)
        lay_mlq.setSpacing(6)

        algs = ["FIFO", "SJF", "Round Robin"]

        self._combo_critica  = crear_combo(algs, indice=2)  # RR por defecto
        self._combo_urgente  = crear_combo(algs, indice=0)  # FIFO
        self._combo_normal   = crear_combo(algs, indice=1)  # SJF
        self._spin_q_critica = crear_spinbox(1, 100, 2)
        self._spin_q_urgente = crear_spinbox(1, 100, 2)
        self._spin_q_normal  = crear_spinbox(1, 100, 2)
        self._spin_q_urgente.setVisible(False)
        self._spin_q_normal.setVisible(False)

        self._combo_critica.currentIndexChanged.connect(
            lambda i: self._spin_q_critica.setVisible(i == 2))
        self._combo_urgente.currentIndexChanged.connect(
            lambda i: self._spin_q_urgente.setVisible(i == 2))
        self._combo_normal.currentIndexChanged.connect(
            lambda i: self._spin_q_normal.setVisible(i == 2))

        for lbl_txt, combo, spin, color_dot in [
            ("Crítica (ROJO/AMR):",   self._combo_critica, self._spin_q_critica, "#EF4444"),
            ("Urgente (EMB/VERDE):",  self._combo_urgente, self._spin_q_urgente, "#22C55E"),
            ("Normal (CITA/SEG):",    self._combo_normal,  self._spin_q_normal,  "#6366F1"),
        ]:
            fila = QHBoxLayout()
            dot = QLabel("●")
            dot.setFont(QFont("Segoe UI", 9))
            dot.setStyleSheet(f"color: {color_dot}; background: transparent;")
            dot.setFixedWidth(14)
            lbl = crear_etiqueta_campo(lbl_txt)
            lbl.setFixedWidth(140)
            combo.setFixedWidth(110)
            spin.setFixedWidth(58)
            fila.addWidget(dot)
            fila.addWidget(lbl)
            fila.addWidget(combo)
            fila.addWidget(spin)
            fila.addStretch()
            lay_mlq.addLayout(fila)

        lay.addWidget(tarjeta_mlq)

        # ── Sección: Control ──────────────────────────────────────────────────
        lay.addWidget(self._seccion_lbl("CONTROL DE SIMULACIÓN"))

        tarjeta_ctrl = TarjetaTema("Ejecución")
        tarjeta_ctrl.setFixedHeight(128)
        inner_ctrl = QWidget(tarjeta_ctrl)
        inner_ctrl.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 400, 92)
        inner_ctrl.setStyleSheet(f"background: {a_css(COLOR_SUPERFICIE)};")

        lay_ctrl = QVBoxLayout(inner_ctrl)
        lay_ctrl.setContentsMargins(8, 8, 8, 8)
        lay_ctrl.setSpacing(8)

        fila_btn_ctrl = QHBoxLayout()
        self._btn_ejecutar = crear_boton("▶  Ejecutar",  _BTN_ACCION,  98, 32)
        self._btn_pausar   = crear_boton("⏸  Pausar",   _BTN_PAUSA,   84, 32)
        self._btn_paso     = crear_boton("⏭  Paso",     _BTN_NEUTRO,  74, 32)
        self._btn_reset    = crear_boton("↺  Reset",    _BTN_RESET,   72, 32)
        self._btn_pausar.setEnabled(False)
        self._btn_paso.setEnabled(False)

        self._btn_ejecutar.clicked.connect(self._al_ejecutar)
        self._btn_pausar.clicked.connect(self._al_pausar)
        self._btn_paso.clicked.connect(self._al_paso)
        self._btn_reset.clicked.connect(self._al_reset)

        fila_btn_ctrl.addWidget(self._btn_ejecutar)
        fila_btn_ctrl.addWidget(self._btn_pausar)
        fila_btn_ctrl.addWidget(self._btn_paso)
        fila_btn_ctrl.addWidget(self._btn_reset)
        fila_btn_ctrl.addStretch()
        lay_ctrl.addLayout(fila_btn_ctrl)

        fila_vel = QHBoxLayout()
        lbl_vel = crear_etiqueta_campo("Velocidad (ms):")
        lbl_vel.setFixedWidth(112)
        self._spin_vel = crear_spinbox(50, 3000, 600)
        self._spin_vel.setSingleStep(50)
        self._spin_vel.setFixedWidth(86)
        fila_vel.addWidget(lbl_vel)
        fila_vel.addWidget(self._spin_vel)
        fila_vel.addStretch()
        lay_ctrl.addLayout(fila_vel)

        lay.addWidget(tarjeta_ctrl)
        lay.addStretch()

        scroll.setWidget(cont)
        return scroll

    # ── PANEL DERECHO ─────────────────────────────────────────────────────────

    def _panel_derecho(self) -> QTabWidget:
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {a_css(COLOR_FONDO_PRIMARIO)};
            }}
            QTabBar::tab {{
                background: {a_css(COLOR_SUPERFICIE)};
                color: {a_css(COLOR_TEXTO_MUTED)};
                border: none;
                border-bottom: 2px solid {a_css(COLOR_BORDE)};
                padding: 8px 18px;
                font-size: 9pt;
                font-family: "Segoe UI";
            }}
            QTabBar::tab:selected {{
                color: {a_css(COLOR_ACENTO)};
                border-bottom: 2px solid {a_css(COLOR_ACENTO)};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                color: {a_css(COLOR_TEXTO_PRIMARIO)};
                background: {a_css(COLOR_SUPERFICIE_ELEV)};
            }}
        """)

        self._tabs.addTab(self._tab_simulacion(),  "Simulación")
        self._tabs.addTab(self._tab_dashboard(),   "Dashboard")
        self._tabs.addTab(self._tab_estadisticas(), "Estadísticas")
        self._tabs.addTab(self._tab_historial(),   "Historial")

        self._tabs.currentChanged.connect(self._al_cambiar_tab)
        return self._tabs

    # ── TAB SIMULACIÓN ────────────────────────────────────────────────────────

    def _tab_simulacion(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {a_css(COLOR_FONDO_PRIMARIO)};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.setStyleSheet(
            f"QSplitter::handle {{ background: {a_css(COLOR_BORDE)}; height: 1px; }}"
        )

        # Gantt
        tarjeta_gantt = TarjetaTema("Diagrama de Gantt — Centro de Emergencias")
        lay_gantt = QVBoxLayout(tarjeta_gantt)
        lay_gantt.setContentsMargins(0, 0, 0, 0)
        lay_gantt.setSpacing(0)

        # Barra de estado (reloj + progreso)
        barra_est = QWidget()
        barra_est.setFixedHeight(38)
        barra_est.setStyleSheet(f"""
            background: {a_css(COLOR_FONDO_PRIMARIO)};
            border-bottom: 1px solid {a_css(COLOR_BORDE)};
        """)
        b_lay = QHBoxLayout(barra_est)
        b_lay.setContentsMargins(12, 8, 12, 8)
        b_lay.setSpacing(12)

        self._lbl_reloj = QLabel("07:00")
        f_reloj = QFont("Consolas", 11)
        f_reloj.setBold(True)
        self._lbl_reloj.setFont(f_reloj)
        self._lbl_reloj.setFixedWidth(58)
        self._lbl_reloj.setStyleSheet(
            f"color: {a_css(COLOR_ACENTO)}; background: transparent;"
        )

        self._barra_prog = QProgressBar()
        self._barra_prog.setTextVisible(False)
        self._barra_prog.setFixedHeight(10)
        self._barra_prog.setStyleSheet(f"""
            QProgressBar {{ background: {a_css(COLOR_SUPERFICIE_ELEV)};
                           border: none; border-radius: 5px; }}
            QProgressBar::chunk {{ background: {a_css(COLOR_ACENTO)};
                                   border-radius: 5px; }}
        """)

        self._lbl_proceso_actual = QLabel("Sin simulación activa")
        self._lbl_proceso_actual.setFont(fuente_pequena())
        self._lbl_proceso_actual.setStyleSheet(
            f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;"
        )

        b_lay.addWidget(self._lbl_reloj)
        b_lay.addWidget(self._barra_prog, 1)
        b_lay.addWidget(self._lbl_proceso_actual)
        lay_gantt.addWidget(barra_est)

        self._gantt = VistaGantt()
        lay_gantt.addWidget(self._gantt)
        splitter_v.addWidget(tarjeta_gantt)

        # Log paso a paso
        tarjeta_log = TarjetaTema("Secuencia de ejecución — log paso a paso")
        lay_log = QVBoxLayout(tarjeta_log)
        lay_log.setContentsMargins(0, 0, 0, 0)

        barra_log = QWidget()
        barra_log.setFixedHeight(34)
        barra_log.setStyleSheet(f"background: {a_css(COLOR_FONDO_PRIMARIO)}; border-bottom: 1px solid {a_css(COLOR_BORDE)};")
        bh = QHBoxLayout(barra_log)
        bh.setContentsMargins(10, 6, 10, 6)
        btn_limpiar_log = QPushButton("Limpiar log")
        btn_limpiar_log.setFixedHeight(22)
        btn_limpiar_log.setFont(QFont("Segoe UI", 7))
        btn_limpiar_log.setStyleSheet(f"""
            QPushButton {{ background: {a_css(COLOR_SUPERFICIE_ELEV)};
                          color: {a_css(COLOR_TEXTO_SECUNDARIO)};
                          border: 1px solid {a_css(COLOR_BORDE)};
                          border-radius: 4px; padding: 0 8px; }}
            QPushButton:hover {{ background: {a_css(COLOR_BORDE)}; }}
        """)
        btn_limpiar_log.clicked.connect(lambda: self._txt_log.clear())
        bh.addStretch()
        bh.addWidget(btn_limpiar_log)
        lay_log.addWidget(barra_log)

        self._txt_log = QTextEdit()
        self._txt_log.setReadOnly(True)
        self._txt_log.setFont(QFont("Consolas", 8))
        self._txt_log.setStyleSheet(f"""
            QTextEdit {{
                background: {a_css(COLOR_SUPERFICIE)};
                color: {a_css(COLOR_TEXTO_PRIMARIO)};
                border: none;
                padding: 8px;
            }}
        """)
        lay_log.addWidget(self._txt_log)
        splitter_v.addWidget(tarjeta_log)

        splitter_v.setSizes([420, 180])
        lay.addWidget(splitter_v)
        return w

    # ── TAB DASHBOARD ─────────────────────────────────────────────────────────

    def _tab_dashboard(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ background: {a_css(COLOR_FONDO_PRIMARIO)}; border: none; }}")

        cont = QWidget()
        cont.setStyleSheet(f"background: {a_css(COLOR_FONDO_PRIMARIO)};")
        lay = QVBoxLayout(cont)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(14)

        # Fila 1: métricas de estado
        fila1 = QHBoxLayout()
        fila1.setSpacing(10)
        self._card_espera      = self._metrica_card("En espera",    "0", "#3B82F6")
        self._card_atencion    = self._metrica_card("En atención",  "0", "#F59E0B")
        self._card_finalizados = self._metrica_card("Finalizados",  "0", "#22C55E")
        self._card_cancelados  = self._metrica_card("Cancelados",   "0", "#EF4444")
        for c in [self._card_espera, self._card_atencion, self._card_finalizados, self._card_cancelados]:
            fila1.addWidget(c)
        lay.addLayout(fila1)

        # Fila 2: métricas de rendimiento
        fila2 = QHBoxLayout()
        fila2.setSpacing(10)
        self._card_prom_espera  = self._metrica_card("Prom. espera",  "—", "#6366F1")
        self._card_prom_retorno = self._metrica_card("Prom. retorno", "—", "#6366F1")
        self._card_uso_cpu      = self._metrica_card("Uso CPU",       "—", "#0C8599")
        self._card_cambios_ctx  = self._metrica_card("Cambios ctx.",  "0", "#EC4899")
        for c in [self._card_prom_espera, self._card_prom_retorno, self._card_uso_cpu, self._card_cambios_ctx]:
            fila2.addWidget(c)
        lay.addLayout(fila2)

        # Tabla: estado de colas por tipo
        tarjeta_cola = TarjetaTema("Estado de colas por tipo de paciente")
        lay_cola = QVBoxLayout(tarjeta_cola)
        lay_cola.setContentsMargins(0, 0, 0, 0)

        self._tabla_colas = crear_tabla(["Tipo", "Cola", "Prioridad", "Registrados", "Algoritmo"])
        self._tabla_colas.setFixedHeight(230)
        lay_cola.addWidget(self._tabla_colas)
        lay.addWidget(tarjeta_cola)

        # Próximo paciente recomendado
        tarjeta_prox = TarjetaTema("Estado actual del sistema")
        tarjeta_prox.setFixedHeight(90)
        inner_prox = QWidget(tarjeta_prox)
        inner_prox.setGeometry(0, TarjetaTema.ALTURA_CABECERA, 1200, 54)
        inner_prox.setStyleSheet(f"background: {a_css(COLOR_SUPERFICIE)};")
        hx = QHBoxLayout(inner_prox)
        hx.setContentsMargins(14, 10, 14, 10)
        hx.setSpacing(24)

        self._lbl_estado_sim = self._lbl_estado_chip("Estado:", "Sin simular", "#8890A8")
        self._lbl_sig_pac    = self._lbl_estado_chip("Próximo paciente:", "—", "#3B82F6")
        self._lbl_algoritmo  = self._lbl_estado_chip("Algoritmo activo:", "—", "#22C55E")
        for lbl in [self._lbl_estado_sim, self._lbl_sig_pac, self._lbl_algoritmo]:
            hx.addWidget(lbl)
        hx.addStretch()
        lay.addWidget(tarjeta_prox)

        lay.addStretch()
        scroll.setWidget(cont)
        return scroll

    # ── TAB ESTADÍSTICAS ──────────────────────────────────────────────────────

    def _tab_estadisticas(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {a_css(COLOR_FONDO_PRIMARIO)};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        tarjeta_st = TarjetaTema("Estadísticas por paciente")
        lay_st = QVBoxLayout(tarjeta_st)
        lay_st.setContentsMargins(0, 0, 0, 0)
        lay_st.setSpacing(0)

        self._tabla_stats = crear_tabla(
            ["Tiquete", "Nombre", "Tipo", "Cola", "H. Llegada",
             "H. Fin", "T. Espera", "T. Retorno", "Algoritmo"]
        )
        lay_st.addWidget(self._tabla_stats)
        lay.addWidget(tarjeta_st, 3)

        # Resumen por tipo
        tarjeta_res = TarjetaTema("Resumen por tipo de paciente")
        lay_res = QVBoxLayout(tarjeta_res)
        lay_res.setContentsMargins(0, 0, 0, 0)
        self._tabla_resumen_tipo = crear_tabla(
            ["Tipo", "Cola", "Atendidos", "Prom. Espera", "Prom. Retorno"]
        )
        self._tabla_resumen_tipo.setFixedHeight(220)
        lay_res.addWidget(self._tabla_resumen_tipo)
        lay.addWidget(tarjeta_res, 2)

        # Barra de métricas globales
        barra_gl = self._barra_global()
        lay.addWidget(barra_gl)
        return w

    # ── TAB HISTORIAL ─────────────────────────────────────────────────────────

    def _tab_historial(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {a_css(COLOR_FONDO_PRIMARIO)};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        # Barra de búsqueda y filtros
        barra_busq = QWidget()
        barra_busq.setFixedHeight(42)
        barra_busq.setStyleSheet(
            f"background: {a_css(COLOR_SUPERFICIE)}; border: 1px solid {a_css(COLOR_BORDE)}; border-radius: 6px;"
        )
        hb = QHBoxLayout(barra_busq)
        hb.setContentsMargins(12, 8, 12, 8)
        hb.setSpacing(10)

        lbl_busq = QLabel("Buscar:")
        lbl_busq.setFont(fuente_base())
        lbl_busq.setStyleSheet(f"color: {a_css(COLOR_TEXTO_SECUNDARIO)}; background: transparent;")

        self._txt_busq = QLineEdit()
        self._txt_busq.setPlaceholderText("ID, nombre o tiquete...")
        self._txt_busq.setFixedHeight(26)
        self._txt_busq.setStyleSheet(f"""
            QLineEdit {{ background: {a_css(COLOR_SUPERFICIE_ELEV)};
                        color: {a_css(COLOR_TEXTO_PRIMARIO)};
                        border: 1.5px solid {a_css(COLOR_BORDE)};
                        border-radius: 4px; padding: 2px 8px; }}
            QLineEdit:focus {{ border-color: {a_css(COLOR_ACENTO)}; }}
        """)
        self._txt_busq.textChanged.connect(self._filtrar_historial)

        self._combo_filtro_tipo = crear_combo(["Todos"] + TIPOS_VALIDOS, indice=0)
        self._combo_filtro_tipo.setFixedWidth(130)
        self._combo_filtro_tipo.currentTextChanged.connect(self._filtrar_historial)

        btn_recargar = crear_boton("Recargar", _BTN_NEUTRO, 88, 26)
        btn_recargar.clicked.connect(self._cargar_historial_tabla)

        btn_limpiar_h = crear_boton("Limpiar historial", _BTN_PELIGRO, 140, 26)
        btn_limpiar_h.clicked.connect(self._limpiar_historial)

        hb.addWidget(lbl_busq)
        hb.addWidget(self._txt_busq, 1)
        hb.addWidget(self._combo_filtro_tipo)
        hb.addWidget(btn_recargar)
        hb.addWidget(btn_limpiar_h)
        lay.addWidget(barra_busq)

        tarjeta_hist = TarjetaTema("Historial de pacientes atendidos")
        lay_hist = QVBoxLayout(tarjeta_hist)
        lay_hist.setContentsMargins(0, 0, 0, 0)
        self._tabla_historial = crear_tabla(
            ["Tiquete", "Nombre", "Tipo", "Cola", "Motivo",
             "Espera", "Retorno", "Algoritmo", "Fecha"]
        )
        lay_hist.addWidget(self._tabla_historial)
        lay.addWidget(tarjeta_hist)

        self._registros_historial: List[dict] = []
        return w

    # ── DATOS DE DEMO ─────────────────────────────────────────────────────────

    def _cargar_demo(self):
        demo = [
            ("P001", "Ana Solano",       "ROJO",        "Accidente de tránsito",      0, 8),
            ("P002", "Carlos Mora",      "VERDE",        "Herida leve",                1, 4),
            ("P003", "María Vargas",     "EMBARAZADA",   "Parto",                      2, 6),
            ("P004", "Luis Pérez",       "AMARILLO",     "Desmayo",                    3, 7),
            ("P005", "Pedro García",     "CITA",         "Cita de control",            5, 3),
            ("P006", "Sofía Torres",     "SEGUIMIENTO",  "Seguimiento postoperatorio", 6, 2),
        ]
        for id_p, nombre, tipo, motivo, llegada, rafaga in demo:
            pac = Paciente(id_p, nombre, tipo, motivo, llegada, rafaga)
            self._pacientes.append(pac)
            self._agregar_fila_paciente(pac)
        self._actualizar_dashboard()

    # ── EVENTOS ───────────────────────────────────────────────────────────────

    def _al_registrar(self):
        dlg = DialogoPaciente(self)
        if dlg.exec() == DialogoPaciente.Accepted:
            pac = Paciente(
                id_paciente=dlg.id_paciente,
                nombre=dlg.nombre,
                tipo=dlg.tipo,
                motivo=dlg.motivo,
                tiempo_llegada=dlg.llegada,
                tiempo_rafaga=dlg.rafaga,
                identificacion=dlg.identificacion,
                edad=dlg.edad,
                telefono=dlg.telefono,
                numero_tiquete=dlg.tiquete,
            )
            self._pacientes.append(pac)
            self._agregar_fila_paciente(pac)
            self._actualizar_dashboard()

    def _al_eliminar_paciente(self):
        filas = sorted(
            set(item.row() for item in self._tabla_pacientes.selectedItems()),
            reverse=True,
        )
        for f in filas:
            id_item = self._tabla_pacientes.item(f, 0)
            if id_item:
                tiquete = id_item.text()
                self._pacientes = [p for p in self._pacientes if p.numero_tiquete != tiquete]
            self._tabla_pacientes.removeRow(f)
        self._actualizar_dashboard()

    def _al_cargar_txt(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Cargar pacientes desde TXT", "",
            "Archivos de texto (*.txt);;Todos los archivos (*.*)"
        )
        if not ruta:
            return
        pacientes, advertencias = cargar_pacientes_desde_archivo(ruta)
        if advertencias:
            QMessageBox.warning(self, "Advertencias al cargar", "\n".join(advertencias))
        if not pacientes:
            QMessageBox.warning(self, "Sin datos",
                                "No se encontraron pacientes válidos en el archivo.")
            return

        for pac in pacientes:
            # Evitar duplicados por ID
            if any(p.id_paciente == pac.id_paciente for p in self._pacientes):
                continue
            self._pacientes.append(pac)
            self._agregar_fila_paciente(pac)

        QMessageBox.information(self, "Carga completada",
                                f"Se cargaron {len(pacientes)} paciente(s) desde el archivo.")
        self._actualizar_dashboard()

    def _al_ejecutar(self):
        if self._simulacion_en_curso:
            return
        if not self._pacientes:
            QMessageBox.warning(self, "Sin pacientes",
                                "Registre al menos un paciente antes de ejecutar.")
            return

        self._al_reset()

        # Construir planificador de emergencias
        planificador = PlanificadorEmergencias(
            self._crear_sub_planificador(self._combo_critica, self._spin_q_critica),
            self._crear_sub_planificador(self._combo_urgente, self._spin_q_urgente),
            self._crear_sub_planificador(self._combo_normal,  self._spin_q_normal),
        )

        # Guardar descripción de algoritmos por tipo de cola
        self._algoritmos_por_tipo = {
            "ROJO":        self._combo_critica.currentText(),
            "AMARILLO":    self._combo_critica.currentText(),
            "EMBARAZADA":  self._combo_urgente.currentText(),
            "VERDE":       self._combo_urgente.currentText(),
            "CITA":        self._combo_normal.currentText(),
            "SEGUIMIENTO": self._combo_normal.currentText(),
        }

        # Convertir pacientes a procesos
        copias_proceso = []
        for idx, pac in enumerate(self._pacientes, start=1):
            proc = pac.clonar().a_proceso(idx)
            copias_proceso.append(proc)

        self._segmentos = planificador.ejecutar(copias_proceso)

        if not self._segmentos:
            QMessageBox.warning(self, "Error", "No se generaron segmentos de ejecución.")
            return

        # Mapa de colores (ID paciente → color del tipo)
        id_a_tipo = {p.id_paciente: p.tipo for p in self._pacientes}
        nombres_unicos = list(dict.fromkeys(s.nombre_proceso for s in self._segmentos))
        self._mapa_colores = {
            nombre: _COLOR_TIPO.get(id_a_tipo.get(nombre, "CITA"), QColor(128, 128, 128))
            for nombre in nombres_unicos
        }

        self._gantt.inicializar(self._segmentos, self._mapa_colores)
        self._barra_prog.setMaximum(max(s.fin for s in self._segmentos))
        self._barra_prog.setValue(0)

        self._segmentos_pendientes = sorted(self._segmentos, key=lambda s: s.inicio)
        self._indice_seg = 0
        self._tick_en_seg = 0
        self._cambios_contexto = 0
        self._simulacion_en_curso = True
        self._modo_paso = False

        self._btn_ejecutar.setEnabled(False)
        self._btn_pausar.setEnabled(True)
        self._btn_paso.setEnabled(True)

        self._log("=" * 60)
        self._log(f"  INICIO DE SIMULACIÓN — {datetime.now().strftime('%H:%M:%S')}")
        self._log(f"  Pacientes: {len(self._pacientes)}  |  Segmentos: {len(self._segmentos)}")
        self._log("=" * 60)

        # Cambiar a tab Simulación
        self._tabs.setCurrentIndex(0)

        self._timer.start(self._spin_vel.value())

    def _al_pausar(self):
        if self._simulacion_en_curso:
            self._timer.stop()
            self._simulacion_en_curso = False
            self._btn_pausar.setText("▶ Continuar")
            self._btn_pausar.setStyleSheet(css_boton(COLOR_ACENTO))
            self._btn_ejecutar.setEnabled(True)
            self._modo_paso = True
            self._log(f"[{self._lbl_reloj.text()}] ⏸ Simulación pausada.")
        else:
            self._simulacion_en_curso = True
            self._modo_paso = False
            self._btn_pausar.setText("⏸  Pausar")
            self._btn_pausar.setStyleSheet(css_boton(_BTN_PAUSA))
            self._btn_ejecutar.setEnabled(False)
            self._log(f"[continuando...] ▶")
            self._timer.start(self._spin_vel.value())

    def _al_paso(self):
        if self._simulacion_en_curso:
            return
        if self._indice_seg < len(self._segmentos_pendientes):
            self._modo_paso = True
            self._ejecutar_tick()

    def _al_reset(self):
        self._timer.stop()
        self._simulacion_en_curso = False
        self._modo_paso = False
        self._btn_ejecutar.setEnabled(True)
        self._btn_pausar.setEnabled(False)
        self._btn_paso.setEnabled(False)
        self._btn_pausar.setText("⏸  Pausar")
        self._btn_pausar.setStyleSheet(css_boton(_BTN_PAUSA))
        self._lbl_reloj.setText("07:00")
        self._barra_prog.setValue(0)
        self._lbl_proceso_actual.setText("Sin simulación activa")
        self._gantt.resetear()
        self._tabla_stats.setRowCount(0)
        self._tabla_resumen_tipo.setRowCount(0)
        self._actualizar_cards_dashboard(0, 0, 0, 0, "—", "—", "—", 0)
        self._lbl_estado_sim.findChild(QLabel, "_valor").setText("Sin simular") if self._lbl_estado_sim.findChild(QLabel, "_valor") else None

    # ── ANIMACIÓN ─────────────────────────────────────────────────────────────

    def _tick_animacion(self):
        self._ejecutar_tick()
        # Ajustar velocidad dinámica
        nuevo = self._spin_vel.value()
        if self._timer.interval() != nuevo:
            self._timer.setInterval(nuevo)

    def _ejecutar_tick(self):
        if self._indice_seg >= len(self._segmentos_pendientes):
            self._timer.stop()
            self._simulacion_en_curso = False
            self._btn_ejecutar.setEnabled(True)
            self._btn_pausar.setEnabled(False)
            self._btn_paso.setEnabled(False)
            self._finalizar_simulacion()
            return

        seg = self._segmentos_pendientes[self._indice_seg]
        t_fin = seg.inicio + self._tick_en_seg + 1
        color = self._mapa_colores.get(seg.nombre_proceso, QColor(128, 128, 128))

        # Log al inicio de cada nuevo segmento
        if self._tick_en_seg == 0:
            pac = self._buscar_paciente_por_id(seg.nombre_proceso)
            nombre_disp = pac.nombre_corto if pac else seg.nombre_proceso
            tipo_disp   = pac.tipo if pac else "?"
            cola_disp   = COLA_POR_TIPO.get(tipo_disp, "?")
            alg_disp    = self._algoritmos_por_tipo.get(tipo_disp, "?")
            self._log(
                f"[t={seg.inicio:>3}] {seg.nombre_proceso} ({nombre_disp} / {tipo_disp}) "
                f"inicia en Cola {cola_disp} via {alg_disp}"
            )
            self._cambios_contexto += 1
            self._actualizar_chip_estado(
                f"En atención: {seg.nombre_proceso} ({nombre_disp})", alg_disp
            )

        self._gantt.avanzar_tick(seg.nombre_proceso, t_fin, color)
        self._lbl_reloj.setText(tick_a_hora(t_fin))
        self._barra_prog.setValue(min(t_fin, self._barra_prog.maximum()))

        # Nombre corto del paciente en la barra de estado
        pac = self._buscar_paciente_por_id(seg.nombre_proceso)
        nombre_disp = pac.nombre_corto if pac else seg.nombre_proceso
        self._lbl_proceso_actual.setText(
            f"Atendiendo: {seg.nombre_proceso} — {nombre_disp}  ({tick_a_hora(t_fin)})"
        )

        self._tick_en_seg += 1
        if self._tick_en_seg >= (seg.fin - seg.inicio):
            # Segmento completado
            pac2 = self._buscar_paciente_por_id(seg.nombre_proceso)
            nom2 = pac2.nombre_corto if pac2 else seg.nombre_proceso
            self._log(f"[t={seg.fin:>3}] {seg.nombre_proceso} ({nom2}) — segmento finalizado")
            self._indice_seg += 1
            self._tick_en_seg = 0

        self._actualizar_dashboard_live()

    def _finalizar_simulacion(self):
        self._log("")
        self._log("=" * 60)
        self._log(f"  FIN DE SIMULACIÓN — {datetime.now().strftime('%H:%M:%S')}")
        self._log(f"  Cambios de contexto: {self._cambios_contexto}")
        self._log("=" * 60)

        self._mostrar_estadisticas()
        self._guardar_en_historial()
        self._actualizar_dashboard()

    def _mostrar_estadisticas(self):
        if not self._segmentos:
            return
        estadisticas = calcular_estadisticas_desde_segmentos(self._segmentos)
        resumen = calcular_resumen_global(self._segmentos)

        id_a_pac = {p.id_paciente: p for p in self._pacientes}
        self._tabla_stats.setRowCount(0)

        for est in estadisticas:
            pac = id_a_pac.get(est["nombre"])
            tiquete = pac.numero_tiquete if pac else "—"
            nombre  = pac.nombre_corto if pac else est["nombre"]
            tipo    = pac.tipo if pac else "?"
            cola    = COLA_POR_TIPO.get(tipo, "?")
            alg     = self._algoritmos_por_tipo.get(tipo, "?")
            agregar_fila_tabla(self._tabla_stats, [
                tiquete, nombre, tipo, cola,
                tick_a_hora(est["llegada"]),
                tick_a_hora(est["fin"]),
                tick_a_duracion(est["espera"]),
                tick_a_duracion(est["retorno"]),
                alg,
            ])

        # Resumen por tipo
        self._tabla_resumen_tipo.setRowCount(0)
        acumulados: Dict[str, list] = {}
        for est in estadisticas:
            pac = id_a_pac.get(est["nombre"])
            tipo = pac.tipo if pac else "?"
            if tipo not in acumulados:
                acumulados[tipo] = []
            acumulados[tipo].append(est)

        for tipo, lista_est in sorted(acumulados.items(),
                                      key=lambda x: PRIORIDAD_SCHEDULER.get(x[0], 9)):
            cola = COLA_POR_TIPO.get(tipo, "?")
            prom_e = sum(e["espera"]   for e in lista_est) / len(lista_est)
            prom_r = sum(e["retorno"]  for e in lista_est) / len(lista_est)
            agregar_fila_tabla(self._tabla_resumen_tipo, [
                tipo, cola, len(lista_est),
                tick_a_duracion(prom_e),
                tick_a_duracion(prom_r),
            ])

        # Actualizar barra global
        self._actualizar_barra_global(
            tick_a_duracion(resumen["promedio_espera"]),
            tick_a_duracion(resumen["promedio_retorno"]),
            f"{resumen['uso_cpu']:.1f}%",
            str(self._cambios_contexto),
        )

        # Cambiar a tab Estadísticas
        self._tabs.setCurrentIndex(2)

    def _guardar_en_historial(self):
        if not self._segmentos:
            return
        estadisticas = calcular_estadisticas_desde_segmentos(self._segmentos)
        try:
            guardar_pacientes_atendidos(
                self._pacientes,
                estadisticas,
                self._algoritmos_por_tipo,
            )
        except Exception as e:
            pass  # Historial no crítico para la simulación

    # ── DASHBOARD HELPERS ─────────────────────────────────────────────────────

    def _actualizar_dashboard(self):
        n_pac = len(self._pacientes)
        self._actualizar_cards_dashboard(n_pac, 0, 0, 0, "—", "—", "—", 0)
        self._actualizar_tabla_colas()

    def _actualizar_dashboard_live(self):
        if not self._segmentos:
            return
        # Contar por estado estimado (simplificado durante la simulación)
        t_actual = self._barra_prog.value()
        en_aten = len({s.nombre_proceso for s in self._segmentos if s.inicio < t_actual < s.fin})
        fin = len({s.nombre_proceso for s in self._segmentos if s.fin <= t_actual})
        esp = max(0, len(self._pacientes) - fin - en_aten)
        self._actualizar_cards_dashboard(
            esp, en_aten, fin, 0, "—", "—", "—", self._cambios_contexto
        )

    def _actualizar_cards_dashboard(self, espera, atencion, finalizados, cancelados,
                                    prom_e, prom_r, uso_cpu, cambios_ctx):
        def set_val(card, val):
            for lbl in card.findChildren(QLabel):
                if getattr(lbl, "_es_valor", False):
                    lbl.setText(str(val))
                    break

        set_val(self._card_espera,       espera)
        set_val(self._card_atencion,     atencion)
        set_val(self._card_finalizados,  finalizados)
        set_val(self._card_cancelados,   cancelados)
        set_val(self._card_prom_espera,  prom_e)
        set_val(self._card_prom_retorno, prom_r)
        set_val(self._card_uso_cpu,      uso_cpu)
        set_val(self._card_cambios_ctx,  cambios_ctx)

    def _actualizar_tabla_colas(self):
        self._tabla_colas.setRowCount(0)
        conteo = {t: sum(1 for p in self._pacientes if p.tipo == t) for t in TIPOS_VALIDOS}
        algos  = {
            "ROJO":        self._combo_critica.currentText(),
            "AMARILLO":    self._combo_critica.currentText(),
            "EMBARAZADA":  self._combo_urgente.currentText(),
            "VERDE":       self._combo_urgente.currentText(),
            "CITA":        self._combo_normal.currentText(),
            "SEGUIMIENTO": self._combo_normal.currentText(),
        }
        for tipo in TIPOS_VALIDOS:
            agregar_fila_tabla(self._tabla_colas, [
                tipo,
                COLA_POR_TIPO.get(tipo, "?"),
                ETIQUETA_PRIORIDAD.get(tipo, "?"),
                conteo.get(tipo, 0),
                algos.get(tipo, "?"),
            ], centrado=True)

    def _actualizar_chip_estado(self, proceso_txt: str, alg_txt: str):
        def _set(widget, txt):
            for lbl in widget.findChildren(QLabel):
                if getattr(lbl, "_es_valor", False):
                    lbl.setText(txt)
                    break

        _set(self._lbl_estado_sim, "En ejecución")
        _set(self._lbl_sig_pac,    proceso_txt)
        _set(self._lbl_algoritmo,  alg_txt)

    # ── HISTORIAL ─────────────────────────────────────────────────────────────

    def _cargar_historial_tabla(self):
        self._registros_historial = cargar_historial()
        self._poblar_tabla_historial(self._registros_historial)

    def _poblar_tabla_historial(self, registros: List[dict]):
        self._tabla_historial.setRowCount(0)
        for r in registros:
            agregar_fila_tabla(self._tabla_historial, [
                r.get("numero_tiquete", "—"),
                r.get("nombre", "—"),
                r.get("tipo", "—"),
                r.get("cola", "—"),
                r.get("motivo", "—"),
                r.get("tiempo_espera", "—"),
                r.get("tiempo_retorno", "—"),
                r.get("algoritmo_usado", "—"),
                r.get("fecha_atencion", "—")[:10] if r.get("fecha_atencion") else "—",
            ])

    def _filtrar_historial(self):
        texto = self._txt_busq.text().strip().lower()
        tipo_f = self._combo_filtro_tipo.currentText()
        filtrados = [
            r for r in self._registros_historial
            if (tipo_f == "Todos" or r.get("tipo", "") == tipo_f)
            and (not texto or
                 texto in r.get("nombre", "").lower() or
                 texto in r.get("numero_tiquete", "").lower() or
                 texto in r.get("id_paciente", "").lower())
        ]
        self._poblar_tabla_historial(filtrados)

    def _limpiar_historial(self):
        resp = QMessageBox.question(
            self, "Confirmar",
            "¿Desea limpiar todo el historial de pacientes atendidos?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            limpiar_historial()
            self._registros_historial = []
            self._tabla_historial.setRowCount(0)

    def _al_cambiar_tab(self, indice: int):
        if indice == 3:  # Historial
            self._cargar_historial_tabla()

    # ── UTILIDADES ────────────────────────────────────────────────────────────

    def _agregar_fila_paciente(self, pac: Paciente):
        fila = self._tabla_pacientes.rowCount()
        self._tabla_pacientes.insertRow(fila)
        valores = [pac.numero_tiquete, pac.nombre_corto, pac.tipo,
                   pac.tiempo_llegada, pac.tiempo_rafaga]
        for col, val in enumerate(valores):
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignCenter)
            # Colorear la columna Tipo con el color del tipo
            if col == 2:
                item.setForeground(_COLOR_TIPO.get(pac.tipo, QColor(0, 0, 0)))
                f = QFont("Segoe UI", 8)
                f.setBold(True)
                item.setFont(f)
            self._tabla_pacientes.setItem(fila, col, item)

    def _buscar_paciente_por_id(self, id_pac: str) -> Optional[Paciente]:
        return next((p for p in self._pacientes if p.id_paciente == id_pac), None)

    def _crear_sub_planificador(self, combo: QComboBox, spin: QSpinBox):
        idx = combo.currentIndex()
        if idx == 0:
            return PlanificadorFIFO()
        if idx == 1:
            return PlanificadorSJF()
        if idx == 2:
            return PlanificadorRoundRobin(spin.value())
        return PlanificadorFIFO()

    def _log(self, texto: str):
        self._txt_log.append(texto)
        cursor = self._txt_log.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._txt_log.setTextCursor(cursor)

    def _sep_h(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {a_css(COLOR_BORDE)};")
        return sep

    def _seccion_lbl(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        f = QFont("Segoe UI", 7)
        f.setBold(True)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        lbl.setFont(f)
        lbl.setStyleSheet(
            f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent; margin-bottom: 2px;"
        )
        return lbl

    def _metrica_card(self, titulo: str, valor: str, color_hex: str) -> QFrame:
        card = QFrame()
        card.setFixedHeight(76)
        card.setMinimumWidth(130)
        card.setStyleSheet(f"""
            QFrame {{
                background: {a_css(COLOR_SUPERFICIE)};
                border: 1px solid {a_css(COLOR_BORDE)};
                border-top: 3px solid {color_hex};
                border-radius: 6px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(4)

        lbl_t = QLabel(titulo.upper())
        f_t = QFont("Segoe UI", 7)
        f_t.setBold(True)
        f_t.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        lbl_t.setFont(f_t)
        lbl_t.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")

        lbl_v = QLabel(valor)
        f_v = QFont("Segoe UI", 20)
        f_v.setBold(True)
        lbl_v.setFont(f_v)
        lbl_v.setStyleSheet(f"color: {color_hex}; background: transparent;")
        lbl_v._es_valor = True

        lay.addWidget(lbl_t)
        lay.addWidget(lbl_v)
        return card

    def _lbl_estado_chip(self, etiqueta: str, valor: str, color_hex: str) -> QWidget:
        chip = QWidget()
        chip.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(chip)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

        lbl_et = QLabel(etiqueta)
        lbl_et.setFont(QFont("Segoe UI", 7))
        lbl_et.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")

        lbl_v = QLabel(valor)
        f_v = QFont("Segoe UI", 9)
        f_v.setBold(True)
        lbl_v.setFont(f_v)
        lbl_v.setStyleSheet(f"color: {color_hex}; background: transparent;")
        lbl_v._es_valor = True
        lbl_v.setObjectName("_valor")

        lay.addWidget(lbl_et)
        lay.addWidget(lbl_v)
        return chip

    def _barra_global(self) -> QWidget:
        barra = QWidget()
        barra.setFixedHeight(44)
        barra.setStyleSheet(f"""
            background: {a_css(COLOR_SUPERFICIE)};
            border: 1px solid {a_css(COLOR_BORDE)};
            border-radius: 6px;
        """)
        lay = QHBoxLayout(barra)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(24)

        self._chips_global: Dict[str, QLabel] = {}
        for clave, titulo, color in [
            ("prom_espera",  "Prom. Espera:",  a_css(COLOR_ACENTO)),
            ("prom_retorno", "Prom. Retorno:", a_css(COLOR_ACENTO)),
            ("uso_cpu",      "Uso CPU:",       a_css(COLOR_ACENTO_CYAN)),
            ("cambios_ctx",  "Cambios ctx.:",  a_css(COLOR_PELIGRO)),
        ]:
            sub = QWidget()
            sub.setStyleSheet("background: transparent;")
            h = QHBoxLayout(sub)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(5)

            l_et = QLabel(titulo)
            l_et.setFont(QFont("Segoe UI", 7))
            l_et.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")

            l_val = QLabel("—")
            f_val = QFont("Segoe UI", 9)
            f_val.setBold(True)
            l_val.setFont(f_val)
            l_val.setStyleSheet(f"color: {color}; background: transparent;")

            h.addWidget(l_et)
            h.addWidget(l_val)
            self._chips_global[clave] = l_val
            lay.addWidget(sub)

        lay.addStretch()
        return barra

    def _actualizar_barra_global(self, prom_e, prom_r, uso_cpu, cambios):
        vals = {"prom_espera": prom_e, "prom_retorno": prom_r,
                "uso_cpu": uso_cpu, "cambios_ctx": cambios}
        for clave, val in vals.items():
            if clave in self._chips_global:
                self._chips_global[clave].setText(str(val))
