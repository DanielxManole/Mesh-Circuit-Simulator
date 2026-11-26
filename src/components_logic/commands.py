"""
Comenzi QUndoCommand pentru add/move/delete componenta si fir.
"""

from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QPointF


class AddComponentCommand(QUndoCommand):
    def __init__(self, scene, component, pos):
        super().__init__(f"Adauga {component.uid}")
        self.scene = scene
        self.component = component
        self.pos = QPointF(pos)
        self._added = False

    def redo(self):
        self.component.setPos(self.pos)
        if not self._added:
            self.scene.addItem(self.component)
            self._added = True
        else:
            self.scene.addItem(self.component)

    def undo(self):
        # sterge si firele atasate
        from src.components.wire import Wire
        wires = [w for w in list(self.scene.items())
                 if isinstance(w, Wire) and
                 (w.pin1.parentItem() is self.component or
                  w.pin2.parentItem() is self.component)]
        for w in wires:
            self.scene.remove_wire(w)
        self.scene.removeItem(self.component)


class DeleteComponentCommand(QUndoCommand):
    def __init__(self, scene, component):
        super().__init__(f"Sterge {component.uid}")
        self.scene = scene
        self.component = component
        self.pos = component.pos()
        self._wire_specs = []   # liste (uid_a, pin_a, uid_b, pin_b)

    def redo(self):
        from src.components.wire import Wire
        self._wire_specs = []
        wires = [w for w in list(self.scene.items())
                 if isinstance(w, Wire) and
                 (w.pin1.parentItem() is self.component or
                  w.pin2.parentItem() is self.component)]
        for w in wires:
            p1c = w.pin1.parentItem()
            p2c = w.pin2.parentItem()
            self._wire_specs.append((p1c.uid, w.pin1.node_name,
                                     p2c.uid, w.pin2.node_name))
            self.scene.remove_wire(w)
        self.scene.removeItem(self.component)

    def undo(self):
        from src.components.wire import Wire
        from src.components.component_item import ComponentItem
        self.component.setPos(self.pos)
        self.scene.addItem(self.component)
        for uid_a, pa, uid_b, pb in self._wire_specs:
            pin_a = self._find_pin(uid_a, pa)
            pin_b = self._find_pin(uid_b, pb)
            if pin_a and pin_b:
                w = Wire(pin_a, pin_b)
                self.scene.addItem(w)
                self.scene.wires.append(w)

    def _find_pin(self, uid, pin_name):
        from src.components.component_item import ComponentItem
        for it in self.scene.items():
            if isinstance(it, ComponentItem) and it.uid == uid:
                for p in it.pins:
                    if p.node_name == pin_name:
                        return p
        return None


class AddWireCommand(QUndoCommand):
    def __init__(self, scene, wire):
        super().__init__("Adauga fir")
        self.scene = scene
        self.wire = wire
        self._added = False

    def redo(self):
        self.scene.addItem(self.wire)
        if self.wire not in self.scene.wires:
            self.scene.wires.append(self.wire)

    def undo(self):
        self.scene.remove_wire(self.wire)


class DeleteWireCommand(QUndoCommand):
    def __init__(self, scene, wire):
        super().__init__("Sterge fir")
        self.scene = scene
        self.wire = wire

    def redo(self):
        self.scene.remove_wire(self.wire)

    def undo(self):
        self.scene.addItem(self.wire)
        if self.wire not in self.scene.wires:
            self.scene.wires.append(self.wire)


class MoveComponentCommand(QUndoCommand):
    def __init__(self, component, old_pos, new_pos):
        super().__init__(f"Muta {component.uid}")
        self.component = component
        self.old_pos = QPointF(old_pos)
        self.new_pos = QPointF(new_pos)

    def redo(self):
        self.component.setPos(self.new_pos)

    def undo(self):
        self.component.setPos(self.old_pos)
