"""
Pin (terminal) de componenta. Inceperea/finalizarea unui fir e gestionata de
CircuitScene (in `mousePressEvent`) — pinul doar semnaleaza hover + isi
actualizeaza firele cand componenta-parinte e mutata.
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtCore import Qt

from .wire import Wire


PIN_RADIUS = 5

PIN_DEFAULT_COLOR = QColor("#fbc02d")   # galben
PIN_HOVER_COLOR   = QColor("#43a047")   # verde
PIN_ACTIVE_COLOR  = QColor("#1e88e5")   # albastru: pin curent in cursul tragerii
PIN_ERROR_COLOR   = QColor("#c62828")   # rosu: pin neconectat / eroare


class Pin(QGraphicsEllipseItem):
    def __init__(self, parent, x, y, node_name):
        super().__init__(-PIN_RADIUS, -PIN_RADIUS,
                         2 * PIN_RADIUS, 2 * PIN_RADIUS, parent)
        self.setPos(x, y)
        self.node_name = node_name
        self._default_color = PIN_DEFAULT_COLOR
        self.setBrush(QBrush(self._default_color))
        self.setPen(QPen(QColor("#212121"), 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)

    # ------------------------------------------------------------- hover
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(PIN_HOVER_COLOR))

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(self._default_color))

    # ------------------------------------------------------------- move
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            scene = self.scene()
            if scene is not None:
                for item in scene.items():
                    if isinstance(item, Wire) and (item.pin1 is self or item.pin2 is self):
                        item.update_position()
        return super().itemChange(change, value)

    # ----------------------------------------------------------- coloring
    def set_default_color(self, color):
        self._default_color = color
        self.setBrush(QBrush(color))

    def reset_color(self):
        self._default_color = PIN_DEFAULT_COLOR
        self.setBrush(QBrush(PIN_DEFAULT_COLOR))

    def mark_active(self):
        self.setBrush(QBrush(PIN_ACTIVE_COLOR))

    def mark_error(self):
        self._default_color = PIN_ERROR_COLOR
        self.setBrush(QBrush(PIN_ERROR_COLOR))
