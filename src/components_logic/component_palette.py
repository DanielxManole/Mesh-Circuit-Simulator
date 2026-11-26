"""
Paleta de componente — arbore cu categorii. Drag-and-drop catre canvas.
Iconitele sunt mici (32x32) si redesenate vectorial folosind aceleasi rutine
ca pentru componenta din canvas, ca paleta sa nu depinda de PNG-uri.
"""

from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QLineEdit, QWidget,
    QVBoxLayout, QLabel,
)
from PyQt6.QtCore import Qt, QMimeData, QSize, QRectF
from PyQt6.QtGui import QDrag, QIcon, QPixmap, QPainter, QColor, QPen, QFont

from src.components.components_catalog import COMPONENTS, list_categories
from src.components.component_item import _SYMBOLS


def _icon_for(symbol_key) -> QIcon:
    # alegem o dimensiune mai mare ca sa surprindem componentele mari (Arduino)
    sizes = {
        "arduino_uno": (180, 200),
        "potentiometer": (80, 60),
        "servo": (80, 60),
        "lm35": (80, 60),
        "relay": (100, 80),
    }
    w, h = sizes.get(symbol_key, (60, 60))
    pix = QPixmap(int(w), int(h))
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor("#212121"), 2))
    draw = _SYMBOLS.get(symbol_key)
    if draw:
        class _Dummy:
            width = float(w)
            height = float(h)
            properties = {
                "color": "rosu", "closed": False, "pressed": False,
                "distance_cm": 100, "angle": 90, "temperature": 25,
            }
            kind = symbol_key
        draw(p, _Dummy())
    p.end()
    return QIcon(pix.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation))


class ComponentPalette(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(230)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        title = QLabel("Componente")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Cauta componenta...")
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(12)
        self.tree.setIconSize(QSize(28, 28))
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.tree.startDrag = self._start_drag
        layout.addWidget(self.tree, 1)

        hint = QLabel(
            "Trage o componenta in canvas.\n"
            "Apoi click pe pini ca sa tragi un fir.\n"
            "Dublu-click pentru a edita parametrii."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#757575; font-size: 11px;")
        layout.addWidget(hint)

        self._load()

    # ---------------------------------------------------------------- load
    def _load(self):
        for category, keys in list_categories().items():
            cat_item = QTreeWidgetItem([category])
            f = cat_item.font(0)
            f.setBold(True)
            cat_item.setFont(0, f)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            for key in keys:
                if key not in COMPONENTS:
                    continue
                data = COMPONENTS[key]
                child = QTreeWidgetItem([data["name"]])
                child.setData(0, Qt.ItemDataRole.UserRole, key)
                child.setIcon(0, _icon_for(data.get("symbol", "generic")))
                child.setToolTip(0, (data.get("manual") or "")[:160])
                cat_item.addChild(child)
            self.tree.addTopLevelItem(cat_item)
            cat_item.setExpanded(True)

    # ----------------------------------------------------------------- drag
    def _start_drag(self, _supported):
        item = self.tree.currentItem()
        if not item:
            return
        key = item.data(0, Qt.ItemDataRole.UserRole)
        if not key:
            return
        drag = QDrag(self.tree)
        mime = QMimeData()
        mime.setText(key)
        drag.setMimeData(mime)
        drag.setPixmap(item.icon(0).pixmap(32, 32))
        drag.exec(Qt.DropAction.CopyAction)

    # --------------------------------------------------------------- filter
    def _filter(self, text):
        text = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            cat = self.tree.topLevelItem(i)
            cat_visible = False
            for j in range(cat.childCount()):
                child = cat.child(j)
                match = (not text) or (text in child.text(0).lower())
                child.setHidden(not match)
                cat_visible = cat_visible or match
            cat.setHidden(not cat_visible)
            if text and cat_visible:
                cat.setExpanded(True)
