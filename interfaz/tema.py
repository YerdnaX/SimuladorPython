from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt


# ── Paleta de colores — Tema claro institucional ──────────────────────────────
COLOR_FONDO_PRIMARIO   = QColor(247, 248, 252)   # Fondo general (gris muy suave)
COLOR_FONDO_SECUNDARIO = QColor(255, 255, 255)   # Blanco puro (sidebar, cabecera)
COLOR_SUPERFICIE       = QColor(255, 255, 255)   # Tarjetas y paneles
COLOR_SUPERFICIE_ALT   = QColor(244, 246, 251)   # Filas alternas en tablas
COLOR_SUPERFICIE_ELEV  = QColor(237, 240, 250)   # Campos de entrada, combos
COLOR_SUPERFICIE_HOVER = QColor(226, 230, 246)   # Hover en controles
COLOR_BORDE            = QColor(218, 222, 238)   # Borde suave
COLOR_BORDE_FUERTE     = QColor(192, 198, 220)   # Borde con más contraste
COLOR_TEXTO_PRIMARIO   = QColor(22,  25,  46)    # Texto principal (casi negro)
COLOR_TEXTO_SECUNDARIO = QColor(72,  79, 108)    # Texto secundario
COLOR_TEXTO_MUTED      = QColor(138, 146, 172)   # Texto atenuado
COLOR_ACENTO           = QColor(59,  91, 219)    # Azul institucional
COLOR_ACENTO_BRILLANTE = QColor(76, 110, 245)    # Azul más claro
COLOR_ACENTO_CYAN      = QColor(12, 133, 153)    # Teal para métricas
COLOR_EXITO            = QColor(47, 158,  68)    # Verde para botones de acción
COLOR_EXITO_OSCURO     = QColor(210, 248, 220)   # Verde muy suave (resaltado tabla)
COLOR_ADVERTENCIA      = QColor(230, 119,   0)   # Naranja
COLOR_ADVERTENCIA_OSC  = QColor(255, 249, 215)   # Amarillo suave
COLOR_PELIGRO          = QColor(201,  42,  42)   # Rojo para eliminar/cancelar
COLOR_PELIGRO_OSCURO   = QColor(255, 237, 237)   # Rojo muy suave (resaltado tabla)
COLOR_PURPURA          = QColor(121,  80, 242)   # Púrpura para reset
COLOR_PURPURA_OSCURO   = QColor(243, 240, 255)   # Púrpura suave

# Colores vivos para procesos/pacientes en el Gantt (sobre fondo blanco)
COLORES_PROCESOS = [
    QColor(59,  130, 246), QColor(239,  68,  68),
    QColor(34,  197,  94), QColor(234, 179,   8),
    QColor(168,  85, 247), QColor( 20, 184, 166),
    QColor(249, 115,  22), QColor( 99, 102, 241),
    QColor(236,  72, 153), QColor( 16, 185, 129),
    QColor(217, 119,   6), QColor( 14, 165, 233),
    QColor(244,  63,  94), QColor(132, 204,  22),
    QColor( 79,  70, 229), QColor(245, 158,  11),
    QColor(190,  24,  93), QColor( 21, 128,  61),
    QColor(202, 138,   4), QColor(109,  40, 217),
]


# ── Fuentes ───────────────────────────────────────────────────────────────────
def fuente_base() -> QFont:
    return QFont("Segoe UI", 9)

def fuente_pequena() -> QFont:
    return QFont("Segoe UI", 8)

def fuente_negrita() -> QFont:
    f = QFont("Segoe UI", 9)
    f.setBold(True)
    return f

def fuente_h1() -> QFont:
    f = QFont("Segoe UI", 13)
    f.setBold(True)
    return f

def fuente_h2() -> QFont:
    f = QFont("Segoe UI", 10)
    f.setBold(True)
    return f

def fuente_seccion() -> QFont:
    f = QFont("Segoe UI", 9)
    f.setBold(True)
    return f

def fuente_mono() -> QFont:
    return QFont("Consolas", 8)

def fuente_mono_grande() -> QFont:
    f = QFont("Consolas", 13)
    f.setBold(True)
    return f


def aclarar(color: QColor, delta: int) -> QColor:
    return QColor(
        min(255, color.red()   + delta),
        min(255, color.green() + delta),
        min(255, color.blue()  + delta),
    )

def oscurecer(color: QColor, delta: int) -> QColor:
    return QColor(
        max(0, color.red()   - delta),
        max(0, color.green() - delta),
        max(0, color.blue()  - delta),
    )

def a_css(color: QColor) -> str:
    return f"rgb({color.red()},{color.green()},{color.blue()})"


def obtener_estilo_global() -> str:
    bg    = a_css(COLOR_FONDO_PRIMARIO)
    surf  = a_css(COLOR_SUPERFICIE)
    selev = a_css(COLOR_SUPERFICIE_ELEV)
    shov  = a_css(COLOR_SUPERFICIE_HOVER)
    brd   = a_css(COLOR_BORDE)
    brdF  = a_css(COLOR_BORDE_FUERTE)
    txt   = a_css(COLOR_TEXTO_PRIMARIO)
    txt2  = a_css(COLOR_TEXTO_SECUNDARIO)
    txtm  = a_css(COLOR_TEXTO_MUTED)
    acc   = a_css(COLOR_ACENTO)
    accb  = a_css(COLOR_ACENTO_BRILLANTE)
    alt   = a_css(COLOR_SUPERFICIE_ALT)
    sel_bg  = "rgb(219,229,251)"
    sel_txt = "rgb(30,58,138)"

    return f"""
QWidget {{
    background-color: {bg};
    color: {txt};
    font-family: "Segoe UI";
    font-size: 9pt;
}}
QMainWindow {{
    background-color: {bg};
}}
QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: {bg};
    border: none;
}}
QSplitter::handle {{
    background-color: {brd};
    width: 1px;
    height: 1px;
}}
QComboBox {{
    background-color: {surf};
    color: {txt};
    border: 1.5px solid {brd};
    border-radius: 5px;
    padding: 3px 8px;
    min-height: 28px;
}}
QComboBox:focus {{
    border-color: {acc};
    border-width: 2px;
}}
QComboBox:hover {{
    border-color: {brdF};
}}
QComboBox QAbstractItemView {{
    background-color: {surf};
    color: {txt};
    selection-background-color: {acc};
    selection-color: white;
    border: 1px solid {brd};
    border-radius: 4px;
    outline: none;
    padding: 2px;
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QSpinBox, QDoubleSpinBox {{
    background-color: {surf};
    color: {txt};
    border: 1.5px solid {brd};
    border-radius: 5px;
    padding: 3px 6px;
    min-height: 28px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {acc};
    border-width: 2px;
}}
QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {brdF};
}}
QLineEdit {{
    background-color: {surf};
    color: {txt};
    border: 1.5px solid {brd};
    border-radius: 5px;
    padding: 4px 10px;
    min-height: 28px;
}}
QLineEdit:focus {{
    border-color: {acc};
    border-width: 2px;
}}
QLineEdit:hover {{
    border-color: {brdF};
}}
QTableWidget {{
    background-color: {surf};
    color: {txt};
    gridline-color: {brd};
    border: none;
    outline: none;
}}
QTableWidget::item {{
    padding: 5px 8px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {sel_bg};
    color: {sel_txt};
}}
QTableWidget::item:alternate {{
    background-color: {alt};
}}
QHeaderView::section {{
    background-color: {bg};
    color: {txt2};
    border: none;
    border-bottom: 2px solid {brd};
    padding: 7px 8px;
    font-weight: bold;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 7px;
    border: none;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {brdF};
    border-radius: 3px;
    min-height: 28px;
}}
QScrollBar::handle:vertical:hover {{
    background: {txtm};
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 7px;
    border: none;
    margin: 2px;
}}
QScrollBar::handle:horizontal {{
    background: {brdF};
    border-radius: 3px;
    min-width: 28px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {txtm};
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}
QLabel {{
    background: transparent;
    color: {txt};
}}
QMessageBox {{
    background-color: {surf};
}}
QMessageBox QLabel {{
    color: {txt};
}}
QMessageBox QPushButton {{
    background-color: {acc};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 7px 20px;
    min-width: 88px;
    font-weight: bold;
}}
QMessageBox QPushButton:hover {{
    background-color: {accb};
}}
QDialog {{
    background-color: {surf};
}}
QToolTip {{
    background-color: rgb(30,33,52);
    color: white;
    border: none;
    padding: 5px 9px;
    border-radius: 4px;
    font-size: 8.5pt;
}}
"""


def css_boton(color_fondo: QColor, color_borde: QColor = None) -> str:
    if color_borde is None:
        color_borde = oscurecer(color_fondo, 22)
    fondo = a_css(color_fondo)
    borde = a_css(color_borde)
    hover = a_css(aclarar(color_fondo, 20))
    click = a_css(oscurecer(color_fondo, 22))
    return f"""
QPushButton {{
    background-color: {fondo};
    color: white;
    border: 1px solid {borde};
    border-radius: 5px;
    padding: 5px 12px;
    font-weight: bold;
    font-size: 8.5pt;
}}
QPushButton:hover {{
    background-color: {hover};
}}
QPushButton:pressed {{
    background-color: {click};
}}
QPushButton:disabled {{
    background-color: {a_css(COLOR_SUPERFICIE_ELEV)};
    color: {a_css(COLOR_TEXTO_MUTED)};
    border-color: {a_css(COLOR_BORDE)};
}}
"""
