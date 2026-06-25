from dataclasses import dataclass, field
from typing import Dict, List, Optional

from PySide6.QtWidgets import QWidget, QScrollBar
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QLinearGradient,
    QPainterPath, QFontMetrics,
)

from interfaz.tema import (
    COLOR_FONDO_PRIMARIO, COLOR_FONDO_SECUNDARIO, COLOR_SUPERFICIE,
    COLOR_SUPERFICIE_ELEV, COLOR_BORDE, COLOR_BORDE_FUERTE,
    COLOR_TEXTO_MUTED, COLOR_ACENTO_CYAN,
    fuente_seccion, fuente_mono, aclarar, oscurecer,
)
from modelos.segmento_ejecucion import SegmentoEjecucion


# ── Constantes de diseño del diagrama (equivalentes a GanttPanel de WinForms) ─
_MARGEN_IZQ    = 110
_ALTO_FILA     = 42
_MARGEN_TOP    = 34
_PX_POR_UNIDAD = 30


# Almacena el estado de un bloque dibujado en el Gantt.
@dataclass
class _BloqueDibujado:
    proceso: str
    inicio: int
    fin_actual: int
    fin_real: int
    color: QColor
    es_idle: bool = False


# Widget personalizado que dibuja el diagrama de Gantt en tiempo real.
# Cada fila representa un proceso; los bloques se rellenan tick a tick.
# Soporta scroll horizontal cuando el tiempo total supera el ancho visible.
class VistaGantt(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)

        self._segmentos: List[SegmentoEjecucion] = []
        self._mapa_colores: Dict[str, QColor] = {}
        self._orden_procesos: List[str] = []
        self._tiempo_actual = 0
        self._tiempo_max = 0
        self._bloques: List[_BloqueDibujado] = []
        self._bloque_actual: Optional[_BloqueDibujado] = None

        # Scrollbar horizontal
        self._scroll = QScrollBar(Qt.Horizontal, self)
        self._scroll.setFixedHeight(14)
        self._scroll.valueChanged.connect(self.update)
        self._actualizar_scroll()

    # ─────────────────────────────────────────────────────────────────────
    # API PÚBLICA
    # ─────────────────────────────────────────────────────────────────────

    # Inicializa el Gantt con los segmentos y el mapa de colores.
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

    # Avanza el Gantt al tick indicado mostrando el proceso en ejecución.
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

        # Auto-scroll cuando el cursor sale del área visible
        cursor_x = _MARGEN_IZQ + self._tiempo_actual * _PX_POR_UNIDAD - self._scroll.value()
        if cursor_x > self.width() - 80:
            nuevo_valor = min(
                self._scroll.maximum(),
                self._scroll.value() + _PX_POR_UNIDAD * 3,
            )
            self._scroll.setValue(nuevo_valor)

        self.update()

    # Limpia el Gantt y vuelve al estado inicial.
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

    # ─────────────────────────────────────────────────────────────────────
    # REDIMENSIONAMIENTO
    # ─────────────────────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scroll.setGeometry(0, self.height() - 14, self.width(), 14)
        self._actualizar_scroll()

    # Actualiza el rango del scrollbar según el tiempo máximo y el ancho del widget.
    def _actualizar_scroll(self) -> None:
        total_ancho = _MARGEN_IZQ + self._tiempo_max * _PX_POR_UNIDAD + 60
        maximo = max(0, total_ancho - self.width() + 20)
        self._scroll.setMaximum(maximo)

    # ─────────────────────────────────────────────────────────────────────
    # PINTADO PRINCIPAL
    # ─────────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        scroll_x = self._scroll.value()
        panel_h = self.height() - 14  # descontar scrollbar

        painter.fillRect(0, 0, self.width(), panel_h, COLOR_FONDO_PRIMARIO)

        if not self._orden_procesos:
            self._dibujar_placeholder(painter, panel_h)
            return

        self._dibujar_regla(painter, scroll_x)
        self._dibujar_filas(painter, scroll_x)
        self._dibujar_bloques(painter, scroll_x)
        self._dibujar_cursor(painter, scroll_x)
        self._dibujar_separador_nombres(painter, panel_h)

    # ─────────────────────────────────────────────────────────────────────
    # SECCIONES DE DIBUJO
    # ─────────────────────────────────────────────────────────────────────

    # Dibuja la regla de tiempo en la parte superior.
    def _dibujar_regla(self, painter: QPainter, scroll_x: int) -> None:
        alto_total = _MARGEN_TOP + len(self._orden_procesos) * _ALTO_FILA

        painter.fillRect(0, 0, self.width(), _MARGEN_TOP, QColor(12, 14, 23))
        painter.fillRect(0, 0, _MARGEN_IZQ - 1, _MARGEN_TOP, QColor(16, 18, 28))

        font_num = QFont("Consolas", 7)
        brush_minor = QColor(90, 118, 185)
        brush_major = QColor(140, 168, 228)
        pen_grid_minor = QPen(QColor(26, 30, 50), 1)
        pen_grid_major = QPen(QColor(42, 48, 76), 1)
        pen_tick_minor = QPen(QColor(55, 65, 100), 1)
        pen_tick_major = QPen(QColor(88, 105, 155), 1)

        painter.setFont(fuente_mono())
        painter.setPen(COLOR_TEXTO_MUTED)
        painter.drawText(
            QRect(0, 0, _MARGEN_IZQ - 1, _MARGEN_TOP),
            Qt.AlignCenter, "PROCESO"
        )

        painter.setFont(font_num)
        for t in range(self._tiempo_max + 2):
            x = _MARGEN_IZQ + t * _PX_POR_UNIDAD - scroll_x
            if x < _MARGEN_IZQ - 5 or x > self.width() + 5:
                continue

            major = (t % 5 == 0)

            # Línea de grid sobre filas
            painter.setPen(pen_grid_major if major else pen_grid_minor)
            painter.drawLine(x, _MARGEN_TOP, x, alto_total)

            # Marca en la regla
            tick_h = 11 if major else 6
            painter.setPen(pen_tick_major if major else pen_tick_minor)
            painter.drawLine(x, _MARGEN_TOP - tick_h, x, _MARGEN_TOP)

            # Número de tiempo
            painter.setPen(brush_major if major else brush_minor)
            y_num = 2 if major else 5
            offset_x = -6 if t >= 10 else -3
            painter.drawText(x + offset_x, y_num, 20, 16, Qt.AlignLeft, str(t))

    # Dibuja el fondo de cada fila con el nombre del proceso.
    def _dibujar_filas(self, painter: QPainter, scroll_x: int) -> None:
        for i, nombre in enumerate(self._orden_procesos):
            y = _MARGEN_TOP + i * _ALTO_FILA

            # Fondo alternado
            color_bg = QColor(17, 19, 30) if i % 2 == 0 else QColor(21, 24, 37)
            painter.fillRect(_MARGEN_IZQ, y, self.width() - _MARGEN_IZQ, _ALTO_FILA, color_bg)

            # Línea divisora inferior de fila
            painter.setPen(QPen(QColor(24, 27, 44), 1))
            painter.drawLine(_MARGEN_IZQ, y + _ALTO_FILA - 1, self.width(), y + _ALTO_FILA - 1)

            # Columna de nombre
            painter.fillRect(0, y, _MARGEN_IZQ - 1, _ALTO_FILA, COLOR_FONDO_SECUNDARIO)

            # Barra de acento lateral izquierda
            color_proc = self._mapa_colores.get(nombre, QColor(128, 128, 128))
            painter.fillRect(0, y + 6, 3, _ALTO_FILA - 12, color_proc)

            # Nombre del proceso centrado
            painter.setFont(fuente_seccion())
            painter.setPen(color_proc)
            painter.drawText(
                QRect(5, y, _MARGEN_IZQ - 7, _ALTO_FILA),
                Qt.AlignCenter, nombre
            )

            # Líneas de grid vertical en área de Gantt
            self._dibujar_grid_fila(painter, scroll_x, y, _ALTO_FILA)

    # Dibuja las líneas de grid vertical dentro de una fila.
    def _dibujar_grid_fila(self, painter: QPainter, scroll_x: int, y: int, h: int) -> None:
        for t in range(self._tiempo_max + 1):
            x = _MARGEN_IZQ + t * _PX_POR_UNIDAD - scroll_x
            if x < _MARGEN_IZQ or x >= self.width():
                continue
            major = (t % 5 == 0)
            pen = QPen(QColor(38, 44, 70) if major else QColor(24, 28, 48), 1)
            painter.setPen(pen)
            painter.drawLine(x, y, x, y + h - 1)

    # Dibuja todos los bloques de ejecución completados y el bloque actual.
    def _dibujar_bloques(self, painter: QPainter, scroll_x: int) -> None:
        for bloque in self._bloques:
            self._dibujar_bloque(painter, bloque, bloque.fin_actual, scroll_x)
        if self._bloque_actual is not None:
            self._dibujar_bloque(painter, self._bloque_actual,
                                 self._bloque_actual.fin_actual, scroll_x)

    # Dibuja un bloque individual con gradiente y etiqueta centrada.
    def _dibujar_bloque(self, painter: QPainter, bloque: _BloqueDibujado,
                        fin_dibujado: int, scroll_x: int) -> None:
        fila_idx = self._orden_procesos.index(bloque.proceso) if bloque.proceso in self._orden_procesos else -1
        if fila_idx < 0:
            return

        PAD = 4
        y = _MARGEN_TOP + fila_idx * _ALTO_FILA + PAD
        h = _ALTO_FILA - PAD * 2
        x = _MARGEN_IZQ + bloque.inicio * _PX_POR_UNIDAD - scroll_x
        w = (fin_dibujado - bloque.inicio) * _PX_POR_UNIDAD

        if w <= 0 or x + w < _MARGEN_IZQ or x > self.width():
            return

        x = max(x, _MARGEN_IZQ)
        rect = QRect(x, y, max(w, 2), h)

        radio = min(5, h // 3)
        color_top = aclarar(bloque.color, 40)
        color_bot = oscurecer(bloque.color, 18)

        # Gradiente vertical
        gradiente = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradiente.setColorAt(0.0, color_top)
        gradiente.setColorAt(1.0, color_bot)

        path = self._rect_redondeado(rect, radio)
        painter.fillPath(path, gradiente)

        # Borde
        painter.setPen(QPen(aclarar(bloque.color, 60), 1.0))
        painter.drawPath(path)

        # Etiqueta centrada
        if rect.width() > 20:
            fuente_etiqueta = QFont("Segoe UI", 8)
            fuente_etiqueta.setBold(True)
            painter.setFont(fuente_etiqueta)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(rect, Qt.AlignCenter, bloque.proceso)

    # Dibuja la línea de cursor de tiempo actual.
    def _dibujar_cursor(self, painter: QPainter, scroll_x: int) -> None:
        cursor_x = _MARGEN_IZQ + self._tiempo_actual * _PX_POR_UNIDAD - scroll_x
        if cursor_x > _MARGEN_IZQ and cursor_x < self.width():
            cursor_bottom = _MARGEN_TOP + len(self._orden_procesos) * _ALTO_FILA

            pen_cursor = QPen(QColor(240, 65, 85), 1.5, Qt.DashLine)
            painter.setPen(pen_cursor)
            painter.drawLine(cursor_x, _MARGEN_TOP, cursor_x, cursor_bottom)

            # Triángulo en la regla
            from PySide6.QtGui import QPolygonF
            from PySide6.QtCore import QPointF
            triangulo = QPolygonF([
                QPointF(cursor_x,       _MARGEN_TOP),
                QPointF(cursor_x - 5.0, _MARGEN_TOP - 9),
                QPointF(cursor_x + 5.0, _MARGEN_TOP - 9),
            ])
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(240, 65, 85))
            painter.drawPolygon(triangulo)

    # Dibuja la línea vertical separadora entre nombres y área de Gantt.
    def _dibujar_separador_nombres(self, painter: QPainter, panel_h: int) -> None:
        painter.setPen(QPen(COLOR_BORDE_FUERTE, 1))
        painter.drawLine(_MARGEN_IZQ - 1, 0, _MARGEN_IZQ - 1, panel_h)

    # Muestra el mensaje de espera cuando no hay datos.
    def _dibujar_placeholder(self, painter: QPainter, panel_h: int) -> None:
        f_titulo = QFont("Segoe UI", 13)
        f_titulo.setBold(True)
        f_sub = QFont("Segoe UI", 10)

        linea1 = "Diagrama de Gantt"
        linea2 = "Presione  ▶ Ejecutar  para iniciar la simulación"

        cy = panel_h // 2

        painter.setFont(f_titulo)
        painter.setPen(QColor(50, 56, 88))
        fm = QFontMetrics(f_titulo)
        ancho1 = fm.horizontalAdvance(linea1)
        painter.drawText((self.width() - ancho1) // 2, cy - 20, linea1)

        painter.setFont(f_sub)
        painter.setPen(COLOR_TEXTO_MUTED)
        fm2 = QFontMetrics(f_sub)
        ancho2 = fm2.horizontalAdvance(linea2)
        painter.drawText((self.width() - ancho2) // 2, cy + 16, linea2)

    # ─────────────────────────────────────────────────────────────────────
    # UTILIDADES
    # ─────────────────────────────────────────────────────────────────────

    # Construye un QPainterPath de rectángulo con esquinas redondeadas.
    @staticmethod
    def _rect_redondeado(rect: QRect, radio: int) -> QPainterPath:
        path = QPainterPath()
        if radio <= 0:
            path.addRect(rect)
        else:
            path.addRoundedRect(rect, radio, radio)
        return path
