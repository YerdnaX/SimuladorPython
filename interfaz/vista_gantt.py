from dataclasses import dataclass
from typing import Dict, List, Optional

from PySide6.QtWidgets import QWidget, QScrollBar
from PySide6.QtCore import Qt, QRect, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QLinearGradient,
    QPainterPath, QFontMetrics, QRadialGradient,
)

from interfaz.tema import (
    COLOR_FONDO_PRIMARIO, COLOR_SUPERFICIE, COLOR_SUPERFICIE_ALT,
    COLOR_BORDE, COLOR_BORDE_FUERTE, COLOR_TEXTO_PRIMARIO,
    COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_MUTED, COLOR_ACENTO,
    fuente_seccion, fuente_pequena, aclarar, oscurecer,
)
from modelos.segmento_ejecucion import SegmentoEjecucion


# ── Conversión de unidades de tiempo a formato horario ───────────────────────
_HORA_BASE_MIN = 7 * 60   # 7:00 AM en minutos
_MIN_POR_UNIDAD = 10      # cada unidad = 10 minutos


def tick_a_hora(t: int) -> str:
    """Unidad de tiempo → 'HH:MM'  (base 07:00, cada unidad = 10 min)."""
    total = _HORA_BASE_MIN + t * _MIN_POR_UNIDAD
    return f"{total // 60:02d}:{total % 60:02d}"


def tick_a_duracion(t) -> str:
    """Unidades de tiempo → duración legible ('Xh Ymin' o 'Y min').
    Acepta int o float; redondea al minuto más cercano."""
    minutos = round(t * _MIN_POR_UNIDAD)
    if minutos == 0:
        return "0 min"
    h, m = divmod(minutos, 60)
    if h and m:
        return f"{h}h {m:02d}min"
    if h:
        return f"{h}h"
    return f"{m} min"


# ── Constantes de diseño ──────────────────────────────────────────────────────
_MARGEN_IZQ    = 136   # Ancho del panel de nombres
_ALTO_FILA     = 46    # Alto de cada fila de proceso
_MARGEN_TOP    = 40    # Alto del área de regla/encabezado
_PX_POR_UNIDAD = 34    # Píxeles por unidad de tiempo

# Colores del Gantt claro
_CL_FONDO      = QColor(255, 255, 255)   # Fondo blanco
_CL_REGLA      = QColor(248, 249, 252)   # Fondo de la regla
_CL_FILA_PAR   = QColor(255, 255, 255)   # Fila par
_CL_FILA_IMPAR = QColor(249, 250, 254)   # Fila impar (levemente azulado)
_CL_NOMBRES    = QColor(250, 251, 255)   # Panel de nombres
_CL_GRID_MIN   = QColor(234, 237, 247)   # Línea de cuadrícula menor
_CL_GRID_MAJ   = QColor(210, 216, 238)   # Línea de cuadrícula mayor
_CL_TICK_MIN   = QColor(185, 192, 218)   # Marca menor
_CL_TICK_MAJ   = QColor(130, 140, 175)   # Marca mayor
_CL_NUM_MIN    = QColor(170, 178, 205)   # Número menor
_CL_NUM_MAJ    = QColor(90,  100, 140)   # Número mayor
_CL_SEP        = QColor(208, 213, 234)   # Separador vertical nombres/timeline
_CL_CURSOR     = QColor(59,   91, 219)   # Azul institucional para cursor
_CL_PH_TIT    = QColor(196, 202, 225)   # Placeholder título
_CL_PH_SUB    = QColor(214, 218, 235)   # Placeholder subtítulo


@dataclass
class _BloqueDibujado:
    proceso: str
    inicio: int
    fin_actual: int
    fin_real: int
    color: QColor
    es_idle: bool = False


class VistaGantt(QWidget):
    """
    Diagrama de Gantt con tema claro institucional.
    Panel izquierdo: nombres con chip de color.
    Timeline: cuadrícula suave, barras redondeadas de color vivo,
    cursor azul, regla compacta con marcas por unidad.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setStyleSheet("background: white;")

        self._segmentos: List[SegmentoEjecucion] = []
        self._mapa_colores: Dict[str, QColor] = {}
        self._orden_procesos: List[str] = []
        self._tiempo_actual = 0
        self._tiempo_max = 0
        self._bloques: List[_BloqueDibujado] = []
        self._bloque_actual: Optional[_BloqueDibujado] = None

        self._scroll = QScrollBar(Qt.Horizontal, self)
        self._scroll.setFixedHeight(12)
        self._scroll.setStyleSheet("""
            QScrollBar:horizontal {
                background: rgb(244,246,251);
                height: 12px;
                border: none;
                border-top: 1px solid rgb(218,222,238);
            }
            QScrollBar::handle:horizontal {
                background: rgb(192,198,220);
                border-radius: 5px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgb(140,148,172);
            }
            QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
        """)
        self._scroll.valueChanged.connect(self.update)
        self._actualizar_scroll()

    # ── API PÚBLICA ───────────────────────────────────────────────────────────

    def inicializar(self, segmentos: List[SegmentoEjecucion],
                    mapa_colores: Dict[str, QColor]) -> None:
        self._segmentos = segmentos
        self._mapa_colores = mapa_colores
        self._orden_procesos = list(dict.fromkeys(s.nombre_proceso for s in segmentos))
        self._tiempo_max = max((s.fin for s in segmentos), default=0)
        self._tiempo_actual = 0
        self._bloques.clear()
        self._bloque_actual = None
        self._actualizar_scroll()
        self.update()

    def avanzar_tick(self, proceso: str, tick_fin: int, color: QColor) -> None:
        self._tiempo_actual = tick_fin

        seg = next(
            (s for s in self._segmentos
             if s.nombre_proceso == proceso and s.fin >= tick_fin and s.inicio < tick_fin),
            None,
        )

        if seg is not None:
            self._bloque_actual = _BloqueDibujado(
                proceso=proceso,
                inicio=seg.inicio,
                fin_actual=tick_fin,
                fin_real=seg.fin,
                color=color,
            )

        if (self._bloque_actual is not None and
                self._bloque_actual.fin_actual >= self._bloque_actual.fin_real):
            self._bloques.append(self._bloque_actual)
            self._bloque_actual = None

        cursor_x = _MARGEN_IZQ + self._tiempo_actual * _PX_POR_UNIDAD - self._scroll.value()
        if cursor_x > self.width() - 80:
            nuevo = min(self._scroll.maximum(),
                        self._scroll.value() + _PX_POR_UNIDAD * 3)
            self._scroll.setValue(nuevo)

        self.update()

    def resetear(self) -> None:
        self._segmentos.clear()
        self._mapa_colores.clear()
        self._orden_procesos.clear()
        self._bloques.clear()
        self._bloque_actual = None
        self._tiempo_actual = 0
        self._tiempo_max = 0
        self._scroll.setValue(0)
        self._actualizar_scroll()
        self.update()

    # ── REDIMENSIONAMIENTO ────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scroll.setGeometry(0, self.height() - 12, self.width(), 12)
        self._actualizar_scroll()

    def _actualizar_scroll(self) -> None:
        total = _MARGEN_IZQ + self._tiempo_max * _PX_POR_UNIDAD + 80
        maximo = max(0, total - self.width() + 20)
        self._scroll.setMaximum(maximo)

    # ── PINTADO ───────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        scroll_x = self._scroll.value()
        panel_h = self.height() - 12

        # Fondo blanco general
        painter.fillRect(0, 0, self.width(), panel_h, _CL_FONDO)

        if not self._orden_procesos:
            self._dibujar_placeholder(painter, panel_h)
            return

        self._dibujar_regla(painter, scroll_x)
        self._dibujar_filas(painter, scroll_x)
        self._dibujar_bloques(painter, scroll_x)
        self._dibujar_cursor(painter, scroll_x, panel_h)
        self._dibujar_panel_nombres(painter, panel_h)

    # ── SECCIONES DE DIBUJO ───────────────────────────────────────────────────

    @staticmethod
    def _tick_a_hora(t: int) -> str:
        return tick_a_hora(t)

    def _dibujar_regla(self, painter: QPainter, scroll_x: int) -> None:
        alto_total = _MARGEN_TOP + len(self._orden_procesos) * _ALTO_FILA

        # Fondo de la regla
        painter.fillRect(0, 0, self.width(), _MARGEN_TOP, _CL_REGLA)

        # Fondo del rincón superior izquierdo (panel de nombres en la regla)
        painter.fillRect(0, 0, _MARGEN_IZQ, _MARGEN_TOP, _CL_NOMBRES)

        # Etiqueta "PROCESO" centrada en el panel de nombres
        f_label = QFont("Segoe UI", 7)
        f_label.setBold(True)
        f_label.setLetterSpacing(QFont.AbsoluteSpacing, 0.8)
        painter.setFont(f_label)
        painter.setPen(_CL_TICK_MAJ)
        painter.drawText(
            QRect(0, 0, _MARGEN_IZQ - 1, _MARGEN_TOP),
            Qt.AlignCenter, "PROCESO"
        )

        # Fuentes para marcas de hora y de 10 min
        f_hora  = QFont("Consolas", 7)
        f_hora.setBold(True)
        f_min   = QFont("Consolas", 6)

        for t in range(self._tiempo_max + 2):
            x = _MARGEN_IZQ + t * _PX_POR_UNIDAD - scroll_x
            if x < _MARGEN_IZQ - 5 or x > self.width() + 5:
                continue

            es_hora       = (t % 6 == 0)   # cada 60 min → marca mayor
            es_media_hora = (t % 3 == 0)   # cada 30 min → marca media

            # Línea de cuadrícula sobre filas
            if es_hora:
                grid_color = _CL_GRID_MAJ
            elif es_media_hora:
                grid_color = QColor(220, 225, 242)
            else:
                grid_color = _CL_GRID_MIN
            painter.setPen(QPen(grid_color, 1))
            painter.drawLine(x, _MARGEN_TOP, x, alto_total)

            # Marca vertical en la regla
            if es_hora:
                tick_h    = 12
                tick_pen  = _CL_TICK_MAJ
            elif es_media_hora:
                tick_h    = 8
                tick_pen  = _CL_TICK_MIN
            else:
                tick_h    = 4
                tick_pen  = QColor(205, 210, 230)
            painter.setPen(QPen(tick_pen, 1))
            painter.drawLine(x, _MARGEN_TOP - tick_h, x, _MARGEN_TOP)

            # Etiqueta de hora (HH:MM)
            etiqueta = self._tick_a_hora(t)
            if es_hora:
                painter.setFont(f_hora)
                painter.setPen(_CL_NUM_MAJ)
                ancho_txt = 34
                y_txt = 3
            elif es_media_hora:
                painter.setFont(f_min)
                painter.setPen(_CL_NUM_MIN)
                ancho_txt = 30
                y_txt = 6
            else:
                painter.setFont(f_min)
                painter.setPen(QColor(200, 206, 228))
                ancho_txt = 28
                y_txt = 9

            painter.drawText(
                QRect(x - ancho_txt // 2, y_txt, ancho_txt, 16),
                Qt.AlignCenter, etiqueta
            )

        # Línea inferior de la regla
        painter.setPen(QPen(_CL_SEP, 1))
        painter.drawLine(_MARGEN_IZQ, _MARGEN_TOP, self.width(), _MARGEN_TOP)

    def _dibujar_filas(self, painter: QPainter, scroll_x: int) -> None:
        for i, nombre in enumerate(self._orden_procesos):
            y = _MARGEN_TOP + i * _ALTO_FILA
            color_bg = _CL_FILA_PAR if i % 2 == 0 else _CL_FILA_IMPAR
            painter.fillRect(_MARGEN_IZQ, y, self.width() - _MARGEN_IZQ, _ALTO_FILA, color_bg)

            # Línea divisora inferior muy sutil
            painter.setPen(QPen(_CL_GRID_MIN, 1))
            painter.drawLine(_MARGEN_IZQ, y + _ALTO_FILA - 1,
                             self.width(), y + _ALTO_FILA - 1)

            # Columna de nombres
            painter.fillRect(0, y, _MARGEN_IZQ - 1, _ALTO_FILA, _CL_NOMBRES)

            # Chip de color (círculo pequeño)
            color_proc = self._mapa_colores.get(nombre, QColor(160, 160, 160))
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(color_proc)
            painter.setPen(Qt.NoPen)
            cy = y + _ALTO_FILA // 2
            painter.drawEllipse(9, cy - 5, 10, 10)

            # Nombre del proceso
            f_nombre = QFont("Segoe UI", 8)
            f_nombre.setBold(True)
            painter.setFont(f_nombre)
            painter.setPen(COLOR_TEXTO_PRIMARIO)
            painter.drawText(
                QRect(26, y, _MARGEN_IZQ - 30, _ALTO_FILA),
                Qt.AlignVCenter | Qt.AlignLeft,
                nombre
            )

    def _dibujar_bloques(self, painter: QPainter, scroll_x: int) -> None:
        for bloque in self._bloques:
            self._dibujar_bloque(painter, bloque, bloque.fin_actual, scroll_x)
        if self._bloque_actual is not None:
            self._dibujar_bloque(painter, self._bloque_actual,
                                 self._bloque_actual.fin_actual, scroll_x)

    def _dibujar_bloque(self, painter: QPainter, bloque: _BloqueDibujado,
                        fin_dibujado: int, scroll_x: int) -> None:
        if bloque.proceso not in self._orden_procesos:
            return
        fila_idx = self._orden_procesos.index(bloque.proceso)

        PAD_V = 8   # Margen vertical dentro de la fila
        PAD_H = 1   # Margen horizontal entre unidades
        y = _MARGEN_TOP + fila_idx * _ALTO_FILA + PAD_V
        h = _ALTO_FILA - PAD_V * 2
        x = _MARGEN_IZQ + bloque.inicio * _PX_POR_UNIDAD - scroll_x + PAD_H
        w = (fin_dibujado - bloque.inicio) * _PX_POR_UNIDAD - PAD_H * 2

        if w <= 0 or x + w < _MARGEN_IZQ or x > self.width():
            return

        x_clip = max(x, _MARGEN_IZQ)
        if x_clip > x:
            w -= (x_clip - x)
            x = x_clip

        rect = QRectF(x, y, max(w, 2), h)
        radio = min(6, h // 3)

        path = QPainterPath()
        path.addRoundedRect(rect, radio, radio)

        # Color base plano del bloque
        color = bloque.color
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillPath(path, color)

        # Brillo sutil en el borde superior (línea blanca semitransparente)
        if rect.width() > 6:
            brillo_rect = QRectF(rect.x() + 2, rect.y() + 2,
                                 rect.width() - 4, max(1, rect.height() * 0.35))
            brillo_path = QPainterPath()
            brillo_path.addRoundedRect(brillo_rect, radio - 1, radio - 1)
            brillo_color = QColor(255, 255, 255, 55)
            painter.fillPath(brillo_path, brillo_color)

        # Borde del bloque (ligeramente más oscuro que el color)
        borde_color = oscurecer(color, 30)
        borde_color.setAlpha(160)
        painter.setPen(QPen(borde_color, 1.0))
        painter.drawPath(path)

        # Etiqueta centrada (texto blanco, negrita)
        if rect.width() > 22:
            f_etiqueta = QFont("Segoe UI", 8)
            f_etiqueta.setBold(True)
            painter.setFont(f_etiqueta)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(rect.toRect(), Qt.AlignCenter, bloque.proceso)

    def _dibujar_cursor(self, painter: QPainter, scroll_x: int, panel_h: int) -> None:
        cursor_x = _MARGEN_IZQ + self._tiempo_actual * _PX_POR_UNIDAD - scroll_x
        if _MARGEN_IZQ < cursor_x < self.width():
            bottom = _MARGEN_TOP + len(self._orden_procesos) * _ALTO_FILA

            # Línea discontinua azul (más visible que en tema oscuro)
            pen = QPen(_CL_CURSOR, 1.5, Qt.DashLine)
            pen.setDashPattern([4, 3])
            painter.setPen(pen)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.drawLine(cursor_x, _MARGEN_TOP - 2, cursor_x, bottom)

            # Triángulo marcador en la regla
            from PySide6.QtGui import QPolygonF
            from PySide6.QtCore import QPointF
            tri = QPolygonF([
                QPointF(cursor_x,       _MARGEN_TOP),
                QPointF(cursor_x - 5.0, _MARGEN_TOP - 9),
                QPointF(cursor_x + 5.0, _MARGEN_TOP - 9),
            ])
            painter.setPen(Qt.NoPen)
            painter.setBrush(_CL_CURSOR)
            painter.drawPolygon(tri)

            # Pequeño círculo en la parte inferior del cursor
            painter.setBrush(_CL_CURSOR)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cursor_x - 3, bottom - 4, 6, 6)

    def _dibujar_panel_nombres(self, painter: QPainter, panel_h: int) -> None:
        # Sombra suave a la derecha del panel de nombres
        grad = QLinearGradient(_MARGEN_IZQ - 1, 0, _MARGEN_IZQ + 8, 0)
        grad.setColorAt(0.0, QColor(0, 0, 0, 22))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(_MARGEN_IZQ - 1, _MARGEN_TOP,
                         9, len(self._orden_procesos) * _ALTO_FILA, grad)

        # Línea divisoria sólida
        painter.setPen(QPen(_CL_SEP, 1))
        painter.drawLine(_MARGEN_IZQ - 1, 0, _MARGEN_IZQ - 1, panel_h)

    def _dibujar_placeholder(self, painter: QPainter, panel_h: int) -> None:
        # Círculo decorativo de fondo
        cx = self.width() // 2
        cy = panel_h // 2 - 10

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(240, 243, 252))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - 36, cy - 40, 72, 72)

        # Símbolo de Gantt (tres barras horizontales dentro del círculo)
        painter.setBrush(QColor(192, 200, 228))
        painter.setPen(Qt.NoPen)
        for i, (bx, bw) in enumerate([(cx - 18, 36), (cx - 18, 26), (cx - 18, 20)]):
            by = cy - 22 + i * 14
            path = QPainterPath()
            path.addRoundedRect(QRectF(bx, by, bw, 8), 4, 4)
            painter.fillPath(path, QColor(180, 190, 225))

        # Título
        f_tit = QFont("Segoe UI", 12)
        f_tit.setBold(True)
        painter.setFont(f_tit)
        painter.setPen(_CL_PH_TIT)
        fm = QFontMetrics(f_tit)
        txt1 = "Diagrama de Gantt"
        painter.drawText((self.width() - fm.horizontalAdvance(txt1)) // 2, cy + 52, txt1)

        f_sub = QFont("Segoe UI", 9)
        painter.setFont(f_sub)
        painter.setPen(_CL_PH_SUB)
        fm2 = QFontMetrics(f_sub)
        txt2 = "Presione  ▶ Ejecutar  para iniciar la simulación"
        painter.drawText((self.width() - fm2.horizontalAdvance(txt2)) // 2, cy + 76, txt2)
