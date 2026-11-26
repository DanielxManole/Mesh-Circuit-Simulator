"""
Properties Panel — afisat in dreapta. Editeaza parametrii componentei selectate
si arata manualul (cerinta SRS).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QGroupBox, QTextEdit, QFrame,
    QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class PropertiesPanel(QWidget):
    """Panou de proprietati pentru componenta selectata."""

    propertyChanged = pyqtSignal(object, str, object)   # comp, key, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(360)
        self.current_component = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("Proprietati")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        self.empty_label = QLabel("Selecteaza o componenta din canvas\n(click sau dublu-click) "
                                  "ca sa-i editezi parametrii.")
        self.empty_label.setWordWrap(True)
        self.empty_label.setStyleSheet("color: #757575;")
        layout.addWidget(self.empty_label)

        # Header info
        self.header = QGroupBox()
        header_layout = QFormLayout(self.header)
        self.id_label = QLabel()
        self.kind_label = QLabel()
        header_layout.addRow("ID:", self.id_label)
        header_layout.addRow("Tip:", self.kind_label)
        self.header.setVisible(False)
        layout.addWidget(self.header)

        # Parameter editors
        self.params_group = QGroupBox("Parametri")
        self.params_layout = QFormLayout(self.params_group)
        self.params_group.setVisible(False)
        layout.addWidget(self.params_group)

        # Manual
        self.manual_group = QGroupBox("Manual de utilizare")
        manual_layout = QVBoxLayout(self.manual_group)
        self.manual_text = QTextEdit()
        self.manual_text.setReadOnly(True)
        self.manual_text.setMaximumHeight(160)
        self.manual_text.setStyleSheet("background:#f5f5f5; border:0;")
        manual_layout.addWidget(self.manual_text)
        self.manual_group.setVisible(False)
        layout.addWidget(self.manual_group)

        layout.addStretch(1)

        self._editors = {}   # key -> QWidget

    # ----------------------------------------------------------------- API
    def show_component(self, comp):
        self.current_component = comp
        self._editors.clear()
        # cleanup
        while self.params_layout.rowCount():
            self.params_layout.removeRow(0)

        if comp is None:
            self.empty_label.setVisible(True)
            self.header.setVisible(False)
            self.params_group.setVisible(False)
            self.manual_group.setVisible(False)
            return

        self.empty_label.setVisible(False)
        self.header.setVisible(True)
        self.params_group.setVisible(True)
        self.manual_group.setVisible(True)

        self.id_label.setText(comp.uid)
        self.kind_label.setText(comp.data.get("name", comp.kind))

        for key, meta in comp.meta.items():
            label = meta.get("label", key)
            unit = meta.get("unit", "")
            value = comp.properties.get(key, meta.get("value"))
            editor = self._make_editor(key, meta, value)
            text = f"{label}" + (f" [{unit}]" if unit else "")
            self.params_layout.addRow(text + ":", editor)
            self._editors[key] = editor

        if not comp.meta:
            self.params_layout.addRow(QLabel("(fara parametri editabili)"))

        manual = comp.data.get("manual", "")
        self.manual_text.setPlainText(manual or "(fara manual)")

    def refresh(self):
        if self.current_component is not None:
            self.show_component(self.current_component)

    # -------------------------------------------------------------- editori
    def _make_editor(self, key, meta, value):
        if "options" in meta:
            box = QComboBox()
            for opt in meta["options"]:
                box.addItem(str(opt), opt)
            try:
                box.setCurrentIndex(meta["options"].index(value))
            except ValueError:
                pass
            box.currentIndexChanged.connect(
                lambda _i, k=key, b=box: self._emit_change(k, b.currentData())
            )
            return box

        if isinstance(value, bool):
            chk = QCheckBox()
            chk.setChecked(bool(value))
            chk.toggled.connect(lambda v, k=key: self._emit_change(k, v))
            return chk

        if isinstance(value, (int, float)):
            spin = QDoubleSpinBox()
            spin.setDecimals(6)
            spin.setRange(float(meta.get("min", -1e12)), float(meta.get("max", 1e12)))
            # pas adaptiv simpla
            step = 1.0 if abs(value) >= 10 else 0.1 if abs(value) >= 1 else 0.01
            spin.setSingleStep(step)
            spin.setValue(float(value))
            spin.setKeyboardTracking(False)
            spin.valueChanged.connect(lambda v, k=key: self._emit_change(k, float(v)))
            return spin

        # text generic
        edit = QLineEdit(str(value))
        edit.editingFinished.connect(
            lambda k=key, e=edit: self._emit_change(k, e.text())
        )
        return edit

    def _emit_change(self, key, value):
        if self.current_component is None:
            return
        self.current_component.set_property(key, value)
        self.propertyChanged.emit(self.current_component, key, value)
