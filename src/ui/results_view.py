"""
Results View — afisare numerica (tabel cu noduri si componente) + grafica
(bare cu tensiuni nodale). Foloseste doar QPainter, fara dependinte externe.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QTabWidget, QTextEdit, QSizePolicy, QPushButton,
    QFileDialog, QMessageBox,
)
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPalette, QPixmap
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF, pyqtSignal


def _eng(v, unit):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return f"{v} {unit}"
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x == 0:
        return f"0 {unit}"
    for mag, pref in [(1e9, "G"), (1e6, "M"), (1e3, "k"), (1.0, ""),
                      (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"), (1e-12, "p")]:
        if x >= mag:
            return f"{sign}{x/mag:.3g} {pref}{unit}"
    return f"{sign}{x:.3g} {unit}"


class _BarChart(QWidget):
    """Diagrama cu bare pentru tensiunile nodale — pictata in QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []   # [(label, value)]
        self.setMinimumHeight(220)

    def set_data(self, data):
        self.data = list(data)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        self._render(p, self.width(), self.height())
        p.end()

    def render_to_pixmap(self, width=900, height=520):
        """Genereaza un QPixmap cu graficul curent (folosit la export)."""
        pix = QPixmap(int(width), int(height))
        pix.fill(QColor("#ffffff"))
        p = QPainter(pix)
        self._render(p, width, height, background=QColor("#ffffff"))
        p.end()
        return pix

    def _render(self, p, w, h, background=QColor("#fafafa")):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(QRectF(0, 0, w, h), background)

        if not self.data:
            p.setPen(QColor("#9e9e9e"))
            p.drawText(QRectF(0, 0, w, h), int(Qt.AlignmentFlag.AlignCenter),
                       "Ruleaza simularea pentru a vedea tensiunile nodale.")
            return

        margin_l = 50
        margin_b = 36
        margin_t = 16
        margin_r = 16
        chart_w = w - margin_l - margin_r
        chart_h = h - margin_t - margin_b
        if chart_w <= 0 or chart_h <= 0:
            return

        vals = [v for _, v in self.data]
        vmin = min(0.0, min(vals))
        vmax = max(0.0, max(vals))
        if vmax == vmin:
            vmax = vmin + 1.0

        def y(value):
            return margin_t + chart_h - (value - vmin) / (vmax - vmin) * chart_h

        p.setPen(QPen(QColor("#bdbdbd"), 1))
        p.drawLine(QLineF(margin_l, y(0), margin_l + chart_w, y(0)))
        p.setPen(QPen(QColor("#9e9e9e"), 1))
        p.drawLine(QLineF(margin_l, margin_t, margin_l, margin_t + chart_h))

        p.setFont(QFont("Segoe UI", 8))
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            v = vmin + (vmax - vmin) * frac
            yy = y(v)
            p.setPen(QPen(QColor("#e0e0e0"), 1, Qt.PenStyle.DashLine))
            p.drawLine(QLineF(margin_l, yy, margin_l + chart_w, yy))
            p.setPen(QColor("#616161"))
            p.drawText(QRectF(0, yy - 8, margin_l - 4, 16),
                       int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                       f"{v:.2f} V")

        n = len(self.data)
        slot = chart_w / max(n, 1)
        bar_w = max(8, slot * 0.6)
        for i, (label, v) in enumerate(self.data):
            cx = margin_l + slot * (i + 0.5)
            top = y(max(v, 0))
            bot = y(min(v, 0))
            color = QColor("#1e88e5") if v >= 0 else QColor("#e53935")
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(cx - bar_w / 2, top, bar_w, max(2.0, bot - top)),
                              3, 3)
            p.setPen(QColor("#212121"))
            p.drawText(QRectF(cx - 40, (top - 16) if v >= 0 else (bot + 2), 80, 14),
                       int(Qt.AlignmentFlag.AlignCenter), f"{v:.2f} V")
            p.drawText(QRectF(cx - slot / 2, margin_t + chart_h + 4, slot, 16),
                       int(Qt.AlignmentFlag.AlignCenter), str(label))


class ResultsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(320)
        self.setMaximumWidth(480)

        # ultimul rezultat (folosit la export CSV)
        self._last_result = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Rezultate simulare")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        self.status = QLabel("Apasa Ruleaza simularea (F5).")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: #616161; padding: 4px;")
        layout.addWidget(self.status)

        # bara cu butoane de export
        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(4)
        self.btn_export_png = QPushButton("Exporta grafic (PNG)")
        self.btn_export_csv = QPushButton("Exporta date (CSV)")
        self.btn_export_png.setEnabled(False)
        self.btn_export_csv.setEnabled(False)
        self.btn_export_png.clicked.connect(self._export_chart_png)
        self.btn_export_csv.clicked.connect(self._export_csv)
        bar.addWidget(self.btn_export_png)
        bar.addWidget(self.btn_export_csv)
        bar.addStretch(1)
        layout.addLayout(bar)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        # ----- componente
        self.comp_table = QTableWidget(0, 3)
        self.comp_table.setHorizontalHeaderLabels(["Componenta", "Tensiune", "Curent"])
        self.comp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.comp_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.comp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabs.addTab(self.comp_table, "Componente")

        # ----- noduri
        self.node_table = QTableWidget(0, 2)
        self.node_table.setHorizontalHeaderLabels(["Nod", "Tensiune (V)"])
        self.node_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.node_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.node_table, "Noduri")

        # ----- grafic
        self.chart = _BarChart()
        self.tabs.addTab(self.chart, "Grafic")

        # ----- erori/avertismente
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("background:#fffde7; border:0;")
        self.tabs.addTab(self.log, "Mesaje")

    # ----------------------------------------------------------------- API
    def clear(self):
        self.status.setText("Apasa Ruleaza simularea (F5).")
        self.comp_table.setRowCount(0)
        self.node_table.setRowCount(0)
        self.chart.set_data([])
        self.log.clear()
        self._last_result = None
        self.btn_export_png.setEnabled(False)
        self.btn_export_csv.setEnabled(False)

    def show_result(self, result, pin_to_node):
        self._last_result = result
        self.btn_export_png.setEnabled(True)
        self.btn_export_csv.setEnabled(True)
        if result.ok:
            self.status.setText(
                f"OK - simulare reusita in {result.runtime_ms:.1f} ms "
                f"({result.iterations} iteratii)."
            )
            self.status.setStyleSheet("color: #2e7d32; padding: 4px; font-weight: bold;")
        elif result.errors_only():
            self.status.setText(
                f"EROARE - simulare oprita: {len(result.errors_only())} eroare/i. "
                f"Vezi tab-ul 'Mesaje'."
            )
            self.status.setStyleSheet("color: #c62828; padding: 4px; font-weight: bold;")
        else:
            self.status.setText(
                f"AVERTISMENT - simulare finalizata cu {len(result.warnings_only())} mesaj(e)."
            )
            self.status.setStyleSheet("color: #ef6c00; padding: 4px; font-weight: bold;")

        # componente
        self.comp_table.setRowCount(len(result.components))
        for r, (uid, data) in enumerate(sorted(result.components.items())):
            v = data.get("V", 0.0)
            i = data.get("I", 0.0)
            self.comp_table.setItem(r, 0, QTableWidgetItem(uid))
            self.comp_table.setItem(r, 1, QTableWidgetItem(_eng(v, "V")))
            self.comp_table.setItem(r, 2, QTableWidgetItem(_eng(i, "A")))

        # noduri
        nodes = sorted(result.node_voltages.items())
        self.node_table.setRowCount(len(nodes))
        for r, (nid, v) in enumerate(nodes):
            label = "GND (0)" if nid == 0 else f"N{nid}"
            self.node_table.setItem(r, 0, QTableWidgetItem(label))
            self.node_table.setItem(r, 1, QTableWidgetItem(f"{v:.4f}"))

        # grafic
        bar_data = [("GND" if nid == 0 else f"N{nid}", v)
                    for nid, v in nodes]
        self.chart.set_data(bar_data)

        # mesaje
        lines = []
        for e in result.errors:
            tag = {"error": "EROARE", "warning": "AVERT.", "info": "INFO"}.get(e.level, "-")
            lines.append(f"[{tag}] [{e.where}] {e.why}")
            if e.suggestion:
                lines.append(f"     -> Sugestie: {e.suggestion}")
        if not lines:
            lines = ["Niciun mesaj - totul e ok."]
        self.log.setPlainText("\n".join(lines))

    # ---------------------------------------------------------------- export
    def _export_chart_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporta grafic ca PNG", "rezultate_grafic.png",
            "Imagine PNG (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        try:
            pix = self.chart.render_to_pixmap(width=1100, height=600)
            if not pix.save(path):
                raise IOError("salvarea fisierului a esuat")
        except Exception as ex:
            QMessageBox.critical(self, "Eroare export",
                                 f"Nu am putut salva graficul:\n{ex}")
            return
        QMessageBox.information(self, "Export reusit",
                                f"Graficul a fost salvat:\n{path}")

    def _export_csv(self):
        if self._last_result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporta date ca CSV", "rezultate.csv",
            "Fisier CSV (*.csv)"
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        r = self._last_result
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Rezultate simulare\n")
                f.write(f"# iteratii: {r.iterations}\n")
                f.write(f"# timp_ms: {r.runtime_ms:.2f}\n")
                f.write("# --- Noduri ---\n")
                f.write("nod,tensiune_V\n")
                for nid, v in sorted(r.node_voltages.items()):
                    name = "GND" if nid == 0 else f"N{nid}"
                    f.write(f"{name},{v:.6f}\n")
                f.write("\n# --- Componente ---\n")
                f.write("uid,tensiune_V,curent_A,putere_W\n")
                for uid, data in sorted(r.components.items()):
                    V = data.get("V", 0.0)
                    I = data.get("I", 0.0)
                    P = V * I
                    f.write(f"{uid},{V:.6f},{I:.6e},{P:.6e}\n")
                f.write("\n# --- Mesaje ---\n")
                f.write("nivel,locatie,mesaj\n")
                for e in r.errors:
                    msg = e.why.replace(",", ";").replace("\n", " ")
                    f.write(f"{e.level},{e.where},{msg}\n")
        except Exception as ex:
            QMessageBox.critical(self, "Eroare export",
                                 f"Nu am putut salva CSV-ul:\n{ex}")
            return
        QMessageBox.information(self, "Export reusit",
                                f"Datele au fost salvate:\n{path}")
