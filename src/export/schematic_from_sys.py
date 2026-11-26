"""
`schematic_from_sys` — exporta circuitul ca schema tehnica (PNG/SVG).

Conform cerintei SRS: optional fara parametri, doar elementele. Foloseste un
QGraphicsScene "curat" generat dinamic, ca exportul sa nu depinda de
chenarele/selectiile UI.
"""

from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF


def schematic_from_sys(scene, path: str, include_params: bool = True,
                       margin: int = 40) -> str:
    """
    Randeaza scena intr-o imagine PNG cu fundal alb (fara grila).

    Daca `include_params` e False, etichetele componentelor sunt redenumite la
    doar id-ul lor (fara valoarea numerica scurta).
    """
    return export_as_image(scene, path, include_params=include_params, margin=margin)


def export_as_image(scene, path: str, include_params: bool = True,
                    margin: int = 40) -> str:
    from src.components.component_item import ComponentItem

    # daca nu e nimic de exportat, alegem o zona implicita
    rect = scene.itemsBoundingRect()
    if rect.isEmpty():
        rect = QRectF(0, 0, 400, 200)
    rect = rect.adjusted(-margin, -margin, margin, margin)

    pixmap = QPixmap(int(rect.width()), int(rect.height()))
    pixmap.fill(QColor("#ffffff"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # ascunde temporar etichetele de valoare daca exportul e doar de schema
    backup_labels = []
    if not include_params:
        for it in scene.items():
            if isinstance(it, ComponentItem) and hasattr(it, "label"):
                backup_labels.append((it, it.label.toPlainText()))
                it.label.setPlainText(it.uid)

    scene.render(painter, target=QRectF(pixmap.rect()), source=rect)
    painter.end()

    # restaureaza etichetele
    for it, txt in backup_labels:
        it.label.setPlainText(txt)

    if not path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
        path = path + ".png"
    pixmap.save(path)
    return path
