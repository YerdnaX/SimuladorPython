from PySide6.QtWidgets import (
    QWidget, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QAbstractSpinBox, QHeaderView, QSizePolicy, QSpinBox, QComboBox,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient

from interfaz.tema import (
    COLOR_FONDO_PRIMARIO, COLOR_FONDO_SECUNDARIO, COLOR_SUPERFICIE,
    COLOR_SUPERFICIE_ALT, COLOR_SUPERFICIE_ELEV, COLOR_SUPERFICIE_HOVER,
    COLOR_BORDE, COLOR_BORDE_FUERTE, COLOR_ACENTO, COLOR_ACENTO_BRILLANTE,
    COLOR_TEXTO_PRIMARIO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_MUTED,
    fuente_seccion, fuente_base, fuente_pequena, css_boton, a_css,
    oscurecer, aclarar,
)


# Tarjeta con cabecera pintada a mano — tema claro institucional.
class TarjetaTema(QFrame):
    ALTURA_CABECERA = 36

    def __init__(self, titulo: str, parent=None):
        super().__init__(parent)
        self._titulo = titulo
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            TarjetaTema {{
                background-color: {a_css(COLOR_SUPERFICIE)};
                border: 1px solid {a_css(COLOR_BORDE)};
                border-radius: 8px;
            }}
        """)
        self.setContentsMargins(1, self.ALTURA_CABECERA, 1, 1)

    def establecer_titulo(self, titulo: str) -> None:
        self._titulo = titulo
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        ancho = self.width()
        h = self.ALTURA_CABECERA

        # Fondo de la cabecera (blanco)
        painter.fillRect(1, 1, ancho - 2, h - 1, COLOR_SUPERFICIE)

        # Barra de acento superior (4px, azul institucional)
        painter.fillRect(1, 1, ancho - 2, 3, COLOR_ACENTO)

        # Título en gris oscuro, negrita pequeña
        f_titulo = QFont("Segoe UI", 8)
        f_titulo.setBold(True)
        painter.setFont(f_titulo)
        painter.setPen(COLOR_TEXTO_SECUNDARIO)
        painter.drawText(14, 0, ancho - 28, h, Qt.AlignVCenter | Qt.AlignLeft,
                         self._titulo.upper())

        # Línea separadora inferior de cabecera (borde suave)
        painter.setPen(QPen(COLOR_BORDE, 1))
        painter.drawLine(1, h, ancho - 2, h)


# Ítem de navegación lateral — tema claro.
class ItemNavegacion(QWidget):
    clic = Signal()
    ALTURA = 48

    def __init__(self, icono: str, texto: str, parent=None):
        super().__init__(parent)
        self._icono = icono
        self._texto = texto
        self._seleccionado = False
        self._hover = False
        self.setFixedHeight(self.ALTURA)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

    @property
    def seleccionado(self) -> bool:
        return self._seleccionado

    @seleccionado.setter
    def seleccionado(self, valor: bool):
        self._seleccionado = valor
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.Antialiasing)

        ancho = self.width()
        alto = self.ALTURA

        # Fondo del ítem
        if self._seleccionado:
            # Fondo azul institucional para el seleccionado
            painter.fillRect(0, 0, ancho, alto, COLOR_ACENTO)
        elif self._hover:
            painter.fillRect(0, 0, ancho, alto, QColor(237, 241, 252))
        else:
            painter.fillRect(0, 0, ancho, alto, COLOR_SUPERFICIE)

        # Barra de acento izquierda solo cuando está seleccionado
        if self._seleccionado:
            painter.fillRect(0, 8, 3, alto - 16, QColor(255, 255, 255, 180))

        # Icono
        f_icono = QFont("Segoe UI", 10)
        painter.setFont(f_icono)
        if self._seleccionado:
            painter.setPen(QColor(255, 255, 255))
        elif self._hover:
            painter.setPen(COLOR_ACENTO)
        else:
            painter.setPen(COLOR_TEXTO_MUTED)
        painter.drawText(16, 0, 28, alto, Qt.AlignVCenter | Qt.AlignLeft, self._icono)

        # Texto
        f_etiqueta = fuente_seccion() if self._seleccionado else fuente_base()
        painter.setFont(f_etiqueta)
        if self._seleccionado:
            painter.setPen(QColor(255, 255, 255))
        elif self._hover:
            painter.setPen(COLOR_ACENTO)
        else:
            painter.setPen(COLOR_TEXTO_PRIMARIO)
        painter.drawText(50, 0, ancho - 56, alto, Qt.AlignVCenter | Qt.AlignLeft, self._texto)

        # Divisor inferior sutil (solo cuando no seleccionado)
        if not self._seleccionado:
            painter.setPen(QPen(COLOR_BORDE, 1))
            painter.drawLine(12, alto - 1, ancho - 12, alto - 1)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clic.emit()


def crear_boton(texto: str, color_fondo: QColor, ancho: int = 120, alto: int = 30) -> QPushButton:
    btn = QPushButton(texto)
    btn.setFixedSize(ancho, alto)
    btn.setStyleSheet(css_boton(color_fondo))
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def crear_tabla(columnas: list[str], alto_fila: int = 28) -> QTableWidget:
    tabla = QTableWidget()
    tabla.setColumnCount(len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.setAlternatingRowColors(True)
    tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabla.verticalHeader().setVisible(False)
    tabla.horizontalHeader().setHighlightSections(False)
    tabla.horizontalHeader().setStretchLastSection(True)
    tabla.setShowGrid(True)
    tabla.setGridStyle(Qt.SolidLine)
    tabla.verticalHeader().setDefaultSectionSize(alto_fila)
    tabla.setStyleSheet(f"""
        QTableWidget {{
            background-color: {a_css(COLOR_SUPERFICIE)};
            alternate-background-color: {a_css(COLOR_SUPERFICIE_ALT)};
            color: {a_css(COLOR_TEXTO_PRIMARIO)};
            gridline-color: {a_css(COLOR_BORDE)};
            border: none;
            outline: none;
        }}
        QTableWidget::item {{
            padding: 5px 8px;
        }}
        QTableWidget::item:selected {{
            background-color: rgb(219,229,251);
            color: rgb(30,58,138);
        }}
        QHeaderView::section {{
            background-color: {a_css(COLOR_FONDO_PRIMARIO)};
            color: {a_css(COLOR_TEXTO_SECUNDARIO)};
            border: none;
            border-bottom: 2px solid {a_css(COLOR_BORDE)};
            border-right: 1px solid {a_css(COLOR_BORDE)};
            padding: 7px 8px;
            font-weight: bold;
            font-size: 8pt;
        }}
        QHeaderView::section:last {{
            border-right: none;
        }}
    """)
    return tabla


def agregar_fila_tabla(tabla: QTableWidget, valores: list, centrado: bool = False) -> int:
    fila = tabla.rowCount()
    tabla.insertRow(fila)
    for col, valor in enumerate(valores):
        item = QTableWidgetItem(str(valor))
        if centrado:
            item.setTextAlignment(Qt.AlignCenter)
        tabla.setItem(fila, col, item)
    return fila


def crear_etiqueta_campo(texto: str) -> QLabel:
    lbl = QLabel(texto)
    lbl.setFont(fuente_base())
    lbl.setStyleSheet(f"color: {a_css(COLOR_TEXTO_SECUNDARIO)}; background: transparent;")
    return lbl


def crear_spinbox(minimo: int, maximo: int, valor: int = 0) -> QSpinBox:
    spin = QSpinBox()
    spin.setMinimum(minimo)
    spin.setMaximum(maximo)
    spin.setValue(valor)
    spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
    spin.setFixedHeight(28)
    spin.setStyleSheet(f"""
        QSpinBox {{
            background-color: {a_css(COLOR_SUPERFICIE)};
            color: {a_css(COLOR_TEXTO_PRIMARIO)};
            border: 1.5px solid {a_css(COLOR_BORDE)};
            border-radius: 5px;
            padding: 2px 6px;
        }}
        QSpinBox:focus {{
            border-color: {a_css(COLOR_ACENTO)};
            border-width: 2px;
        }}
        QSpinBox:hover {{
            border-color: {a_css(COLOR_BORDE_FUERTE)};
        }}
    """)
    return spin


def crear_combo(opciones: list[str], indice: int = 0) -> QComboBox:
    combo = QComboBox()
    combo.addItems(opciones)
    combo.setCurrentIndex(indice)
    combo.setFixedHeight(28)
    combo.setStyleSheet(f"""
        QComboBox {{
            background-color: {a_css(COLOR_SUPERFICIE)};
            color: {a_css(COLOR_TEXTO_PRIMARIO)};
            border: 1.5px solid {a_css(COLOR_BORDE)};
            border-radius: 5px;
            padding: 2px 8px;
        }}
        QComboBox:focus {{
            border-color: {a_css(COLOR_ACENTO)};
            border-width: 2px;
        }}
        QComboBox:hover {{
            border-color: {a_css(COLOR_BORDE_FUERTE)};
        }}
        QComboBox QAbstractItemView {{
            background-color: {a_css(COLOR_SUPERFICIE)};
            color: {a_css(COLOR_TEXTO_PRIMARIO)};
            selection-background-color: {a_css(COLOR_ACENTO)};
            selection-color: white;
            border: 1px solid {a_css(COLOR_BORDE)};
            border-radius: 4px;
            outline: none;
            padding: 2px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 22px;
        }}
    """)
    return combo
