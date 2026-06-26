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
_MIN_POR_UNIDAD = 1       # cada unidad (tick) = 1 minuto


def tick_a_hora(t: int) -> str:
    """Unidad de tiempo → 'HH:MM'  (base 07:00, cada unidad = 1 min)."""
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
_MARGEN_IZQ    = 176   # Ancho del panel de nombres
_ALTO_FILA     = 52    # Alto de cada fila de proceso
_MARGEN_TOP    = 56    # Alto del área de regla/encabezado
_PX_POR_UNIDAD = 28    # Píxeles por unidad de tiempo

# Paleta "planner" cálida para un aspecto totalmente distinto.
_CL_FONDO      = QColor(252, 248, 238)
_CL_REGLA_A    = QColor(255, 245, 222)
_CL_REGLA_B    = QColor(252, 235, 195)
_CL_FILA_PAR   = QColor(255, 252, 245)
_CL_FILA_IMPAR = QColor(250, 244, 232)
_CL_NOMBRES    = QColor(245, 233, 210)
_CL_GRID_MIN   = QColor(236, 223, 194)
_CL_GRID_MAJ   = QColor(210, 184, 138)
_CL_TICK_MIN   = QColor(187, 151, 102)
_CL_TICK_MAJ   = QColor(145, 104, 54)
_CL_NUM_MIN    = QColor(130, 104, 67)
_CL_NUM_MAJ    = QColor(92, 67, 36)
_CL_SEP        = QColor(202, 173, 132)
_CL_CURSOR     = QColor(225, 122, 53)
_CL_PH_TIT     = QColor(166, 140, 103)
_CL_PH_SUB     = QColor(188, 165, 132)


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
    Diagrama de Gantt con estética tipo planner de papel.
    Panel izquierdo en tono arena, regla superior en degradado cálido,
    barras tipo píldora y cursor vertical naranja.
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
        self._scroll.setFixedHeight(14)
        self._scroll.setStyleSheet("""
            QScrollBar:horizontal {
                background: rgb(243,232,210);
                height: 14px;
                border: none;
                border-top: 1px solid rgb(202,173,132);
            }
            QScrollBar::handle:horizontal {
                background: rgb(219,128,54);
                border-radius: 6px;
                min-width: 30px;
                margin: 2px 3px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgb(196,103,34);
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
        self._scroll.setGeometry(0, self.height() - 14, self.width(), 14)
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
        panel_h = self.height() - 14

        # Fondo cálido general
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

        grad_regla = QLinearGradient(0, 0, 0, _MARGEN_TOP)
        grad_regla.setColorAt(0.0, _CL_REGLA_A)
        grad_regla.setColorAt(1.0, _CL_REGLA_B)
        painter.fillRect(0, 0, self.width(), _MARGEN_TOP, grad_regla)

        painter.fillRect(0, 0, _MARGEN_IZQ, _MARGEN_TOP, _CL_NOMBRES)

        f_label = QFont("Segoe UI", 8)
        f_label.setBold(True)
        f_label.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        painter.setFont(f_label)
        painter.setPen(_CL_TICK_MAJ)
        painter.drawText(
            QRect(0, 0, _MARGEN_IZQ - 1, _MARGEN_TOP),
            Qt.AlignCenter, "LINEA DE PROCESOS"
        )

        f_hora  = QFont("Consolas", 8)
        f_hora.setBold(True)
        f_min   = QFont("Consolas", 7)

        for t in range(self._tiempo_max + 2):
            x = _MARGEN_IZQ + t * _PX_POR_UNIDAD - scroll_x
            if x < _MARGEN_IZQ - 5 or x > self.width() + 5:
                continue

            es_hora = (t % 60 == 0)
            es_quince = (t % 15 == 0)
            es_cinco = (t % 5 == 0)

            if es_hora:
                grid_color = _CL_GRID_MAJ
            elif es_quince:
                grid_color = QColor(224, 200, 156)
            elif es_cinco:
                grid_color = QColor(232, 213, 178)
            else:
                grid_color = _CL_GRID_MIN
            painter.setPen(QPen(grid_color, 1))
            painter.drawLine(x, _MARGEN_TOP, x, alto_total)

            if es_hora:
                tick_h    = 16
                tick_pen  = _CL_TICK_MAJ
            elif es_quince:
                tick_h    = 11
                tick_pen  = _CL_TICK_MIN
            elif es_cinco:
                tick_h    = 7
                tick_pen  = QColor(177, 145, 97)
            else:
                tick_h    = 4
                tick_pen  = QColor(210, 186, 145)
            painter.setPen(QPen(tick_pen, 1))
            painter.drawLine(x, _MARGEN_TOP - tick_h, x, _MARGEN_TOP)

            if es_hora:
                painter.setFont(f_hora)
                painter.setPen(_CL_NUM_MAJ)
                painter.drawText(QRect(x - 30, 5, 60, 18), Qt.AlignCenter, self._tick_a_hora(t))
            elif es_quince:
                painter.setFont(f_min)
                painter.setPen(_CL_NUM_MIN)
                painter.drawText(QRect(x - 20, 9, 40, 14), Qt.AlignCenter, self._tick_a_hora(t)[-2:])

        painter.setPen(QPen(_CL_SEP, 1))
        painter.drawLine(_MARGEN_IZQ, _MARGEN_TOP, self.width(), _MARGEN_TOP)

    def _dibujar_filas(self, painter: QPainter, scroll_x: int) -> None:
        for i, nombre in enumerate(self._orden_procesos):
            y = _MARGEN_TOP + i * _ALTO_FILA
            color_bg = _CL_FILA_PAR if i % 2 == 0 else _CL_FILA_IMPAR
            painter.fillRect(_MARGEN_IZQ, y, self.width() - _MARGEN_IZQ, _ALTO_FILA, color_bg)
            painter.fillRect(0, y, _MARGEN_IZQ - 1, _ALTO_FILA, _CL_NOMBRES)

            painter.setPen(QPen(_CL_GRID_MIN, 1))
            painter.drawLine(_MARGEN_IZQ, y + _ALTO_FILA - 1, self.width(), y + _ALTO_FILA - 1)

            color_proc = self._mapa_colores.get(nombre, QColor(160, 160, 160))
            painter.setRenderHint(QPainter.Antialiasing)
            chip = QRectF(10, y + 11, 22, _ALTO_FILA - 22)
            chip_grad = QLinearGradient(chip.left(), chip.top(), chip.right(), chip.bottom())
            chip_grad.setColorAt(0.0, aclarar(color_proc, 45))
            chip_grad.setColorAt(1.0, oscurecer(color_proc, 15))
            painter.setBrush(chip_grad)
            painter.setPen(QPen(oscurecer(color_proc, 28), 1))
            painter.drawRoundedRect(chip, 6, 6)

            cy = y + _ALTO_FILA // 2
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 180))
            painter.drawEllipse(18, cy - 2, 3, 3)

            f_nombre = QFont("Segoe UI", 9)
            f_nombre.setBold(True)
            painter.setFont(f_nombre)
            painter.setPen(_CL_NUM_MAJ)
            painter.drawText(
                QRect(42, y, _MARGEN_IZQ - 48, _ALTO_FILA),
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
        es_en_progreso = fin_dibujado < bloque.fin_real

        path = QPainterPath()
        path.addRoundedRect(rect, radio, radio)

        color = bloque.color
        grad = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        grad.setColorAt(0.0, aclarar(color, 36))
        grad.setColorAt(0.52, color)
        grad.setColorAt(1.0, oscurecer(color, 22))
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillPath(path, grad)

        # En progreso: mostrar "cuadros" por unidad para evidenciar el llenado.
        if es_en_progreso and rect.width() > (_PX_POR_UNIDAD * 0.45):
            inicio_visible = max(bloque.inicio, (scroll_x - _MARGEN_IZQ) // _PX_POR_UNIDAD - 1)
            for t in range(inicio_visible, fin_dibujado):
                celda_x = _MARGEN_IZQ + t * _PX_POR_UNIDAD - scroll_x + PAD_H + 1
                celda_w = _PX_POR_UNIDAD - 4
                x0 = max(celda_x, rect.x() + 1)
                x1 = min(celda_x + celda_w, rect.x() + rect.width() - 1)
                if x1 <= x0:
                    continue

                celda = QRectF(x0, rect.y() + 1.5, x1 - x0, max(2.0, rect.height() - 3.0))
                celda_path = QPainterPath()
                celda_path.addRoundedRect(celda, 3, 3)

                celda_grad = QLinearGradient(celda.left(), celda.top(), celda.right(), celda.bottom())
                if (t - bloque.inicio) % 2 == 0:
                    celda_grad.setColorAt(0.0, QColor(255, 255, 255, 60))
                    celda_grad.setColorAt(1.0, QColor(0, 0, 0, 18))
                else:
                    celda_grad.setColorAt(0.0, QColor(255, 255, 255, 35))
                    celda_grad.setColorAt(1.0, QColor(0, 0, 0, 10))
                painter.fillPath(celda_path, celda_grad)

                painter.setPen(QPen(QColor(255, 255, 255, 45), 0.8))
                painter.drawPath(celda_path)

            # Frente de avance del llenado.
            frente_x = _MARGEN_IZQ + fin_dibujado * _PX_POR_UNIDAD - scroll_x
            if rect.left() < frente_x < rect.right():
                glow = QLinearGradient(frente_x - 12, 0, frente_x + 8, 0)
                glow.setColorAt(0.0, QColor(255, 255, 255, 0))
                glow.setColorAt(0.45, QColor(255, 255, 255, 95))
                glow.setColorAt(1.0, QColor(255, 255, 255, 0))
                painter.fillRect(QRectF(max(rect.left(), frente_x - 12), rect.top(), 20, rect.height()), glow)

        if rect.width() > 6:
            brillo_rect = QRectF(rect.x() + 2, rect.y() + 2,
                                 rect.width() - 4, max(1, rect.height() * 0.35))
            brillo_path = QPainterPath()
            brillo_path.addRoundedRect(brillo_rect, radio - 1, radio - 1)
            brillo_color = QColor(255, 255, 255, 70)
            painter.fillPath(brillo_path, brillo_color)

        borde_color = oscurecer(color, 34)
        borde_color.setAlpha(190)
        painter.setPen(QPen(borde_color, 1.3))
        painter.drawPath(path)

        if rect.width() > 22:
            f_etiqueta = QFont("Segoe UI", 8)
            f_etiqueta.setBold(True)
            painter.setFont(f_etiqueta)
            painter.setPen(QColor(26, 18, 6))
            painter.drawText(rect.toRect(), Qt.AlignCenter, bloque.proceso)

    def _dibujar_cursor(self, painter: QPainter, scroll_x: int, panel_h: int) -> None:
        cursor_x = _MARGEN_IZQ + self._tiempo_actual * _PX_POR_UNIDAD - scroll_x
        if _MARGEN_IZQ < cursor_x < self.width():
            bottom = _MARGEN_TOP + len(self._orden_procesos) * _ALTO_FILA

            pen = QPen(_CL_CURSOR, 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.drawLine(cursor_x, _MARGEN_TOP - 2, cursor_x, bottom)

            from PySide6.QtGui import QPolygonF
            from PySide6.QtCore import QPointF
            tri = QPolygonF([
                QPointF(cursor_x,       _MARGEN_TOP),
                QPointF(cursor_x - 7.0, _MARGEN_TOP - 12),
                QPointF(cursor_x + 7.0, _MARGEN_TOP - 12),
            ])
            painter.setPen(Qt.NoPen)
            painter.setBrush(_CL_CURSOR)
            painter.drawPolygon(tri)

            badge = QRectF(cursor_x - 30, 2, 60, 16)
            painter.setBrush(_CL_CURSOR)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(badge, 5, 5)
            f_badge = QFont("Consolas", 7)
            f_badge.setBold(True)
            painter.setFont(f_badge)
            painter.setPen(QColor(255, 250, 242))
            painter.drawText(badge.toRect(), Qt.AlignCenter, self._tick_a_hora(self._tiempo_actual))

    def _dibujar_panel_nombres(self, painter: QPainter, panel_h: int) -> None:
        grad = QLinearGradient(_MARGEN_IZQ - 2, 0, _MARGEN_IZQ + 10, 0)
        grad.setColorAt(0.0, QColor(120, 84, 46, 36))
        grad.setColorAt(1.0, QColor(120, 84, 46, 0))
        painter.fillRect(_MARGEN_IZQ - 2, _MARGEN_TOP, 12,
                         len(self._orden_procesos) * _ALTO_FILA, grad)

        pen = QPen(_CL_SEP, 1.2, Qt.DashLine)
        pen.setDashPattern([2.5, 2.5])
        painter.setPen(pen)
        painter.drawLine(_MARGEN_IZQ - 1, 0, _MARGEN_IZQ - 1, panel_h)

    def _dibujar_placeholder(self, painter: QPainter, panel_h: int) -> None:
        cx = self.width() // 2
        cy = panel_h // 2 - 10

        painter.setRenderHint(QPainter.Antialiasing)
        marco = QRectF(cx - 120, cy - 72, 240, 130)
        painter.setBrush(QColor(255, 249, 237))
        painter.setPen(QPen(QColor(220, 196, 155), 1.5, Qt.DashLine))
        painter.drawRoundedRect(marco, 10, 10)

        for i, ancho in enumerate([150, 120, 90]):
            barra = QRectF(cx - 75, cy - 40 + i * 24, ancho, 12)
            path = QPainterPath()
            path.addRoundedRect(barra, 6, 6)
            grad = QLinearGradient(barra.left(), barra.top(), barra.right(), barra.bottom())
            grad.setColorAt(0.0, QColor(224, 186, 132))
            grad.setColorAt(1.0, QColor(196, 145, 82))
            painter.fillPath(path, grad)

        f_tit = QFont("Segoe UI", 11)
        f_tit.setBold(True)
        painter.setFont(f_tit)
        painter.setPen(_CL_PH_TIT)
        fm = QFontMetrics(f_tit)
        txt1 = "Planner de ejecucion"
        painter.drawText((self.width() - fm.horizontalAdvance(txt1)) // 2, cy + 52, txt1)

        f_sub = QFont("Segoe UI", 9)
        painter.setFont(f_sub)
        painter.setPen(_CL_PH_SUB)
        fm2 = QFontMetrics(f_sub)
        txt2 = "Presione Ejecutar para iniciar la linea de tiempo"
        painter.drawText((self.width() - fm2.horizontalAdvance(txt2)) // 2, cy + 76, txt2)
