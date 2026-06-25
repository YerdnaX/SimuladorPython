from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QFrame, QWidget, QMessageBox,
)
from PySide6.QtCore import Qt

from interfaz.tema import (
    COLOR_SUPERFICIE, COLOR_SUPERFICIE_ELEV, COLOR_FONDO_SECUNDARIO,
    COLOR_BORDE, COLOR_ACENTO_BRILLANTE, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_MUTED,
    COLOR_EXITO, COLOR_PELIGRO_OSCURO, COLOR_PELIGRO,
    fuente_h2, fuente_base, fuente_mono, css_boton, a_css,
)
from interfaz.controles_personalizados import crear_spinbox, crear_combo


# Diálogo modal para registrar un cliente bancario.
# Expone propiedades: nombre, tipo, llegada tras aceptar.
class DialogoCliente(QDialog):

    TIPOS_CLIENTE = ["VIP", "ADULTOMAYOR", "EMBARAZADA", "REGULAR", "FORANEO"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Cliente")
        self.setFixedSize(360, 315)
        self.setStyleSheet(f"QDialog {{ background-color: {a_css(COLOR_SUPERFICIE)}; }}")

        self._nombre = ""
        self._tipo = "REGULAR"
        self._llegada = 0

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
        titulo = QLabel("Registrar Cliente Bancario", cabecera)
        titulo.setFont(fuente_h2())
        titulo.setStyleSheet(f"color: {a_css(COLOR_ACENTO_BRILLANTE)}; background: transparent;")
        titulo.move(16, 14)

        sep_top = QFrame()
        sep_top.setFrameShape(QFrame.HLine)
        sep_top.setFixedHeight(1)
        sep_top.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")

        layout_principal.addWidget(cabecera)
        layout_principal.addWidget(sep_top)

        # ── Campos ────────────────────────────────────────────────────────
        area = QWidget()
        area.setStyleSheet(f"background-color: {a_css(COLOR_SUPERFICIE)};")
        layout_area = QVBoxLayout(area)
        layout_area.setContentsMargins(18, 12, 18, 8)
        layout_area.setSpacing(10)

        # Nombre
        self._txt_nombre = QLineEdit()
        self._txt_nombre.setFixedHeight(26)
        self._txt_nombre.setStyleSheet(f"""
            QLineEdit {{
                background-color: {a_css(COLOR_SUPERFICIE_ELEV)};
                color: white;
                border: 1px solid {a_css(COLOR_BORDE)};
                border-radius: 3px;
                padding: 2px 8px;
            }}
        """)
        layout_area.addLayout(self._fila_campo("Nombre:", self._txt_nombre))

        # Tipo de cliente
        self._combo_tipo = crear_combo(self.TIPOS_CLIENTE, indice=3)
        self._combo_tipo.setFixedWidth(130)
        layout_area.addLayout(self._fila_campo("Tipo de cliente:", self._combo_tipo))

        # Tiempo de llegada
        self._spin_llegada = crear_spinbox(0, 9999, 0)
        self._spin_llegada.setFixedWidth(130)
        layout_area.addLayout(self._fila_campo("Tiempo de llegada:", self._spin_llegada))

        # Hint de tipos
        sep_hint = QFrame()
        sep_hint.setFrameShape(QFrame.HLine)
        sep_hint.setFixedHeight(1)
        sep_hint.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_area.addWidget(sep_hint)

        hint = QLabel("VIP · ADULTOMAYOR · EMBARAZADA · REGULAR · FORANEO")
        hint.setFont(fuente_mono())
        hint.setStyleSheet(f"color: {a_css(COLOR_TEXTO_MUTED)}; background: transparent;")
        layout_area.addWidget(hint)

        layout_principal.addWidget(area)
        layout_principal.addStretch()

        # ── Footer ────────────────────────────────────────────────────────
        sep_footer = QFrame()
        sep_footer.setFrameShape(QFrame.HLine)
        sep_footer.setFixedHeight(1)
        sep_footer.setStyleSheet(f"background-color: {a_css(COLOR_BORDE)};")
        layout_principal.addWidget(sep_footer)

        pie = QWidget()
        pie.setFixedHeight(56)
        pie.setStyleSheet(f"background-color: {a_css(COLOR_FONDO_SECUNDARIO)};")
        layout_pie = QHBoxLayout(pie)
        layout_pie.setContentsMargins(16, 10, 16, 10)
        layout_pie.setSpacing(10)

        btn_aceptar = QPushButton("✔  Aceptar")
        btn_aceptar.setFixedSize(138, 32)
        btn_aceptar.setStyleSheet(css_boton(COLOR_EXITO))
        btn_aceptar.setCursor(Qt.PointingHandCursor)
        btn_aceptar.clicked.connect(self._aceptar)

        btn_cancelar = QPushButton("✖  Cancelar")
        btn_cancelar.setFixedSize(138, 32)
        btn_cancelar.setStyleSheet(css_boton(COLOR_PELIGRO_OSCURO, COLOR_PELIGRO))
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)

        layout_pie.addWidget(btn_aceptar)
        layout_pie.addWidget(btn_cancelar)
        layout_pie.addStretch()
        layout_principal.addWidget(pie)

    # Crea una fila horizontal etiqueta + control.
    def _fila_campo(self, etiqueta: str, control) -> QHBoxLayout:
        fila = QHBoxLayout()
        lbl = QLabel(etiqueta)
        lbl.setFont(fuente_base())
        lbl.setStyleSheet(f"color: {a_css(COLOR_TEXTO_SECUNDARIO)}; background: transparent;")
        lbl.setFixedWidth(155)
        fila.addWidget(lbl)
        fila.addWidget(control)
        fila.addStretch()
        return fila

    # Valida los campos y guarda los valores antes de cerrar con Aceptar.
    def _aceptar(self):
        nombre = self._txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Aviso", "Ingrese un nombre.")
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
