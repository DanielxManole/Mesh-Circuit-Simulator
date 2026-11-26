"""
MainWindow -fereastra principala.

Aspect: paleta in stanga, canvas in centru, properties panel + results in dreapta.
Meniuri: Fisier (Nou/Deschide/Salveaza/Export/Iesire),
         Editare (Undo/Redo/Sterge/Curata),
         Vizualizare (Grila/Reset zoom/Fit),
         Simulare (Ruleaza/Stop/Animatie),
         Ajutor (Despre/Scurtaturi).
"""

import os
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QFileDialog, QMessageBox, QStatusBar, QToolBar,
    QWidget, QVBoxLayout, QLabel, QDialog, QTextBrowser, QPushButton,
    QHBoxLayout, QStyle,
)
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QFont
from PyQt6.QtCore import Qt, QTimer

from src.components_logic.wire_logic    import CircuitScene
from src.components_logic.component_palette import ComponentPalette
from src.ui.circuit_view        import CircuitView
from src.ui.properties_panel    import PropertiesPanel
from src.ui.results_view        import ResultsView

from src.calculation            import calculate_sys
from src.calculation.data_parsing import parse_circuit
from src.persistence            import save_project, load_project, autosave, load_autosave
from src.export                 import schematic_from_sys


APP_TITLE = "Simulator circuite electrice"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1380, 820)

        self.current_file = None
        self.dirty = False

        # ---- componente UI
        self.scene    = CircuitScene()
        self.view     = CircuitView(self.scene)
        self.palette  = ComponentPalette()
        self.props    = PropertiesPanel()
        self.results  = ResultsView()

        # ---- splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.palette)
        splitter.addWidget(self.view)
        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(self.props)
        right.addWidget(self.results)
        right.setStretchFactor(0, 1)
        right.setStretchFactor(1, 2)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([230, 800, 360])
        self.setCentralWidget(splitter)

        # ---- status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.coord_label = QLabel("  ")
        self.status.addPermanentWidget(self.coord_label)
        self.status.showMessage("Gata.")

        # ---- conexiuni
        self.scene.selectionMaybeChanged.connect(self._on_selection)
        self.scene.componentDoubleClicked.connect(self._on_double_click)
        self.scene.statusMessage.connect(self.status.showMessage)
        self.scene.changed.connect(self._on_scene_changed)

        # ---- meniuri si toolbar
        self._build_actions()
        self._build_menus()
        self._build_toolbar()

        # ---- autosave la fiecare 30s
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._do_autosave)
        self.autosave_timer.start(30_000)

        # ---- restaurare cache (daca exista)
        if load_autosave(self.scene):
            self.status.showMessage("Restaurat din cache. (Fisier > Nou pentru a reincepe)")

        self._refresh_title()

    # ----------------------------------------------------------- actions
    def _build_actions(self):
        st = self.style()

        self.act_new = QAction(st.standardIcon(QStyle.StandardPixmap.SP_FileIcon), "Nou", self)
        self.act_new.setShortcut(QKeySequence.StandardKey.New)
        self.act_new.triggered.connect(self._action_new)

        self.act_open = QAction(st.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Deschide...", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self._action_open)

        self.act_save = QAction(st.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Salveaza", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.triggered.connect(self._action_save)

        self.act_save_as = QAction("Salveaza ca...", self)
        self.act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.act_save_as.triggered.connect(self._action_save_as)

        self.act_export = QAction("Exporta schema (PNG)...", self)
        self.act_export.setShortcut(QKeySequence("Ctrl+E"))
        self.act_export.triggered.connect(self._action_export)

        self.act_quit = QAction("Iesire", self)
        self.act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        self.act_quit.triggered.connect(self.close)

        # editare
        self.act_undo = self.scene.undo_stack.createUndoAction(self, "Anuleaza")
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_redo = self.scene.undo_stack.createRedoAction(self, "Reaplica")
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)

        self.act_delete = QAction("Sterge selectia", self)
        self.act_delete.setShortcut(QKeySequence.StandardKey.Delete)
        self.act_delete.triggered.connect(self._action_delete)

        self.act_clear = QAction("Curata canvas-ul", self)
        self.act_clear.triggered.connect(self._action_clear)

        # vizualizare
        self.act_grid = QAction("Arata grila", self, checkable=True, checked=True)
        self.act_grid.triggered.connect(lambda v: self.view.toggle_grid(v))

        self.act_snap = QAction("Snap pe grila", self, checkable=True, checked=True)
        self.act_snap.triggered.connect(self._toggle_snap)

        self.act_fit = QAction("Incadreaza tot", self)
        self.act_fit.setShortcut(QKeySequence("Ctrl+0"))
        self.act_fit.triggered.connect(self.view.fit_circuit)

        self.act_reset_zoom = QAction("Zoom 100%", self)
        self.act_reset_zoom.setShortcut(QKeySequence("Ctrl+1"))
        self.act_reset_zoom.triggered.connect(self.view.reset_zoom)

        # simulare
        self.act_run = QAction(st.standardIcon(QStyle.StandardPixmap.SP_MediaPlay), "Ruleaza simularea", self)
        self.act_run.setShortcut(QKeySequence("F5"))
        self.act_run.triggered.connect(self._action_run)

        self.act_stop = QAction(st.standardIcon(QStyle.StandardPixmap.SP_MediaStop), "Opreste animatia", self)
        self.act_stop.setShortcut(QKeySequence("Shift+F5"))
        self.act_stop.triggered.connect(self._action_stop)

        # ajutor
        self.act_help = QAction("Scurtaturi & Ajutor", self)
        self.act_help.setShortcut(QKeySequence.StandardKey.HelpContents)
        self.act_help.triggered.connect(self._action_help)

        self.act_about = QAction("Despre", self)
        self.act_about.triggered.connect(self._action_about)

    def _build_menus(self):
        mb = self.menuBar()
        m_file = mb.addMenu("&Fisier")
        m_file.addAction(self.act_new)
        m_file.addAction(self.act_open)
        # ---- submeniu cu exemplele incluse
        self.m_examples = m_file.addMenu("Deschide &exemplu")
        self._populate_examples()
        m_file.addAction(self.act_save)
        m_file.addAction(self.act_save_as)
        m_file.addSeparator()
        m_file.addAction(self.act_export)
        m_file.addSeparator()
        m_file.addAction(self.act_quit)

        m_edit = mb.addMenu("&Editare")
        m_edit.addAction(self.act_undo)
        m_edit.addAction(self.act_redo)
        m_edit.addSeparator()
        m_edit.addAction(self.act_delete)
        m_edit.addAction(self.act_clear)

        m_view = mb.addMenu("&Vizualizare")
        m_view.addAction(self.act_grid)
        m_view.addAction(self.act_snap)
        m_view.addSeparator()
        m_view.addAction(self.act_fit)
        m_view.addAction(self.act_reset_zoom)

        m_sim = mb.addMenu("&Simulare")
        m_sim.addAction(self.act_run)
        m_sim.addAction(self.act_stop)

        m_help = mb.addMenu("&Ajutor")
        m_help.addAction(self.act_help)
        m_help.addAction(self.act_about)

    def _build_toolbar(self):
        tb = QToolBar("Principal")
        tb.setIconSize(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon).availableSizes()[0])
        tb.setMovable(False)
        self.addToolBar(tb)
        tb.addAction(self.act_new)
        tb.addAction(self.act_open)
        tb.addAction(self.act_save)
        tb.addSeparator()
        tb.addAction(self.act_undo)
        tb.addAction(self.act_redo)
        tb.addSeparator()
        tb.addAction(self.act_run)
        tb.addAction(self.act_stop)
        tb.addSeparator()
        tb.addAction(self.act_fit)

    # ----------------------------------------------------------- handlers
    def _on_selection(self, comp):
        self.props.show_component(comp)

    def _on_double_click(self, comp):
        self.props.show_component(comp)

    def _on_scene_changed(self, *_):
        if not self.dirty:
            self.dirty = True
            self._refresh_title()

    def _toggle_snap(self, on):
        self.scene.snap_enabled = on
        self.status.showMessage(f"Snap pe grila: {'pornit' if on else 'oprit'}.")

    def _refresh_title(self):
        name = os.path.basename(self.current_file) if self.current_file else "circuit nou"
        mark = " *" if self.dirty else ""
        self.setWindowTitle(f"{APP_TITLE} - {name}{mark}")

    # ----------------------------------------------------------- File
    def _confirm_discard(self) -> bool:
        if not self.dirty:
            return True
        r = QMessageBox.question(
            self, "Modificari nesalvate",
            "Ai modificari nesalvate. Vrei sa continui?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return r == QMessageBox.StandardButton.Yes

    def _action_new(self):
        if not self._confirm_discard():
            return
        self.scene.clear_circuit()
        self.current_file = None
        self.dirty = False
        self.results.clear()
        self.props.show_component(None)
        self._refresh_title()
        self.status.showMessage("Canvas nou.")

    def _populate_examples(self):
        """Listeaza toate proiectele din folderul `examples/`."""
        self.m_examples.clear()
        examples_dir = self._examples_dir()
        labels = {
            "arduino_night_light.json":   "Arduino - Night-light (LDR + LED + pot)",
            "voltage_divider.json":       "Divizor de tensiune 9V (R1=1k, R2=2.2k)",
            "arduino_buzzer_button.json": "Arduino - Buzzer (PWM) + Buton + LED",
        }
        if not os.path.isdir(examples_dir):
            empty = QAction("(nu exista exemple)", self)
            empty.setEnabled(False)
            self.m_examples.addAction(empty)
            return
        any_added = False
        for fname in sorted(os.listdir(examples_dir)):
            if not fname.endswith(".json"):
                continue
            label = labels.get(fname, fname)
            act = QAction(label, self)
            full = os.path.join(examples_dir, fname)
            act.triggered.connect(lambda _checked=False, p=full: self._open_path(p))
            self.m_examples.addAction(act)
            any_added = True
        if not any_added:
            empty = QAction("(nu exista exemple)", self)
            empty.setEnabled(False)
            self.m_examples.addAction(empty)

    def _examples_dir(self):
        # rezolva relativ la radacina proiectului (un nivel deasupra src/)
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(here, "..", "..", "examples"))

    def _open_path(self, path):
        if not self._confirm_discard():
            return
        try:
            self.scene.clear_circuit()
            load_project(path, self.scene)
            self.current_file = path
            self.dirty = False
            self.results.clear()
            self.props.show_component(None)
            self._refresh_title()
            self.view.fit_circuit()
            self.status.showMessage(f"Deschis exemplu: {os.path.basename(path)}")
            logging.getLogger().info(f"Exemplu deschis: {path}")
        except Exception as ex:
            QMessageBox.critical(self, "Eroare", f"Nu am putut deschide:\n{ex}")

    def _action_open(self):
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Deschide proiect", "", "Proiect circuit (*.json)"
        )
        if not path:
            return
        try:
            self.scene.clear_circuit()
            load_project(path, self.scene)
            self.current_file = path
            self.dirty = False
            self.results.clear()
            self.props.show_component(None)
            self._refresh_title()
            self.view.fit_circuit()
            logging.getLogger().info(f"Proiect deschis: {path}")
            self.status.showMessage(f"Deschis: {os.path.basename(path)}")
        except Exception as ex:
            QMessageBox.critical(self, "Eroare", f"Nu am putut deschide:\n{ex}")

    def _action_save(self):
        if not self.current_file:
            return self._action_save_as()
        try:
            save_project(self.current_file, self.scene)
            self.dirty = False
            self._refresh_title()
            logging.getLogger().info(f"Proiect salvat: {self.current_file}")
            self.status.showMessage(f"Salvat: {os.path.basename(self.current_file)}")
        except Exception as ex:
            QMessageBox.critical(self, "Eroare", f"Nu am putut salva:\n{ex}")

    def _action_save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salveaza proiect", "circuit.json", "Proiect circuit (*.json)"
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        self.current_file = path
        self._action_save()

    def _action_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporta schema", "schema.png", "Imagine PNG (*.png)"
        )
        if not path:
            return
        include = QMessageBox.question(
            self, "Export schema",
            "Sa includem valorile parametrilor pe schema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes
        try:
            out = schematic_from_sys(self.scene, path, include_params=include)
            self.status.showMessage(f"Exportat: {os.path.basename(out)}")
        except Exception as ex:
            QMessageBox.critical(self, "Eroare", f"Export esuat:\n{ex}")

    # ----------------------------------------------------------- Edit
    def _action_delete(self):
        from src.components.wire import Wire
        from src.components.component_item import ComponentItem
        from src.components_logic.commands import DeleteWireCommand, DeleteComponentCommand
        for item in list(self.scene.selectedItems()):
            if isinstance(item, Wire):
                self.scene.undo_stack.push(DeleteWireCommand(self.scene, item))
            elif isinstance(item, ComponentItem):
                self.scene.undo_stack.push(DeleteComponentCommand(self.scene, item))

    def _action_clear(self):
        if not self._confirm_discard():
            return
        self.scene.clear_circuit()
        self.results.clear()
        self.props.show_component(None)
        self.status.showMessage("Canvas curatat.")

    # ----------------------------------------------------------- Simulate
    def _action_run(self):
        self.scene.clear_highlights()
        parsed = parse_circuit(self.scene)
        result = calculate_sys(parsed)
        self.scene.apply_result(result)
        self.results.show_result(result, parsed.pin_node)
        if result.ok:
            self.scene.start_animation()
            logging.getLogger().info(
                f"Simulare ok: {len(parsed.elements)} elemente, "
                f"{result.iterations} iteratii, {result.runtime_ms:.1f}ms"
            )
        else:
            self.scene.stop_animation()
            err_count = len(result.errors_only())
            warn_count = len(result.warnings_only())
            logging.getLogger().warning(
                f"Simulare cu probleme: {err_count} erori, {warn_count} avertismente"
            )
            if err_count:
                first = result.errors_only()[0]
                QMessageBox.warning(
                    self, "Simulare oprita",
                    f"[{first.where}] {first.why}\n\n"
                    f"Vezi tab-ul 'Mesaje' pentru detalii."
                )

    def _action_stop(self):
        self.scene.stop_animation()
        self.scene.clear_highlights()
        self.status.showMessage("Animatie oprita.")

    # ----------------------------------------------------------- Help
    def _action_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Scurtaturi & Ajutor")
        dlg.resize(640, 520)
        layout = QVBoxLayout(dlg)
        br = QTextBrowser()
        br.setOpenExternalLinks(True)
        br.setHtml(HELP_HTML)
        layout.addWidget(br, 1)
        btn = QPushButton("Inchide")
        btn.clicked.connect(dlg.accept)
        bar = QHBoxLayout(); bar.addStretch(1); bar.addWidget(btn)
        layout.addLayout(bar)
        dlg.exec()

    def _action_about(self):
        QMessageBox.about(
            self, "Despre",
            "<h3>Simulator circuite electrice</h3>"
            "<p>Aplicatie didactica pentru construirea si simularea de circuite "
            "electrice prin drag-and-drop.</p>"
            "<p>Echipa 631AB Sg.2, FIIR-SIA: Andrei, Manole, Pralea.</p>"
            "<p>Motor: Analiza Nodala Modificata (MNA). UI: PyQt6.</p>"
        )

    # ----------------------------------------------------------- close
    def closeEvent(self, event):
        if not self._confirm_discard():
            event.ignore()
            return
        autosave(self.scene)
        logging.getLogger().info("=== Aplicatie inchisa ===")
        super().closeEvent(event)

    # ----------------------------------------------------------- helpers
    def _do_autosave(self):
        if self.dirty:
            path = autosave(self.scene)
            if path:
                self.status.showMessage("Autosave...", 1500)


HELP_HTML = """
<h2>Scurtaturi & ghid rapid</h2>

<h3>Construirea circuitului</h3>
<ul>
  <li><b>Trage</b> o componenta din paleta in canvas.</li>
  <li><b>Click pe un pin</b> (cercul galben) si apoi pe alt pin = fir intre ele.</li>
  <li><b>Dublu-click</b> pe o componenta = editare parametri in panoul din dreapta.</li>
  <li><b>Esc</b> = anuleaza tragerea unui fir.</li>
</ul>

<h3>Editare</h3>
<ul>
  <li><b>Delete / Backspace</b> - sterge componenta sau firul selectat.</li>
  <li><b>Ctrl+Z / Ctrl+Y</b> - Undo / Redo.</li>
  <li><b>Ctrl+N / Ctrl+O / Ctrl+S</b> - fisier Nou / Deschide / Salveaza.</li>
  <li><b>Ctrl+E</b> - exporta schema ca PNG.</li>
</ul>

<h3>Vizualizare</h3>
<ul>
  <li><b>Rotita mouse-ului</b> - zoom in/out.</li>
  <li><b>Buton mijlociu + drag</b> - pan.</li>
  <li><b>Ctrl+0 / Ctrl+1</b> - fit-to-content / zoom 100%.</li>
</ul>

<h3>Simulare</h3>
<ul>
  <li><b>F5</b> - ruleaza simularea (DC).</li>
  <li><b>Shift+F5</b> - opreste animatia curentului.</li>
  <li>Tensiunile nodale, curentii si mesajele apar in panoul din dreapta.</li>
  <li>Componentele cu probleme sunt evidentiate cu chenar rosu/portocaliu.</li>
</ul>

<h3>Recomandari</h3>
<ul>
  <li>Plaseaza intotdeauna o componenta <b>GND</b> - fara ea, motorul alege automat
      un nod de referinta.</li>
  <li>Pune un <b>rezistor in serie cu LED-ul</b> ca sa nu-l arzi.</li>
  <li>Foloseste <b>voltmetrul/ampermetrul</b> pentru masurari precise.</li>
</ul>
"""
