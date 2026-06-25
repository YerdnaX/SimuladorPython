from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFrame, QWidget, QMessageBox, QGridLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from interfaz.tema import (
    COLOR_SUPERFICIE, COLOR_FONDO_PRIMARIO, COLOR_BORDE,
    COLOR_ACENTO, COLOR_TEXTO_PRIMARIO, COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_MUTED, COLOR_EXITO,
    fuente_h2, fuente_base, fuente_pequena, css_boton, a_css,
)
from interfaz.controles_personalizados import crear_spinbox, crear_combo
from modelos.paciente import (
    TIPOS_VALIDOS, ETIQUETA_PRIORIDAD, COLA_POR_TIPO, RAFAGA_DEFAULT
)

# Color visual asociado a cada tipo de paciente
_COLOR_TIPO: dict[str, str] = {
    "ROJO":        "#EF4444",
    "AMARILLO":    "#F59E0B",
    "EMBARAZADA":  "#EC4899",
    "VERDE":       "#22C55E",
    "CITA":        "#3B82F6",
    "SEGUIMIENTO": "#6366F1",
}

_MOTIVOS: list[str] = [
    "Accidente de tránsito", "Herida grave", "Herida leve", "Parto",
    "Desmayo / pérdida de conciencia", "Dolor de pecho", "Fractura",
    "Quemadura", "Cita de control programada",
    "Seguimiento postoperatorio", "Otro",
]

# Contador global de tiquetes dentro de la sesión
_contador_tiquete: list[int] = [0]


def _generar_id_y_tiquete() -> tuple[str, str]:
    _contador_tiquete[0] += 1
    n = _contador_tiquete[0]
    return f"P{n:03d}", f"T-{n:04d}"


class DialogoPaciente(QDialog):
    """Diálogo de registro manual de un paciente del Centro de Emergencias."""

    def __init__(self, parent=None, id_sugerido: str = "", tiquete_sugerido: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Registrar Paciente")
        self.setFixedSize(480, 520)
        self.setStyleSheet(f"QDialog {{ background-color: {a_css(COLOR_SUPERFICIE)}; }}")

        id_auto, tq_auto = _generar_id_y_tiquete()
        self._id_inicial = id_sugerido or id_auto
        self._tq_inicial = tiquete_sugerido or tq_auto

        # Valores exportados tras aceptar
        self._id_paciente = ""
        self._nombre = ""
        self._tipo = ""
        self._motivo = ""
        self._llegada = 0
        self._rafaga = 4
        self._identificacion = ""
        self._edad = 0
        self._telefono = ""

        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Cabecera ──────────────────────────────────────────────────────────
        cab = QWidget()
        cab.setFixedHeight(64)
        cab.setStyleSheet(f"""
            background-color: {a_css(COLOR_SUPERFICIE)};
            border-bottom: 3px solid {a_css(COLOR_ACENTO)};
        """)
        cab_lay = QVBoxLayout(cab)
        cab_lay.setContentsMargins(20, 10, 20, 0)
        cab_lay.setSpacing(2)

        tit = QLabel("Registro de Paciente")
        tit.setFont(fuente_h2())
        tit.setStyleSheet(f"color: {a_css(COLOR_TEXTO_PRIMARIO)}; background: transparent;")

        sub = QLabel(f"Tiquete asignado: {self._tq_inicial}  ·  ID: {self._id_inicial}")
        sub.setFont(fuente_pequena())
        sub.setStyleSheet(f"color: {a_css(COLOR_ACENTO)}; background: transparent; font-weight: bold;")

        cab_lay.addWidget(tit)
        cab_lay.addWidget(sub)
        layout.addWidget(cab)

        # ── Formulario ────────────────────────────────────────────────────────
        form_w = QWidget()
        form_w.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        form_lay = QGridLayout(form_w)
        form_lay.setContentsMargins(20, 16, 20, 8)
        form_lay.setHorizontalSpacing(14)
        form_lay.setVerticalSpacing(12)
        form_lay.setColumnStretch(1, 1)
        form_lay.setColumnStretch(3, 1)

        def lbl(txt):
            l = QLabel(txt)
            l.setFont(fuente_base())
            l.setStyleSheet(f"color: {a_css(COLOR_TEXTO_PRIMARIO)}; background: transparent;")
            return l

        def campo_texto(placeholder=""):
            t = QLineEdit()
            t.setFixedHeight(30)
            t.setPlaceholderText(placeholder)
            t.setStyleSheet(f"""
                QLineEdit {{
                    background: {a_css(COLOR_SUPERFICIE)};
                    color: {a_css(COLOR_TEXTO_PRIMARIO)};
                    border: 1.5px solid {a_css(COLOR_BORDE)};
                    border-radius: 5px; padding: 3px 8px;
                }}
                QLineEdit:focus {{
                    border-color: {a_css(COLOR_ACENTO)}; border-width: 2px;
                }}
            """)
            return t

        # Fila 0: Nombre completo (col 0-3)
        form_lay.addWidget(lbl("Nombre completo *"), 0, 0)
        self._txt_nombre = campo_texto("Ej: Ana Solano Vargas")
        form_lay.addWidget(self._txt_nombre, 0, 1, 1, 3)

        # Fila 1: Identificación | Edad
        form_lay.addWidget(lbl("Identificación"), 1, 0)
        self._txt_id = campo_texto("Cédula o pasaporte")
        form_lay.addWidget(self._txt_id, 1, 1)
        form_lay.addWidget(lbl("Edad"), 1, 2)
        self._spin_edad = crear_spinbox(0, 120, 0)
        self._spin_edad.setFixedWidth(80)
        form_lay.addWidget(self._spin_edad, 1, 3, Qt.AlignLeft)

        # Fila 2: Teléfono | Tipo paciente
        form_lay.addWidget(lbl("Teléfono"), 2, 0)
        self._txt_tel = campo_texto("8888-0000")
        form_lay.addWidget(self._txt_tel, 2, 1)
        form_lay.addWidget(lbl("Tipo de paciente *"), 2, 2)
        self._combo_tipo = crear_combo(TIPOS_VALIDOS, indice=0)
        self._combo_tipo.currentTextChanged.connect(self._al_cambiar_tipo)
        form_lay.addWidget(self._combo_tipo, 2, 3)

        # Fila 3: Motivo (col 0-3)
        form_lay.addWidget(lbl("Motivo de atención"), 3, 0)
        self._combo_motivo = crear_combo(_MOTIVOS, indice=0)
        form_lay.addWidget(self._combo_motivo, 3, 1, 1, 3)

        # Fila 4: Tiempo llegada | Tiempo ráfaga
        form_lay.addWidget(lbl("Tiempo de llegada"), 4, 0)
        self._spin_llegada = crear_spinbox(0, 9999, 0)
        form_lay.addWidget(self._spin_llegada, 4, 1, Qt.AlignLeft)
        form_lay.addWidget(lbl("Tiempo de ráfaga *"), 4, 2)
        self._spin_rafaga = crear_spinbox(1, 9999, RAFAGA_DEFAULT.get("ROJO", 8))
        form_lay.addWidget(self._spin_rafaga, 4, 3, Qt.AlignLeft)

        # Fila 5: Chip de información del tipo seleccionado
        self._lbl_info_tipo = QLabel()
        self._lbl_info_tipo.setFont(QFont("Segoe UI", 7))
        self._lbl_info_tipo.setStyleSheet(
            f"color: {a_css(COLOR_ACENTO)}; background: transparent; "
            f"padding: 4px 8px; border-left: 2px solid {a_css(COLOR_ACENTO)};"
        )
        form_lay.addWidget(self._lbl_info_tipo, 5, 0, 1, 4)

        layout.addWidget(form_w)
        layout.addStretch()

        # ── Separador ─────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout.addWidget(sep)

        # ── Footer ────────────────────────────────────────────────────────────
        pie = QWidget()
        pie.setFixedHeight(58)
        pie.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        pie_lay = QHBoxLayout(pie)
        pie_lay.setContentsMargins(20, 12, 20, 12)
        pie_lay.setSpacing(10)
        pie_lay.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedSize(110, 34)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {a_css(COLOR_SUPERFICIE)}; color: {a_css(COLOR_TEXTO_SECUNDARIO)};
                border: 1.5px solid {a_css(COLOR_BORDE)}; border-radius: 5px;
                font-weight: bold; font-size: 8.5pt;
            }}
            QPushButton:hover {{ background: rgb(244,246,251); }}
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Registrar paciente")
        btn_ok.setFixedSize(160, 34)
        btn_ok.setStyleSheet(css_boton(COLOR_ACENTO))
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(self._aceptar)

        pie_lay.addWidget(btn_cancel)
        pie_lay.addWidget(btn_ok)
        layout.addWidget(pie)

        # Disparar una vez para mostrar el hint inicial
        self._al_cambiar_tipo("ROJO")

    def _al_cambiar_tipo(self, tipo: str):
        tipo = tipo.upper()
        from modelos.paciente import ETIQUETA_PRIORIDAD, COLA_POR_TIPO
        prioridad_txt = ETIQUETA_PRIORIDAD.get(tipo, "—")
        cola_txt = COLA_POR_TIPO.get(tipo, "NORMAL")
        rafaga_def = RAFAGA_DEFAULT.get(tipo, 4)
        self._spin_rafaga.setValue(rafaga_def)
        self._lbl_info_tipo.setText(
            f"Prioridad: {prioridad_txt}   |   Cola de atención: {cola_txt}   |   "
            f"Ráfaga sugerida: {rafaga_def} u.t."
        )

    def _aceptar(self):
        nombre = self._txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo requerido", "Ingrese el nombre completo del paciente.")
            return
        if self._spin_rafaga.value() <= 0:
            QMessageBox.warning(self, "Campo requerido", "El tiempo de ráfaga debe ser mayor que 0.")
            return

        self._id_paciente   = self._id_inicial
        self._nombre        = nombre
        self._tipo          = self._combo_tipo.currentText()
        self._motivo        = self._combo_motivo.currentText()
        self._llegada       = self._spin_llegada.value()
        self._rafaga        = self._spin_rafaga.value()
        self._identificacion = self._txt_id.text().strip()
        self._edad          = self._spin_edad.value()
        self._telefono      = self._txt_tel.text().strip()
        self.accept()

    # ── Propiedades exportadas ────────────────────────────────────────────────
    @property
    def id_paciente(self) -> str:     return self._id_paciente
    @property
    def nombre(self) -> str:          return self._nombre
    @property
    def tipo(self) -> str:            return self._tipo
    @property
    def motivo(self) -> str:          return self._motivo
    @property
    def llegada(self) -> int:         return self._llegada
    @property
    def rafaga(self) -> int:          return self._rafaga
    @property
    def identificacion(self) -> str:  return self._identificacion
    @property
    def edad(self) -> int:            return self._edad
    @property
    def telefono(self) -> str:        return self._telefono
    @property
    def tiquete(self) -> str:         return self._tq_inicial
