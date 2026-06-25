from PySide6.QtWidgets import (
    QWidget, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QSizePolicy, QSpinBox, QComboBox,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush

from interfaz.tema import (
    COLOR_FONDO_PRIMARIO, COLOR_FONDO_SECUNDARIO, COLOR_SUPERFICIE,
    COLOR_SUPERFICIE_ELEV, COLOR_BORDE, COLOR_ACENTO, COLOR_ACENTO_BRILLANTE,
    COLOR_TEXTO_PRIMARIO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_MUTED,
    fuente_seccion, fuente_base, fuente_pequena, css_boton, a_css,
    oscurecer, aclarar,
)


# Panel con cabecera pintada a mano, equivalente a ThemedCard de WinForms.
class TarjetaTema(QFrame):
    ALTURA_CABECERA = 34

    def __init__(self, titulo: str, parent=None):
        super().__init__(parent)
        self._titulo = titulo
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            TarjetaTema {{
                background-color: {a_css(COLOR_SUPERFICIE)};
                border: 1px solid {a_css(COLOR_BORDE)};
            }}
        """)
        # Espacio superior reservado para la cabecera pintada
        self.setContentsMargins(1, self.ALTURA_CABECERA, 1, 1)

    # Actualiza el título de la tarjeta y repinta.
    def establecer_titulo(self, titulo: str) -> None:
        self._titulo = titulo
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        ancho = self.width()
        h = self.ALTURA_CABECERA

        # Fondo de la cabecera
        painter.fillRect(1, 1, ancho - 2, h - 1, COLOR_SUPERFICIE_ELEV)

        # Barra de acento superior (3px)
        painter.fillRect(1, 1, ancho - 2, 3, COLOR_ACENTO)

        # Título
        painter.setFont(fuente_seccion())
        painter.setPen(COLOR_ACENTO_BRILLANTE)
        painter.drawText(12, 0, ancho - 24, h, Qt.AlignVCenter | Qt.AlignLeft, self._titulo)

        # Línea separadora inferior de cabecera
        painter.setPen(QPen(COLOR_BORDE, 1))
        painter.drawLine(1, h, ancho - 2, h)


# Ítem de navegación lateral, equivalente a NavItem de WinForms.
class ItemNavegacion(QWidget):
    clic = Signal()

    ALTURA = 52

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

        ancho = self.width()
        alto = self.ALTURA

        if self._seleccionado:
            fondo = COLOR_SUPERFICIE
        elif self._hover:
            fondo = QColor(21, 23, 36)
        else:
            fondo = COLOR_FONDO_SECUNDARIO
        painter.fillRect(0, 0, ancho, alto, fondo)

        # Barra de acento lateral cuando está seleccionado
        if self._seleccionado:
            painter.fillRect(0, 10, 3, alto - 20, COLOR_ACENTO)

        # Icono
        fuente_icono = QFont("Segoe UI", 11)
        painter.setFont(fuente_icono)
        color_icono = COLOR_ACENTO_BRILLANTE if self._seleccionado else COLOR_TEXTO_MUTED
        painter.setPen(color_icono)
        offset_icono = 16 if self._seleccionado else 14
        painter.drawText(offset_icono, 0, 30, alto, Qt.AlignVCenter | Qt.AlignLeft, self._icono)

        # Etiqueta
        fuente_etiqueta = fuente_seccion() if self._seleccionado else fuente_base()
        painter.setFont(fuente_etiqueta)
        color_etiqueta = COLOR_TEXTO_PRIMARIO if self._seleccionado else COLOR_TEXTO_SECUNDARIO
        painter.setPen(color_etiqueta)
        painter.drawText(52, 0, ancho - 58, alto, Qt.AlignVCenter | Qt.AlignLeft, self._texto)

        # Divisor inferior
        painter.setPen(QPen(QColor(20, 22, 36), 1))
        painter.drawLine(0, alto - 1, ancho, alto - 1)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clic.emit()


# Crea y devuelve una QPushButton estilizada con el color dado.
def crear_boton(texto: str, color_fondo: QColor, ancho: int = 120, alto: int = 30) -> QPushButton:
    btn = QPushButton(texto)
    btn.setFixedSize(ancho, alto)
    btn.setStyleSheet(css_boton(color_fondo))
    btn.setCursor(Qt.PointingHandCursor)
    return btn


# Crea y devuelve una QTableWidget con el estilo oscuro del tema.
def crear_tabla(columnas: list[str], alto_fila: int = 26) -> QTableWidget:
    tabla = QTableWidget()
    tabla.setColumnCount(len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.setAlternatingRowColors(True)
    tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabla.verticalHeader().setVisible(False)
    tabla.horizontalHeader().setHighlightSections(False)
    tabla.setShowGrid(True)
    tabla.setGridStyle(Qt.SolidLine)
    tabla.verticalHeader().setDefaultSectionSize(alto_fila)
    tabla.setStyleSheet(f"""
        QTableWidget {{
            background-color: {a_css(COLOR_SUPERFICIE)};
            alternate-background-color: {a_css(QColor(29, 32, 48))};
            color: {a_css(COLOR_TEXTO_PRIMARIO)};
            gridline-color: {a_css(COLOR_BORDE)};
            border: none;
            outline: none;
        }}
        QTableWidget::item {{
            padding: 4px 6px;
        }}
        QTableWidget::item:selected {{
            background-color: {a_css(COLOR_ACENTO)};
            color: white;
        }}
        QHeaderView::section {{
            background-color: {a_css(COLOR_SUPERFICIE_ELEV)};
            color: {a_css(COLOR_ACENTO_BRILLANTE)};
            border: none;
            border-bottom: 1px solid {a_css(COLOR_BORDE)};
            padding: 5px 8px;
            font-weight: bold;
        }}
    """)
    return tabla


# Agrega una fila de datos a una QTableWidget con alineación centrada.
def agregar_fila_tabla(tabla: QTableWidget, valores: list, centrado: bool = False) -> int:
    fila = tabla.rowCount()
    tabla.insertRow(fila)
    for col, valor in enumerate(valores):
        item = QTableWidgetItem(str(valor))
        if centrado:
            item.setTextAlignment(Qt.AlignCenter)
        tabla.setItem(fila, col, item)
    return fila


# Crea un QLabel con estilo de etiqueta de campo (color secundario).
def crear_etiqueta_campo(texto: str) -> QLabel:
    lbl = QLabel(texto)
    lbl.setFont(fuente_base())
    lbl.setStyleSheet(f"color: {a_css(COLOR_TEXTO_SECUNDARIO)}; background: transparent;")
    return lbl


# Crea un QSpinBox estilizado con el tema oscuro.
def crear_spinbox(minimo: int, maximo: int, valor: int = 0) -> QSpinBox:
    spin = QSpinBox()
    spin.setMinimum(minimo)
    spin.setMaximum(maximo)
    spin.setValue(valor)
    spin.setFixedHeight(26)
    spin.setStyleSheet(f"""
        QSpinBox {{
            background-color: {a_css(COLOR_SUPERFICIE_ELEV)};
            color: {a_css(COLOR_TEXTO_PRIMARIO)};
            border: 1px solid {a_css(COLOR_BORDE)};
            border-radius: 3px;
            padding: 2px 6px;
        }}
    """)
    return spin


# Crea un QComboBox estilizado con el tema oscuro.
def crear_combo(opciones: list[str], indice: int = 0) -> QComboBox:
    combo = QComboBox()
    combo.addItems(opciones)
    combo.setCurrentIndex(indice)
    combo.setFixedHeight(26)
    combo.setStyleSheet(f"""
        QComboBox {{
            background-color: {a_css(COLOR_SUPERFICIE_ELEV)};
            color: {a_css(COLOR_TEXTO_PRIMARIO)};
            border: 1px solid {a_css(COLOR_BORDE)};
            border-radius: 3px;
            padding: 2px 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {a_css(COLOR_SUPERFICIE_ELEV)};
            color: {a_css(COLOR_TEXTO_PRIMARIO)};
            selection-background-color: {a_css(COLOR_ACENTO)};
            border: 1px solid {a_css(COLOR_BORDE)};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
    """)
    return combo
