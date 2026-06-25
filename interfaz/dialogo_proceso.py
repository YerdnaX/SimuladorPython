from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QFrame, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from interfaz.tema import (
    COLOR_SUPERFICIE, COLOR_SUPERFICIE_ELEV, COLOR_FONDO_SECUNDARIO,
    COLOR_BORDE, COLOR_ACENTO_BRILLANTE, COLOR_TEXTO_SECUNDARIO,
    COLOR_EXITO, COLOR_PELIGRO_OSCURO, COLOR_PELIGRO,
    fuente_h2, fuente_base, css_boton, a_css,
)
from interfaz.controles_personalizados import crear_spinbox


# Diálogo modal para ingresar un proceso manualmente.
# Expone propiedades: llegada, rafaga, prioridad tras aceptar.
class DialogoProceso(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar Proceso")
        self.setFixedSize(340, 280)
        self.setStyleSheet(f"QDialog {{ background-color: {a_css(COLOR_SUPERFICIE)}; }}")

        self._llegada = 0
        self._rafaga = 4
        self._prioridad = 1

        self._construir_interfaz()

    # Construye todos los widgets del diálogo.
    def _construir_interfaz(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ── Cabecera ──────────────────────────────────────────────────────
        cabecera = QWidget()
        cabecera.setFixedHeight(50)
        cabecera.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE_ELEV)};")
        titulo = QLabel("Nuevo Proceso", cabecera)
        titulo.setFont(fuente_h2())
        titulo.setStyleSheet(f"color: {a_css(COLOR_ACENTO_BRILLANTE)}; background: transparent;")
        titulo.move(16, 14)

        separador_top = QFrame()
        separador_top.setFrameShape(QFrame.HLine)
        separador_top.setFixedHeight(1)
        separador_top.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")

        layout_principal.addWidget(cabecera)
        layout_principal.addWidget(separador_top)

        # ── Campos ────────────────────────────────────────────────────────
        area_campos = QWidget()
        area_campos.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        layout_campos = QVBoxLayout(area_campos)
        layout_campos.setContentsMargins(18, 12, 18, 12)
        layout_campos.setSpacing(12)

        self._spin_llegada = crear_spinbox(0, 9999, 0)
        self._spin_rafaga = crear_spinbox(1, 9999, 4)
        self._spin_prioridad = crear_spinbox(1, 5, 1)

        for etiqueta, spin in [
            ("Tiempo de llegada:", self._spin_llegada),
            ("Tiempo de ráfaga:", self._spin_rafaga),
            ("Prioridad  (1 – 5):", self._spin_prioridad),
        ]:
            fila = QHBoxLayout()
            lbl = QLabel(etiqueta)
            lbl.setFont(fuente_base())
            lbl.setStyleSheet(f"color: {a_css(COLOR_TEXTO_SECUNDARIO)}; background: transparent;")
            lbl.setFixedWidth(160)
            spin.setFixedWidth(120)
            fila.addWidget(lbl)
            fila.addWidget(spin)
            fila.addStretch()
            layout_campos.addLayout(fila)

        layout_principal.addWidget(area_campos)
        layout_principal.addStretch()

        # ── Separador y botones ───────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_principal.addWidget(sep)

        pie = QWidget()
        pie.setFixedHeight(56)
        pie.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_SECUNDARIO)};")
        layout_pie = QHBoxLayout(pie)
        layout_pie.setContentsMargins(16, 10, 16, 10)
        layout_pie.setSpacing(10)

        btn_aceptar = QPushButton("✔  Aceptar")
        btn_aceptar.setFixedSize(130, 32)
        btn_aceptar.setStyleSheet(css_boton(COLOR_EXITO))
        btn_aceptar.setCursor(Qt.PointingHandCursor)
        btn_aceptar.clicked.connect(self._aceptar)

        btn_cancelar = QPushButton("✖  Cancelar")
        btn_cancelar.setFixedSize(130, 32)
        btn_cancelar.setStyleSheet(css_boton(COLOR_PELIGRO_OSCURO, COLOR_PELIGRO))
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)

        layout_pie.addWidget(btn_aceptar)
        layout_pie.addWidget(btn_cancelar)
        layout_pie.addStretch()
        layout_principal.addWidget(pie)

    # Valida y guarda los valores antes de cerrar el diálogo con Aceptar.
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
