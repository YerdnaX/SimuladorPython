from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QFrame, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from interfaz.tema import (
    COLOR_SUPERFICIE, COLOR_FONDO_PRIMARIO, COLOR_BORDE,
    COLOR_ACENTO, COLOR_TEXTO_PRIMARIO, COLOR_TEXTO_SECUNDARIO,
    COLOR_TEXTO_MUTED, COLOR_EXITO, COLOR_PELIGRO,
    fuente_h2, fuente_base, fuente_pequena, css_boton, a_css,
)
from interfaz.controles_personalizados import crear_spinbox


class DialogoProceso(QDialog):
    """Diálogo para ingresar un proceso manualmente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Proceso")
        # Evita solapes cuando el sistema usa escalado DPI/fuentes mayores.
        self.setMinimumSize(380, 360)
        self.resize(390, 370)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {a_css(COLOR_SUPERFICIE)};
            }}
        """)

        self._llegada = 0
        self._rafaga = 4
        self._prioridad = 1

        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Cabecera ──────────────────────────────────────────────────────────
        cabecera = QWidget()
        cabecera.setObjectName("cabecera_proceso")
        cabecera.setFixedHeight(72)
        cabecera.setStyleSheet(f"""
            QWidget#cabecera_proceso {{
                background-color: {a_css(COLOR_SUPERFICIE)};
                border-bottom: 3px solid {a_css(COLOR_ACENTO)};
            }}
        """)
        layout_cab = QVBoxLayout(cabecera)
        layout_cab.setContentsMargins(20, 9, 20, 8)
        layout_cab.setSpacing(4)

        titulo = QLabel("Nuevo Proceso")
        titulo.setFont(fuente_h2())
        titulo.setStyleSheet(f"color: {a_css(COLOR_TEXTO_PRIMARIO)}; background: transparent;")

        subtitulo = QLabel("Complete los parámetros de tiempo y prioridad")
        subtitulo.setFont(fuente_pequena())
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")

        layout_cab.addWidget(titulo)
        layout_cab.addWidget(subtitulo)
        layout.addWidget(cabecera)

        # ── Área de campos ────────────────────────────────────────────────────
        area = QWidget()
        area.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        layout_area = QVBoxLayout(area)
        layout_area.setContentsMargins(20, 16, 20, 14)
        layout_area.setSpacing(12)

        self._spin_llegada = crear_spinbox(0, 9999, 0)
        self._spin_rafaga = crear_spinbox(1, 9999, 4)
        self._spin_prioridad = crear_spinbox(1, 5, 1)

        campos = [
            ("Tiempo de llegada", "Unidades antes de ingresar a la cola", self._spin_llegada),
            ("Tiempo de ráfaga",  "Unidades de CPU que requiere el proceso", self._spin_rafaga),
            ("Prioridad  (1 = alta, 5 = baja)", "", self._spin_prioridad),
        ]

        for etiqueta, hint, spin in campos:
            contenedor = QWidget()
            contenedor.setStyleSheet("background: transparent;")
            col = QVBoxLayout(contenedor)
            col.setContentsMargins(0, 0, 0, 0)
            col.setSpacing(3)

            fila = QHBoxLayout()
            fila.setSpacing(10)

            lbl = QLabel(etiqueta)
            lbl.setFont(fuente_base())
            lbl.setStyleSheet(f"color: {a_css(COLOR_TEXTO_PRIMARIO)}; background: transparent;")
            lbl.setMinimumWidth(190)

            spin.setFixedWidth(110)
            fila.addWidget(lbl)
            fila.addWidget(spin)
            fila.addStretch()
            col.addLayout(fila)

            if hint:
                lbl_hint = QLabel(hint)
                lbl_hint.setFont(QFont("Segoe UI", 7))
                lbl_hint.setStyleSheet(
                    f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent; margin-left: 0px;"
                )
                col.addWidget(lbl_hint)

            layout_area.addWidget(contenedor)

        layout.addWidget(area)
        layout.addStretch()

        # ── Separador ─────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout.addWidget(sep)

        # ── Footer con botones ────────────────────────────────────────────────
        pie = QWidget()
        pie.setFixedHeight(58)
        pie.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_PRIMARIO)};")
        layout_pie = QHBoxLayout(pie)
        layout_pie.setContentsMargins(20, 10, 20, 10)
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

        btn_aceptar = QPushButton("Agregar proceso")
        btn_aceptar.setFixedSize(140, 34)
        btn_aceptar.setStyleSheet(css_boton(COLOR_ACENTO))
        btn_aceptar.setCursor(Qt.PointingHandCursor)
        btn_aceptar.clicked.connect(self._aceptar)

        layout_pie.addWidget(btn_cancelar)
        layout_pie.addWidget(btn_aceptar)
        layout.addWidget(pie)

    def _aceptar(self):
        self._llegada = self._spin_llegada.value()
        self._rafaga = self._spin_rafaga.value()
        self._prioridad = self._spin_prioridad.value()
        self.accept()

    @property
    def llegada(self) -> int:
        return self._llegada

    @property
    def rafaga(self) -> int:
        return self._rafaga

    @property
    def prioridad(self) -> int:
        return self._prioridad
