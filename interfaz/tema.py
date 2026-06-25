from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtCore import Qt


# ── Colores del tema oscuro (equivalentes a AppTheme de WinForms) ────────────
COLOR_FONDO_PRIMARIO   = QColor(13,  15,  22)
COLOR_FONDO_SECUNDARIO = QColor(18,  20,  30)
COLOR_SUPERFICIE       = QColor(24,  27,  40)
COLOR_SUPERFICIE_ALT   = QColor(29,  32,  48)
COLOR_SUPERFICIE_ELEV  = QColor(36,  40,  58)
COLOR_SUPERFICIE_HOVER = QColor(46,  51,  74)
COLOR_BORDE            = QColor(50,  55,  80)
COLOR_BORDE_FUERTE     = QColor(72,  80, 118)
COLOR_TEXTO_PRIMARIO   = QColor(225, 228, 252)
COLOR_TEXTO_SECUNDARIO = QColor(128, 138, 175)
COLOR_TEXTO_MUTED      = QColor(68,  76, 110)
COLOR_ACENTO           = QColor(75,  108, 212)
COLOR_ACENTO_BRILLANTE = QColor(115, 150, 245)
COLOR_ACENTO_CYAN      = QColor(52,  196, 182)
COLOR_EXITO            = QColor(38,  168, 104)
COLOR_EXITO_OSCURO     = QColor(16,   76,  44)
COLOR_ADVERTENCIA      = QColor(215, 152,  36)
COLOR_ADVERTENCIA_OSC  = QColor(84,   58,   8)
COLOR_PELIGRO          = QColor(205,  58,  58)
COLOR_PELIGRO_OSCURO   = QColor(88,   20,  20)
COLOR_PURPURA          = QColor(124,  84, 224)
COLOR_PURPURA_OSCURO   = QColor(52,   28,  96)

# Colores para los procesos/pacientes en el Gantt
COLORES_PROCESOS = [
    QColor(70,  130, 180), QColor(220,  80,  80),
    QColor(60,  160,  60), QColor(200, 140,   0),
    QColor(150,  60, 200), QColor(  0, 160, 160),
    QColor(220, 100,  40), QColor(100, 100, 200),
    QColor(180,  60, 120), QColor( 40, 160, 100),
    QColor(160,  80,  40), QColor( 80, 140, 200),
    QColor(200,  60, 160), QColor(100, 180,  60),
    QColor( 60,  80, 180), QColor(180, 120,  60),
    QColor(120,  40,  80), QColor( 40, 120,  80),
    QColor(160, 160,  40), QColor( 80,  60, 160),
]


# ── Fuentes del tema ──────────────────────────────────────────────────────────
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


# Retorna un color más claro sumando el delta a cada canal RGB.
def aclarar(color: QColor, delta: int) -> QColor:
    return QColor(
        min(255, color.red()   + delta),
        min(255, color.green() + delta),
        min(255, color.blue()  + delta),
    )


# Retorna un color más oscuro restando el delta a cada canal RGB.
def oscurecer(color: QColor, delta: int) -> QColor:
    return QColor(
        max(0, color.red()   - delta),
        max(0, color.green() - delta),
        max(0, color.blue()  - delta),
    )


# Convierte un QColor a cadena CSS "rgb(r, g, b)".
def a_css(color: QColor) -> str:
    return f"rgb({color.red()},{color.green()},{color.blue()})"


# Devuelve la hoja de estilos CSS global para toda la aplicación.
def obtener_estilo_global() -> str:
    bg   = a_css(COLOR_FONDO_PRIMARIO)
    bg2  = a_css(COLOR_FONDO_SECUNDARIO)
    surf = a_css(COLOR_SUPERFICIE)
    selev = a_css(COLOR_SUPERFICIE_ELEV)
    shov = a_css(COLOR_SUPERFICIE_HOVER)
    brd  = a_css(COLOR_BORDE)
    txt  = a_css(COLOR_TEXTO_PRIMARIO)
    txt2 = a_css(COLOR_TEXTO_SECUNDARIO)
    txtm = a_css(COLOR_TEXTO_MUTED)
    acc  = a_css(COLOR_ACENTO)
    accb = a_css(COLOR_ACENTO_BRILLANTE)
    cyan = a_css(COLOR_ACENTO_CYAN)

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
    width: 2px;
    height: 2px;
}}
QComboBox {{
    background-color: {selev};
    color: {txt};
    border: 1px solid {brd};
    border-radius: 3px;
    padding: 3px 6px;
    min-height: 24px;
}}
QComboBox:focus {{
    border-color: {acc};
}}
QComboBox QAbstractItemView {{
    background-color: {selev};
    color: {txt};
    selection-background-color: {acc};
    border: 1px solid {brd};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QSpinBox, QDoubleSpinBox {{
    background-color: {selev};
    color: {txt};
    border: 1px solid {brd};
    border-radius: 3px;
    padding: 3px 6px;
    min-height: 24px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {acc};
}}
QLineEdit {{
    background-color: {selev};
    color: {txt};
    border: 1px solid {brd};
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 24px;
}}
QLineEdit:focus {{
    border-color: {acc};
}}
QTableWidget {{
    background-color: {surf};
    color: {txt};
    gridline-color: {brd};
    border: none;
    outline: none;
}}
QTableWidget::item {{
    padding: 4px 6px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: {acc};
    color: white;
}}
QTableWidget::item:alternate {{
    background-color: {a_css(COLOR_SUPERFICIE_ALT)};
}}
QHeaderView::section {{
    background-color: {selev};
    color: {accb};
    border: none;
    border-bottom: 1px solid {brd};
    padding: 5px 8px;
    font-weight: bold;
}}
QScrollBar:vertical {{
    background: {surf};
    width: 10px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {a_css(COLOR_BORDE_FUERTE)};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar:horizontal {{
    background: {surf};
    height: 10px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {a_css(COLOR_BORDE_FUERTE)};
    border-radius: 5px;
    min-width: 20px;
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
    background-color: {selev};
    color: {txt};
    border: 1px solid {brd};
    border-radius: 4px;
    padding: 6px 18px;
    min-width: 80px;
}}
QMessageBox QPushButton:hover {{
    background-color: {shov};
    border-color: {acc};
}}
QDialog {{
    background-color: {surf};
}}
QToolTip {{
    background-color: {selev};
    color: {txt};
    border: 1px solid {brd};
    padding: 4px 8px;
}}
"""


# Devuelve el CSS de un botón de acción según color base.
def css_boton(color_fondo: QColor, color_borde: QColor = None) -> str:
    if color_borde is None:
        color_borde = aclarar(color_fondo, 38)
    fondo = a_css(color_fondo)
    borde = a_css(color_borde)
    hover = a_css(aclarar(color_fondo, 22))
    click = a_css(oscurecer(color_fondo, 18))
    return f"""
QPushButton {{
    background-color: {fondo};
    color: white;
    border: 1px solid {borde};
    border-radius: 4px;
    padding: 5px 10px;
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
    background-color: {a_css(oscurecer(color_fondo, 30))};
    color: {a_css(COLOR_TEXTO_MUTED)};
    border-color: {a_css(oscurecer(color_borde, 20))};
}}
"""
