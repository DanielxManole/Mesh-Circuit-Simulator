"""
Fir intre doi pini. Foloseste un QGraphicsPathItem orto (manhattan) pentru un
aspect schematic curat. Animatia curentului se face deplasand un offset al
liniei punctate (vezi `set_current` + `step_animation`).
"""

from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PyQt6.QtGui import QPen, QColor, QPainterPath, QBrush
from PyQt6.QtCore import Qt, QPointF


WIRE_COLOR = QColor("#212121")
WIRE_SELECTED = QColor("#1976d2")


class Wire(QGraphicsPathItem):
    def __init__(self, pin1, pin2):
        super().__init__()
        self.pin1 = pin1
        self.pin2 = pin2
        self.current = 0.0           # curent calculat (A) — informativ
        self._anim_offset = 0.0      # offset pentru animatia "dash"
        self._animated = False

        pen = QPen(WIRE_COLOR, 2.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(0)

        self.update_position()

    # ------------------------------------------------------------ routing
    def update_position(self):
        p1 = self.pin1.scenePos()
        p2 = self.pin2.scenePos()
        path = QPainterPath(p1)
        # routing manhattan simplu — un singur cot la mijloc
        mid_x = (p1.x() + p2.x()) / 2
        path.lineTo(QPointF(mid_x, p1.y()))
        path.lineTo(QPointF(mid_x, p2.y()))
        path.lineTo(p2)
        self.setPath(path)

    # ------------------------------------------------------------ paint
    def paint(self, painter, option, widget=None):
        pen = QPen(self.pen())
        if self.isSelected():
            pen.setColor(WIRE_SELECTED)
            pen.setWidthF(2.8)
        if self._animated and abs(self.current) > 1e-12:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern([6, 4])
            pen.setDashOffset(self._anim_offset)
            pen.setColor(QColor("#1e88e5"))
        painter.setPen(pen)
        painter.drawPath(self.path())

    # ------------------------------------------------------------ animation
    def set_current(self, value):
        self.current = value
        self.update()

    def enable_animation(self, on):
        self._animated = on
        self.update()

    def step_animation(self, dt):
        """Avanseaza offset-ul de dash proportional cu curentul (sens semn)."""
        if not self._animated:
            return
        sign = 1 if self.current >= 0 else -1
        speed = min(60.0, 6.0 + abs(self.current) * 50.0)
        self._anim_offset -= sign * speed * dt
        self.update()
