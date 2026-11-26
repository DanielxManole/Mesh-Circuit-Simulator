"""
CircuitScene — scena drag-and-drop a circuitului.

Responsabilitati:
  - desenarea firelor temporare in timpul tragerii;
  - validarea conexiunilor (un fir nu se conecteaza la acelasi pin etc.);
  - stergerea componentelor/firelor cu BACKSPACE/DELETE;
  - drag-and-drop dintr-o paleta de componente;
  - snap pe grila;
  - animatie curent (timer la 60 FPS daca activata);
  - integrare QUndoStack (add/move/delete).

Nu contine logica de calcul — folositi `calculation.calculate_sys` pentru asta.
"""

from PyQt6.QtWidgets import QGraphicsScene
from PyQt6.QtCore import Qt, QLineF, QPointF, QTimer, pyqtSignal
from PyQt6.QtGui import QPen, QUndoStack

from src.components.pin import Pin
from src.components.wire import Wire
from src.components.component_factory import create_component
from src.components.component_item import ComponentItem

from .commands import (
    AddComponentCommand,
    AddWireCommand,
    DeleteComponentCommand,
    DeleteWireCommand,
    MoveComponentCommand,
)


GRID_SIZE = 20


class CircuitScene(QGraphicsScene):
    selectionMaybeChanged = pyqtSignal(object)   # ComponentItem | None
    componentDoubleClicked = pyqtSignal(object)  # ComponentItem
    statusMessage = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setSceneRect(0, 0, 2400, 1600)
        self.temp_line = None
        self.start_pin = None
        self.wires = []
        self.snap_enabled = True
        self.undo_stack = QUndoStack()

        # animatie
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_last = 0.0

        # urmarirea pozitiei initiale pentru undo move
        self._move_initial = {}   # uid -> QPointF

        self.selectionChanged.connect(self._on_selection_changed)

    # ---------------------------------------------------------------- wire
    def start_wire(self, pin):
        self.cancel_wire()
        self.start_pin = pin
        pin.mark_active()
        self.temp_line = self.addLine(
            QLineF(pin.scenePos(), pin.scenePos()),
            QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.DashLine),
        )
        self.temp_line.setZValue(10)

    def cancel_wire(self):
        if self.temp_line:
            self.removeItem(self.temp_line)
        self.temp_line = None
        if self.start_pin:
            self.start_pin.reset_color()
        self.start_pin = None

    def finish_wire(self, end_pin):
        wire = Wire(self.start_pin, end_pin)
        cmd = AddWireCommand(self, wire)
        self.undo_stack.push(cmd)
        self.removeItem(self.temp_line)
        self.temp_line = None
        self.start_pin.reset_color()
        self.start_pin = None
        self.statusMessage.emit("Fir adaugat.")

    def can_connect(self, pin1, pin2):
        if pin1 is pin2:
            return False
        if pin1.parentItem() is pin2.parentItem():
            return False
        for w in self.wires:
            if (w.pin1 is pin1 and w.pin2 is pin2) or \
               (w.pin1 is pin2 and w.pin2 is pin1):
                return False
        return True

    def remove_wire(self, wire):
        if wire in self.wires:
            self.wires.remove(wire)
        if wire.scene() is self:
            self.removeItem(wire)

    # ----------------------------------------------------------------- mouse
    def mousePressEvent(self, event):
        items = self.items(event.scenePos())

        pin_under = next((it for it in items if isinstance(it, Pin)), None)

        # daca suntem in modul "tragem fir"
        if self.start_pin:
            if pin_under and self.can_connect(self.start_pin, pin_under):
                self.finish_wire(pin_under)
                event.accept()
                return
            elif pin_under is self.start_pin:
                self.cancel_wire()
                self.statusMessage.emit("Tragere de fir anulata.")
                event.accept()
                return
            else:
                # click in alta parte = anulare
                self.cancel_wire()
                self.statusMessage.emit("Tragere de fir anulata.")
                # nu propaga ca sa nu deselecteze nimic
                return

        # daca am dat click pe un pin, incepe un nou fir
        if pin_under is not None and event.button() == Qt.MouseButton.LeftButton:
            self.start_wire(pin_under)
            event.accept()
            return

        # altfel selectie / mutare componenta
        self._move_initial.clear()
        comp_under = next((it for it in items if isinstance(it, ComponentItem)), None)
        if comp_under is not None and event.button() == Qt.MouseButton.LeftButton:
            self._move_initial[id(comp_under)] = (comp_under, QPointF(comp_under.pos()))

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.temp_line and self.start_pin:
            line = QLineF(self.start_pin.scenePos(), event.scenePos())
            self.temp_line.setLine(line)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.snap_enabled:
            for comp, _ in self._move_initial.values():
                p = comp.pos()
                snapped = QPointF(round(p.x() / GRID_SIZE) * GRID_SIZE,
                                  round(p.y() / GRID_SIZE) * GRID_SIZE)
                comp.setPos(snapped)
        # undo: daca pozitia s-a schimbat, inregistreaza
        for comp, old_pos in self._move_initial.values():
            new_pos = comp.pos()
            if (new_pos - old_pos).manhattanLength() > 0.5:
                self.undo_stack.push(MoveComponentCommand(comp, old_pos, new_pos))
        self._move_initial.clear()

    def mouseDoubleClickEvent(self, event):
        items = self.items(event.scenePos())
        comp = next((it for it in items if isinstance(it, ComponentItem)), None)
        if comp:
            self.componentDoubleClicked.emit(comp)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    # ------------------------------------------------------------- keyboard
    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            for item in list(self.selectedItems()):
                if isinstance(item, Wire):
                    self.undo_stack.push(DeleteWireCommand(self, item))
                elif isinstance(item, ComponentItem):
                    self.undo_stack.push(DeleteComponentCommand(self, item))
            return
        if key == Qt.Key.Key_Escape:
            self.cancel_wire()
            return
        super().keyPressEvent(event)

    # -------------------------------------------------------------- drag/drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        ctype = event.mimeData().text()
        try:
            comp = create_component(ctype)
        except ValueError:
            event.ignore()
            return
        pos = event.scenePos()
        if self.snap_enabled:
            pos = QPointF(round(pos.x() / GRID_SIZE) * GRID_SIZE,
                          round(pos.y() / GRID_SIZE) * GRID_SIZE)
        cmd = AddComponentCommand(self, comp, pos)
        self.undo_stack.push(cmd)
        comp.update_label()
        event.acceptProposedAction()
        self.statusMessage.emit(f"Adaugat {comp.uid}.")

    # ------------------------------------------------------------ selection
    def _on_selection_changed(self):
        sel = [it for it in self.selectedItems() if isinstance(it, ComponentItem)]
        self.selectionMaybeChanged.emit(sel[0] if sel else None)

    # ------------------------------------------------------- highlights/anim
    def clear_highlights(self):
        for it in self.items():
            if isinstance(it, ComponentItem):
                it.set_highlight(None)
            elif isinstance(it, Wire):
                it.set_current(0.0)
                it.enable_animation(False)

    def apply_result(self, result):
        """Aplica vizual rezultatele simularii (highlight + curenti pe fire).

        Componentele multi-element (ex: Arduino, potentiometer) au sub-uid-uri
        de forma 'UNO1.5V'; aici mapam prefixul inainte de punct la componenta
        din UI ca evidentierile sa apara pe componenta-parinte.
        """
        def parent_uid(uid):
            return uid.split(".", 1)[0]

        offenders = {}
        for e in result.errors:
            uid = parent_uid(e.where)
            if e.level == "error":
                offenders[uid] = "error"
            elif e.level == "warning" and offenders.get(uid) != "error":
                offenders[uid] = "warning"
        for it in self.items():
            if isinstance(it, ComponentItem):
                it.set_highlight(offenders.get(it.uid))

        # curentul pe fire (estimat din componenta adiacenta cu I cunoscut)
        i_by_uid = {uid: data.get("I", 0.0)
                    for uid, data in result.components.items()}
        for it in self.items():
            if isinstance(it, Wire):
                c1 = it.pin1.parentItem()
                c2 = it.pin2.parentItem()
                cur = 0.0
                for c, pin in ((c1, it.pin1), (c2, it.pin2)):
                    if c is None:
                        continue
                    uid = getattr(c, "uid", None)
                    if uid in i_by_uid:
                        cur = i_by_uid[uid]
                        break
                    # incearca sub-uid pe pin (ex: UNO1.D13)
                    sub = f"{uid}.{pin.node_name}"
                    if sub in i_by_uid:
                        cur = i_by_uid[sub]
                        break
                it.set_current(cur)

    def start_animation(self):
        for it in self.items():
            if isinstance(it, Wire):
                it.enable_animation(True)
        if not self._anim_timer.isActive():
            self._anim_timer.start(33)   # ~30 FPS — suficient si economic

    def stop_animation(self):
        if self._anim_timer.isActive():
            self._anim_timer.stop()
        for it in self.items():
            if isinstance(it, Wire):
                it.enable_animation(False)

    def _tick(self):
        for it in self.items():
            if isinstance(it, Wire):
                it.step_animation(0.033)

    # ------------------------------------------------------ clear scena
    def clear_circuit(self):
        self.clear()
        self.wires = []
        self.undo_stack.clear()
        ComponentItem.reset_id_counters()
