"""
View pentru canvas-ul de circuit. Adauga zoom (rotita), pan (Space + drag sau
butonul mijlociu), grila vizibila pe fundal si paint inteligent al fundalului.
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPointF


GRID_SIZE = 20
GRID_COLOR_MINOR = QColor("#e8eef5")
GRID_COLOR_MAJOR = QColor("#cdd9e5")
BACKGROUND = QColor("#fbfcfe")


class CircuitView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setBackgroundBrush(BACKGROUND)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setMouseTracking(True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self._panning = False
        self._pan_start = QPointF()
        self.show_grid = True
        self._zoom = 1.0

    # --------------------------------------------------------- background
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if not self.show_grid:
            return
        left  = int(rect.left())  - (int(rect.left())  % GRID_SIZE)
        top   = int(rect.top())   - (int(rect.top())   % GRID_SIZE)
        right = int(rect.right()) + GRID_SIZE
        bot   = int(rect.bottom())+ GRID_SIZE

        pen_minor = QPen(GRID_COLOR_MINOR, 0)
        pen_major = QPen(GRID_COLOR_MAJOR, 0)
        painter.setPen(pen_minor)
        for x in range(left, right, GRID_SIZE):
            painter.setPen(pen_major if x % (GRID_SIZE * 5) == 0 else pen_minor)
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, bot, GRID_SIZE):
            painter.setPen(pen_major if y % (GRID_SIZE * 5) == 0 else pen_minor)
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    # ----------------------------------------------------------------- zoom
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier or True:
            factor = 1.15 if event.angleDelta().y() > 0 else (1 / 1.15)
            new_zoom = self._zoom * factor
            if 0.2 <= new_zoom <= 5.0:
                self._zoom = new_zoom
                self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def reset_zoom(self):
        self.resetTransform()
        self._zoom = 1.0

    def fit_circuit(self):
        rect = self.scene().itemsBoundingRect()
        if rect.isEmpty():
            return
        self.fitInView(rect.adjusted(-40, -40, 40, 40),
                       Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = self.transform().m11()

    # ----------------------------------------------------------------- pan
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def toggle_grid(self, on):
        self.show_grid = on
        self.viewport().update()
