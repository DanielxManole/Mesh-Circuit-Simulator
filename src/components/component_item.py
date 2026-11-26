"""
Item grafic pentru o componenta din circuit.

Subsistem: Modelare circuite (UI). Nu contine logica de calcul — doar afiseaza
componenta si pastreaza pini + parametri. Simbolurile sunt desenate vectorial
(QPainter) conform IEC 60617 / ANSI Y32.2 ca aplicatia sa nu depinda de imagini.
"""

from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QGraphicsTextItem,
)
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPolygonF, QPainterPath
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF

from .pin import Pin


COMPONENT_SIZE = 60   # bounding box implicit pentru componentele standard


class ComponentItem(QGraphicsObject):
    """Componenta vizuala. Pastreaza data catalog, parametri si id-ul unic."""

    _id_counters = {}   # contor global pe tip pentru id-uri unice (R1, R2, V1...)

    def __init__(self, data, comp_id=None):
        super().__init__()
        self.data = data
        self.kind = data["kind"]
        self.symbol = data.get("symbol", "generic")

        # dimensiuni (implicit 60x60). Folosite de boundingRect + draw functions.
        sz = data.get("size", (COMPONENT_SIZE, COMPONENT_SIZE))
        self.width  = float(sz[0])
        self.height = float(sz[1])

        # parametri editabili — extragem doar valoarea, dar pastram metadata in self.meta
        self.meta = {k: v for k, v in (data.get("properties") or {}).items()}
        self.properties = {k: v["value"] for k, v in self.meta.items()}

        # id unic in proiect (ex: R1, V2, LED3...)
        self.uid = comp_id or self._next_id(self.kind)

        # stare vizuala (folosita pentru afisarea erorilor)
        self.highlight = None   # None | "error" | "warning" | "ok"

        # flag-uri pentru selectare / mutare
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)

        self._create_pins()
        self._create_label()

    # ------------------------------------------------------------------ id
    @classmethod
    def _next_id(cls, kind):
        cls._id_counters[kind] = cls._id_counters.get(kind, 0) + 1
        prefix = {
            "R": "R", "V": "V", "I": "I", "CAP": "C", "IND": "L",
            "D": "D", "LED": "LED", "SW": "SW", "GND": "GND",
            "METER_V": "VM", "METER_I": "AM",
            "BJT_NPN": "Q", "BJT_PNP": "Q",
            "PHOTORES": "LDR", "ULTRA": "US",
            "ARDUINO": "UNO", "BTN": "BTN", "POT": "POT", "BUZZER": "BZ",
            "SERVO": "SV", "DCMOTOR": "M", "LM35": "TS", "THERM": "TH",
            "RELAY": "RL",
        }.get(kind, kind)
        return f"{prefix}{cls._id_counters[kind]}"

    @classmethod
    def reset_id_counters(cls):
        cls._id_counters.clear()

    @classmethod
    def bump_counter_to(cls, kind, n):
        """Forteaza contorul cel putin la n (folosit la load)."""
        cls._id_counters[kind] = max(cls._id_counters.get(kind, 0), n)

    # ----------------------------------------------------------------- geom
    def boundingRect(self):
        return QRectF(-4, -16, self.width + 8, self.height + 24)

    def _create_pins(self):
        from PyQt6.QtGui import QFont
        self.pins = []
        show_labels = bool(self.data.get("show_pin_labels"))
        for pin_data in self.data["pins"]:
            pin = Pin(self, pin_data["x"], pin_data["y"], pin_data["name"])
            self.pins.append(pin)
            if show_labels:
                label = QGraphicsTextItem(pin_data["name"], self)
                label.setFont(QFont("Segoe UI", 6))
                label.setDefaultTextColor(QColor("#37474f"))
                # plaseaza eticheta langa pin, in interior
                anchor = pin_data.get("label_at", "auto")
                self._place_pin_label(label, pin_data["x"], pin_data["y"], anchor)

    def _place_pin_label(self, label, x, y, anchor):
        rect = label.boundingRect()
        if anchor == "left":
            label.setPos(x - rect.width() - 4, y - rect.height() / 2)
        elif anchor == "right":
            label.setPos(x + 4, y - rect.height() / 2)
        elif anchor == "above":
            label.setPos(x - rect.width() / 2, y - rect.height() - 2)
        elif anchor == "below":
            label.setPos(x - rect.width() / 2, y + 2)
        else:
            # auto: pune eticheta spre interiorul componentei
            cx, cy = self.width / 2, self.height / 2
            if x < 8:
                label.setPos(x + 4, y - rect.height() / 2)
            elif x > self.width - 8:
                label.setPos(x - rect.width() - 4, y - rect.height() / 2)
            elif y < 8:
                label.setPos(x - rect.width() / 2, y + 2)
            else:
                label.setPos(x - rect.width() / 2, y - rect.height() - 2)

    def _create_label(self):
        font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        self.label = QGraphicsTextItem(self.uid, self)
        self.label.setFont(font)
        self.label.setDefaultTextColor(QColor("#0d47a1"))
        self.label.setPos(0, -16)

    def update_label(self):
        """Actualizeaza textul (id + valoare scurta)."""
        txt = self.uid
        v = self._short_value()
        if v:
            txt += f"  {v}"
        self.label.setPlainText(txt)

    def _short_value(self):
        """Reprezentare scurta a parametrului principal (afisat langa id)."""
        if self.kind == "R":
            return _eng_format(self.properties.get("resistance", 0), "Ω")
        if self.kind == "V":
            return _eng_format(self.properties.get("voltage", 0), "V")
        if self.kind == "I":
            return _eng_format(self.properties.get("current", 0), "A")
        if self.kind == "CAP":
            return _eng_format(self.properties.get("capacitance", 0), "F")
        if self.kind == "IND":
            return _eng_format(self.properties.get("inductance", 0), "H")
        if self.kind == "LED":
            return self.properties.get("color", "")
        if self.kind == "SW":
            return "ON" if self.properties.get("closed") else "OFF"
        return ""

    # ------------------------------------------------------------ rendering
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # fundal subtil + chenar daca e selectat / erori
        box = QRectF(0, 0, self.width, self.height)
        if self.highlight == "error":
            painter.setBrush(QBrush(QColor(255, 80, 80, 55)))
            painter.setPen(QPen(QColor("#c62828"), 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(box, 6, 6)
        elif self.highlight == "warning":
            painter.setBrush(QBrush(QColor(255, 200, 0, 55)))
            painter.setPen(QPen(QColor("#ef6c00"), 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(box, 6, 6)
        elif self.isSelected():
            painter.setBrush(QBrush(QColor(33, 150, 243, 35)))
            painter.setPen(QPen(QColor("#1976d2"), 2, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(box, 6, 6)

        # desenul simbolic propriu-zis
        painter.setPen(QPen(QColor("#212121"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        draw = _SYMBOLS.get(self.symbol, _draw_generic)
        draw(painter, self)

    def itemChange(self, change, value):
        # cand se misca componenta, redesenam firele atasate prin Pin.itemChange.
        return super().itemChange(change, value)

    def set_highlight(self, level):
        """level ∈ {None, 'ok', 'warning', 'error'}."""
        self.highlight = level
        self.update()

    # ----------------------------------------------------------------- prop
    def set_property(self, key, value):
        if key not in self.properties:
            return
        self.properties[key] = value
        self.update_label()
        self.update()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _eng_format(value, unit):
    """Formatare ingineresca: 1000 -> '1 kΩ', 1e-6 -> '1 µF'."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return f"{value} {unit}"
    if v == 0:
        return f"0 {unit}"
    sign = "-" if v < 0 else ""
    v = abs(v)
    prefixes = [(1e9, "G"), (1e6, "M"), (1e3, "k"), (1.0, ""),
                (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"), (1e-12, "p")]
    for mag, pref in prefixes:
        if v >= mag:
            return f"{sign}{v / mag:g} {pref}{unit}"
    return f"{sign}{v:g} {unit}"


# ---------------------------------------------------------------------------
# Desenele simbolurilor (functii pure, primesc painter + componenta)
# Toate componentele standard au pini la (0,30) si (60,30) (latime 60).
# ---------------------------------------------------------------------------

def _draw_generic(p, c):
    p.drawRoundedRect(8, 8, 44, 44, 4, 4)
    p.drawText(QRectF(8, 8, 44, 44),
               int(Qt.AlignmentFlag.AlignCenter), c.kind)


def _draw_resistor(p, c):
    # corp dreptunghi IEC + zig-zag ANSI optional la mijloc
    p.drawLine(0, 30, 12, 30)
    p.drawLine(48, 30, 60, 30)
    p.drawRect(12, 22, 36, 16)
    # mic zig-zag in interior pentru estetica
    p.setPen(QPen(QColor("#212121"), 1))
    pts = [QPointF(14, 30), QPointF(18, 24), QPointF(24, 36),
           QPointF(30, 24), QPointF(36, 36), QPointF(42, 24), QPointF(46, 30)]
    for i in range(len(pts) - 1):
        p.drawLine(pts[i], pts[i + 1])


def _draw_capacitor(p, c):
    p.drawLine(0, 30, 26, 30)
    p.drawLine(34, 30, 60, 30)
    p.drawLine(26, 12, 26, 48)
    p.drawLine(34, 12, 34, 48)


def _draw_inductor(p, c):
    p.drawLine(0, 30, 10, 30)
    p.drawLine(50, 30, 60, 30)
    # 4 bucle
    for i in range(4):
        x = 10 + i * 10
        p.drawArc(x, 22, 10, 16, 0 * 16, 180 * 16)


def _draw_vsource(p, c):
    p.drawLine(0, 30, 14, 30)
    p.drawLine(46, 30, 60, 30)
    p.drawEllipse(14, 8, 32, 44)
    f = QFont("Segoe UI", 12, QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(QRectF(18, 12, 12, 18), int(Qt.AlignmentFlag.AlignCenter), "+")
    p.drawText(QRectF(30, 30, 12, 18), int(Qt.AlignmentFlag.AlignCenter), "−")


def _draw_isource(p, c):
    p.drawLine(0, 30, 14, 30)
    p.drawLine(46, 30, 60, 30)
    p.drawEllipse(14, 8, 32, 44)
    # sageata sus → jos transformata in stanga → dreapta
    p.drawLine(22, 30, 38, 30)
    arrow = QPolygonF([QPointF(38, 30), QPointF(32, 26), QPointF(32, 34)])
    p.setBrush(QBrush(QColor("#212121")))
    p.drawPolygon(arrow)


def _draw_ground(p, c):
    # pin sus, simbol jos
    p.drawLine(30, 0, 30, 18)
    p.drawLine(18, 18, 42, 18)
    p.drawLine(22, 24, 38, 24)
    p.drawLine(26, 30, 34, 30)
    f = QFont("Segoe UI", 7)
    p.setFont(f)
    p.setPen(QColor("#616161"))
    p.drawText(QRectF(0, 36, 60, 14), int(Qt.AlignmentFlag.AlignCenter), "GND")


def _draw_diode(p, c):
    p.drawLine(0, 30, 22, 30)
    p.drawLine(38, 30, 60, 30)
    tri = QPolygonF([QPointF(22, 18), QPointF(22, 42), QPointF(38, 30)])
    p.setBrush(QBrush(QColor("#212121")))
    p.drawPolygon(tri)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(38, 18, 38, 42)


def _draw_led(p, c):
    _draw_diode(p, c)
    # doua sageti exterioare = lumina
    p.setPen(QPen(QColor("#ef6c00"), 1.5))
    for off in (0, 6):
        p.drawLine(36 + off, 14 - off, 48 + off, 2 - off)
        arrow = QPolygonF([
            QPointF(48 + off, 2 - off),
            QPointF(44 + off, 4 - off),
            QPointF(46 + off, 8 - off),
        ])
        p.setBrush(QBrush(QColor("#ef6c00")))
        p.drawPolygon(arrow)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # mic patrat de culoare in stanga sus, sugestiv pentru culoarea LED-ului
    color_map = {
        "rosu": "#e53935", "verde": "#43a047", "albastru": "#1e88e5",
        "galben": "#fdd835", "alb": "#eceff1",
    }
    fill = QColor(color_map.get(c.properties.get("color", "rosu"), "#e53935"))
    p.setBrush(QBrush(fill))
    p.setPen(QPen(QColor("#212121"), 1))
    p.drawEllipse(2, 2, 8, 8)
    p.setBrush(Qt.BrushStyle.NoBrush)


def _draw_photoresistor(p, c):
    _draw_resistor(p, c)
    # cerc cu sageti pentru lumina
    p.setPen(QPen(QColor("#fbc02d"), 1.5))
    p.drawEllipse(40, 0, 18, 18)
    p.drawLine(58, 0, 50, 8)
    arrow = QPolygonF([QPointF(50, 8), QPointF(54, 4), QPointF(56, 8)])
    p.setBrush(QBrush(QColor("#fbc02d")))
    p.drawPolygon(arrow)


def _draw_bjt_npn(p, c):
    # pini: B(0,30), C(60,0), E(60,60). desenam un cerc cu T in mijloc.
    p.drawEllipse(10, 5, 50, 50)
    p.drawLine(0, 30, 22, 30)        # spre baza
    p.drawLine(22, 14, 22, 46)       # bara baza
    p.drawLine(22, 22, 60, 0)        # spre colector
    p.drawLine(22, 38, 60, 60)       # spre emitor
    # sageata pe emitor (NPN: spre exterior)
    arrow = QPolygonF([QPointF(60, 60), QPointF(50, 54), QPointF(52, 50)])
    p.setBrush(QBrush(QColor("#212121")))
    p.drawPolygon(arrow)
    p.setBrush(Qt.BrushStyle.NoBrush)


def _draw_bjt_pnp(p, c):
    # pini: B(0,30), C(60,60), E(60,0).
    p.drawEllipse(10, 5, 50, 50)
    p.drawLine(0, 30, 22, 30)
    p.drawLine(22, 14, 22, 46)
    p.drawLine(22, 22, 60, 0)        # spre emitor
    p.drawLine(22, 38, 60, 60)       # spre colector
    # sageata pe emitor (PNP: spre interior)
    arrow = QPolygonF([QPointF(30, 18), QPointF(36, 16), QPointF(34, 12)])
    p.setBrush(QBrush(QColor("#212121")))
    p.drawPolygon(arrow)
    p.setBrush(Qt.BrushStyle.NoBrush)


def _draw_switch(p, c):
    p.drawLine(0, 30, 14, 30)
    p.drawLine(46, 30, 60, 30)
    p.setBrush(QBrush(QColor("#212121")))
    p.drawEllipse(11, 27, 6, 6)
    p.drawEllipse(43, 27, 6, 6)
    p.setBrush(Qt.BrushStyle.NoBrush)
    if c.properties.get("closed"):
        p.drawLine(14, 30, 46, 30)
    else:
        p.drawLine(14, 30, 46, 14)


def _draw_voltmeter(p, c):
    p.drawLine(0, 30, 14, 30)
    p.drawLine(46, 30, 60, 30)
    p.drawEllipse(14, 8, 32, 44)
    f = QFont("Segoe UI", 14, QFont.Weight.Bold)
    p.setFont(f)
    p.setPen(QColor("#1976d2"))
    p.drawText(QRectF(14, 12, 32, 36), int(Qt.AlignmentFlag.AlignCenter), "V")


def _draw_ammeter(p, c):
    p.drawLine(0, 30, 14, 30)
    p.drawLine(46, 30, 60, 30)
    p.drawEllipse(14, 8, 32, 44)
    f = QFont("Segoe UI", 14, QFont.Weight.Bold)
    p.setFont(f)
    p.setPen(QColor("#c62828"))
    p.drawText(QRectF(14, 12, 32, 36), int(Qt.AlignmentFlag.AlignCenter), "A")


def _draw_ultrasonic(p, c):
    p.drawRoundedRect(0, 0, 60, 60, 6, 6)
    p.drawEllipse(8, 8, 18, 18)
    p.drawEllipse(34, 8, 18, 18)
    f = QFont("Segoe UI", 7)
    p.setFont(f)
    p.drawText(QRectF(0, 28, 60, 12), int(Qt.AlignmentFlag.AlignCenter), "ULTRA")
    p.drawText(QRectF(0, 40, 60, 12), int(Qt.AlignmentFlag.AlignCenter),
               f"{c.properties.get('distance_cm', 0):.0f} cm")


def _draw_arduino(p, c):
    w, h = c.width, c.height
    # corp placa (bleu Arduino)
    p.setBrush(QBrush(QColor("#006d75")))
    p.setPen(QPen(QColor("#01383c"), 1.5))
    p.drawRoundedRect(QRectF(8, 8, w - 16, h - 16), 8, 8)
    # chip ATmega
    p.setBrush(QBrush(QColor("#212121")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(QRectF(w / 2 - 22, h / 2 - 18, 44, 36))
    # USB
    p.setBrush(QBrush(QColor("#cfd8dc")))
    p.drawRect(QRectF(-2, h / 2 - 14, 14, 28))
    # text Arduino
    p.setPen(QColor("#e0f7fa"))
    f = QFont("Segoe UI", 11, QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(QRectF(0, 8, w, 22),
               int(Qt.AlignmentFlag.AlignCenter), "ARDUINO")
    f.setPointSize(8)
    p.setFont(f)
    p.drawText(QRectF(0, h - 26, w, 18),
               int(Qt.AlignmentFlag.AlignCenter), "UNO R3")
    # mici LED-uri pe placa (TX/RX/Power/L13)
    p.setBrush(QBrush(QColor("#ffeb3b")))
    p.setPen(Qt.PenStyle.NoPen)
    for i in range(4):
        p.drawEllipse(QRectF(w - 22, 30 + i * 6, 4, 4))


def _draw_push_button(p, c):
    # corp + capac
    p.drawLine(0, 30, 14, 30)
    p.drawLine(46, 30, 60, 30)
    p.setBrush(QBrush(QColor("#ef9a9a")))
    p.drawEllipse(QRectF(20, 12, 20, 20))
    p.setBrush(Qt.BrushStyle.NoBrush)
    # contact intern
    pressed = bool(c.properties.get("pressed", False))
    if pressed:
        p.drawLine(14, 30, 46, 30)
    else:
        p.drawLine(14, 30, 24, 22)
        p.drawLine(36, 22, 46, 30)


def _draw_potentiometer(p, c):
    w, h = c.width, c.height
    p.drawLine(QPointF(0, 30), QPointF(14, 30))
    p.drawLine(QPointF(w - 14, 30), QPointF(w, 30))
    p.drawRect(QRectF(14, 22, w - 28, 16))
    p.setPen(QPen(QColor("#212121"), 1))
    n = 6
    pts = []
    for i in range(n + 1):
        x = 16 + i * ((w - 32) / n)
        y = 26 if i % 2 == 0 else 34
        pts.append(QPointF(x, y))
    for i in range(len(pts) - 1):
        p.drawLine(pts[i], pts[i + 1])
    p.setPen(QPen(QColor("#212121"), 2))
    p.drawLine(QPointF(w / 2, 0), QPointF(w / 2, 22))
    arrow = QPolygonF([
        QPointF(w / 2, 22),
        QPointF(w / 2 - 5, 14),
        QPointF(w / 2 + 5, 14),
    ])
    p.setBrush(QBrush(QColor("#212121")))
    p.drawPolygon(arrow)
    p.setBrush(Qt.BrushStyle.NoBrush)


def _draw_buzzer(p, c):
    p.drawLine(0, 30, 14, 30)
    p.drawLine(46, 30, 60, 30)
    # corp circular
    p.setBrush(QBrush(QColor("#212121")))
    p.drawEllipse(QRectF(14, 8, 32, 44))
    # interiorul = mic cerc cu '+' si '-'
    p.setBrush(QBrush(QColor("#424242")))
    p.drawEllipse(QRectF(22, 16, 16, 28))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QColor("#fdd835"))
    f = QFont("Segoe UI", 7, QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(QRectF(14, 12, 32, 14), int(Qt.AlignmentFlag.AlignCenter), "BUZ")


def _draw_servo(p, c):
    w, h = c.width, c.height
    p.setBrush(QBrush(QColor("#1565c0")))
    p.setPen(QPen(QColor("#0d47a1"), 1.5))
    p.drawRoundedRect(QRectF(10, 8, w - 20, h - 16), 4, 4)
    p.setBrush(QBrush(QColor("#ffffff")))
    p.setPen(QPen(QColor("#212121"), 2))
    p.drawEllipse(QRectF(w - 32, h / 2 - 12, 24, 24))
    import math
    angle = float(c.properties.get("angle", 90)) * math.pi / 180.0
    cx, cy = w - 20, h / 2
    end_x = cx + math.cos(angle - math.pi / 2) * 14
    end_y = cy + math.sin(angle - math.pi / 2) * 14
    p.setPen(QPen(QColor("#c62828"), 3))
    p.drawLine(QPointF(cx, cy), QPointF(end_x, end_y))
    p.setBrush(Qt.BrushStyle.NoBrush)
    f = QFont("Segoe UI", 7, QFont.Weight.Bold)
    p.setFont(f)
    p.setPen(QColor("white"))
    p.drawText(QRectF(10, 8, w - 40, 14),
               int(Qt.AlignmentFlag.AlignCenter), "SERVO")


def _draw_dc_motor(p, c):
    p.drawLine(0, 30, 14, 30)
    p.drawLine(46, 30, 60, 30)
    p.setBrush(QBrush(QColor("#fff8e1")))
    p.drawEllipse(QRectF(14, 8, 32, 44))
    p.setBrush(Qt.BrushStyle.NoBrush)
    # litera M
    f = QFont("Segoe UI", 16, QFont.Weight.Bold)
    p.setFont(f)
    p.setPen(QColor("#212121"))
    p.drawText(QRectF(14, 10, 32, 40), int(Qt.AlignmentFlag.AlignCenter), "M")


def _draw_lm35(p, c):
    w, h = c.width, c.height
    p.setBrush(QBrush(QColor("#37474f")))
    p.drawRoundedRect(QRectF(10, 8, w - 20, h - 16), 4, 4)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QColor("#ffeb3b"))
    f = QFont("Segoe UI", 9, QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(QRectF(10, 8, w - 20, 18),
               int(Qt.AlignmentFlag.AlignCenter), "LM35")
    p.setPen(QColor("white"))
    f.setPointSize(8)
    p.setFont(f)
    p.drawText(QRectF(10, h - 24, w - 20, 16),
               int(Qt.AlignmentFlag.AlignCenter),
               f"{c.properties.get('temperature', 25):.0f} °C")


def _draw_thermistor(p, c):
    _draw_resistor(p, c)
    # linie diagonala traversand corpul (simbolul de element variabil)
    p.setPen(QPen(QColor("#c62828"), 1.5))
    p.drawLine(8, 44, 52, 16)
    f = QFont("Segoe UI", 7, QFont.Weight.Bold)
    p.setFont(f)
    p.setPen(QColor("#c62828"))
    p.drawText(QRectF(48, 4, 18, 12), int(Qt.AlignmentFlag.AlignCenter), "T°")


def _draw_relay(p, c):
    w, h = c.width, c.height
    p.setBrush(QBrush(QColor("#fafafa")))
    p.drawRoundedRect(QRectF(10, 8, w - 20, h - 16), 6, 6)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # bobina (stanga)
    p.drawLine(14, 20, 24, 20)
    p.drawLine(14, 60, 24, 60)
    for i in range(4):
        p.drawArc(20, 20 + i * 10, 8, 10, 90 * 16, 180 * 16)
    # contact (dreapta)
    p.drawLine(86, 20, 76, 20)        # COM
    p.drawLine(86, 40, 76, 36)        # NO
    p.drawLine(86, 60, 76, 60)        # NC
    # bara mobila (afisam in pozitia NC implicit)
    p.setPen(QPen(QColor("#c62828"), 2))
    p.drawLine(76, 20, 76, 58)
    # eticheta
    p.setPen(QColor("#212121"))
    f = QFont("Segoe UI", 7, QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(QRectF(10, 8, w - 20, 14), int(Qt.AlignmentFlag.AlignCenter), "RELAY")


_SYMBOLS = {
    "resistor":      _draw_resistor,
    "capacitor":     _draw_capacitor,
    "inductor":      _draw_inductor,
    "vsource":       _draw_vsource,
    "isource":       _draw_isource,
    "ground":        _draw_ground,
    "diode":         _draw_diode,
    "led":           _draw_led,
    "photoresistor": _draw_photoresistor,
    "bjt_npn":       _draw_bjt_npn,
    "bjt_pnp":       _draw_bjt_pnp,
    "switch":        _draw_switch,
    "voltmeter":     _draw_voltmeter,
    "ammeter":       _draw_ammeter,
    "ultrasonic":    _draw_ultrasonic,
    "arduino_uno":   _draw_arduino,
    "push_button":   _draw_push_button,
    "potentiometer": _draw_potentiometer,
    "buzzer":        _draw_buzzer,
    "servo":         _draw_servo,
    "dc_motor":      _draw_dc_motor,
    "lm35":          _draw_lm35,
    "thermistor":    _draw_thermistor,
    "relay":         _draw_relay,
}
