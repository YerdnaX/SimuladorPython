from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QFrame, QWidget, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from interfaz.tema import (
    COLOR_SUPERFICIE, COLOR_FONDO_PRIMARIO, COLOR_BORDE,
    COLOR_ACENTO, COLOR_TEXTO_PRIMARIO, COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_MUTED, COLORES_PROCESOS,
    fuente_h2, fuente_base, fuente_pequena, css_boton, a_css,
)
from interfaz.controles_personalizados import crear_spinbox, crear_combo


class DialogoCliente(QDialog):
    """Diálogo para registrar un cliente bancario."""

    TIPOS_CLIENTE = ["VIP", "ADULTOMAYOR", "EMBARAZADA", "REGULAR", "FORANEO"]

    # Descripción breve de cada tipo para mostrar como ayuda
    _HINTS = {
        "VIP":         "Prioridad 1 — Cola Alta   — 2 min de atención",
        "ADULTOMAYOR": "Prioridad 2 — Cola Alta   — 3 min de atención",
        "EMBARAZADA":  "Prioridad 3 — Cola Media  — 3 min de atención",
        "REGULAR":     "Prioridad 4 — Cola Baja   — 4 min de atención",
        "FORANEO":     "Prioridad 5 — Cola Baja   — 5 min de atención",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Cliente")
        self.setFixedSize(400, 330)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {a_css(COLOR_SUPERFICIE)};
            }}
        """)

        self._nombre = ""
        self._tipo = "REGULAR"
        self._llegada = 0

        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Cabecera ──────────────────────────────────────────────────────────
        cabecera = QWidget()
        cabecera.setFixedHeight(56)
        cabecera.setStyleSheet(f"""
            background-color: {a_css(COLOR_SUPERFICIE)};
            border-bottom: 3px solid {a_css(COLOR_ACENTO)};
        """)
        layout_cab = QVBoxLayout(cabecera)
        layout_cab.setContentsMargins(20, 10, 20, 0)
        layout_cab.setSpacing(2)

        titulo = QLabel("Registrar Cliente Bancario")
        titulo.setFont(fuente_h2())
        titulo.setStyleSheet(f"color: {a_css(COLOR_TEXTO_PRIMARIO)}; background: transparent;")

        subtitulo = QLabel("Ingrese los datos del cliente para la cola de atención")
        subtitulo.setFont(fuente_pequena())
        subtitulo.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")

        layout_cab.addWidget(titulo)
        layout_cab.addWidget(subtitulo)
        layout.addWidget(cabecera)

        # ── Área de campos ────────────────────────────────────────────────────
        area = QWidget()
        area.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        layout_area = QVBoxLayout(area)
        layout_area.setContentsMargins(20, 18, 20, 8)
        layout_area.setSpacing(14)

        # Nombre
        self._txt_nombre = QLineEdit()
        self._txt_nombre.setFixedHeight(32)
        self._txt_nombre.setPlaceholderText("Ej: Ana García")
        self._txt_nombre.setStyleSheet(f"""
            QLineEdit {{
                background-color: {a_css(COLOR_SUPERFICIE)};
                color: {a_css(COLOR_TEXTO_PRIMARIO)};
                border: 1.5px solid {a_css(COLOR_BORDE)};
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 9pt;
            }}
            QLineEdit:focus {{
                border-color: {a_css(COLOR_ACENTO)};
                border-width: 2px;
            }}
        """)
        layout_area.addLayout(self._fila("Nombre del cliente", self._txt_nombre))

        # Tipo de cliente
        self._combo_tipo = crear_combo(self.TIPOS_CLIENTE, indice=3)
        self._combo_tipo.setFixedWidth(160)
        self._combo_tipo.currentTextChanged.connect(self._al_cambiar_tipo)
        layout_area.addLayout(self._fila("Tipo de cliente", self._combo_tipo))

        # Hint de tipo
        self._lbl_hint_tipo = QLabel(self._HINTS["REGULAR"])
        self._lbl_hint_tipo.setFont(QFont("Segoe UI", 7))
        self._lbl_hint_tipo.setStyleSheet(
            f"color: {a_css(COLOR_ACENTO)}; background: transparent; "
            f"padding: 3px 8px; "
            f"border-left: 2px solid {a_css(COLOR_ACENTO)};"
        )
        layout_area.addWidget(self._lbl_hint_tipo)

        # Tiempo de llegada
        self._spin_llegada = crear_spinbox(0, 9999, 0)
        self._spin_llegada.setFixedWidth(110)
        layout_area.addLayout(self._fila("Tiempo de llegada", self._spin_llegada))

        layout.addWidget(area)
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
        layout_pie = QHBoxLayout(pie)
        layout_pie.setContentsMargins(20, 12, 20, 12)
        layout_pie.setSpacing(10)

        layout_pie.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedSize(110, 34)
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setStyleSheet(f"""
            QPushButton {{
                background-color: {a_css(COLOR_SUPERFICIE)};
                color: {a_css(COLOR_TEXTO_SECUNDARIO)};
                border: 1.5px solid {a_css(COLOR_BORDE)};
                border-radius: 5px;
                font-weight: bold;
                font-size: 8.5pt;
            }}
            QPushButton:hover {{
                background-color: rgb(244,246,251);
                border-color: rgb(192,198,220);
            }}
            QPushButton:pressed {{
                background-color: rgb(237,240,250);
            }}
        """)
        btn_cancelar.clicked.connect(self.reject)

        btn_aceptar = QPushButton("Registrar cliente")
        btn_aceptar.setFixedSize(148, 34)
        btn_aceptar.setStyleSheet(css_boton(COLOR_ACENTO))
        btn_aceptar.setCursor(Qt.PointingHandCursor)
        btn_aceptar.clicked.connect(self._aceptar)

        layout_pie.addWidget(btn_cancelar)
        layout_pie.addWidget(btn_aceptar)
        layout.addWidget(pie)

    def _fila(self, etiqueta: str, control) -> QHBoxLayout:
        fila = QHBoxLayout()
        fila.setSpacing(12)
        lbl = QLabel(etiqueta)
        lbl.setFont(fuente_base())
        lbl.setStyleSheet(f"color: {a_css(COLOR_TEXTO_PRIMARIO)}; background: transparent;")
        lbl.setFixedWidth(160)
        fila.addWidget(lbl)
        fila.addWidget(control)
        fila.addStretch()
        return fila

    def _al_cambiar_tipo(self, tipo: str):
        self._lbl_hint_tipo.setText(self._HINTS.get(tipo, ""))

    def _aceptar(self):
        nombre = self._txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo requerido", "Ingrese el nombre del cliente.")
            return
        self._nombre = nombre
        self._tipo = self._combo_tipo.currentText()
        self._llegada = self._spin_llegada.value()
        self.accept()

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tipo(self) -> str:
        return self._tipo

    @property
    def llegada(self) -> int:
        return self._llegada
