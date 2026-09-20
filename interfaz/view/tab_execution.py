"""
PESTAÑA EJECUCIÓN v2
---------------------
Cambios respecto de la v1:
 · La fila "Archivo: Ninguno cargado + 2 botones" se convierte en una tarjeta
   con icono, ruta monoespaciada y cantidad de puntos.
 · Progreso muestra porcentaje grande y "paso N de M": antes la QProgressBar
   estaba suelta, sin contexto.
 · PLAY / PAUSA / DETENER usan variantes semánticas del stylesheet en lugar de
   setStyleSheet inline por botón.
 · NUEVO: panel lateral "Secuencia" con los pasos de la rutina; el paso en
   curso se resalta. Esto era lo único que faltaba para entender qué está
   haciendo el robot sin leer el log.

Expone: lbl_file, btn_load_file, btn_preview, progress_bar, btn_play,
        btn_pause, btn_stop_run, txt_run_log  (+ list_steps, lbl_step)
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QProgressBar, QTextEdit, QListWidget, QListWidgetItem,
                             QFrame, QAbstractItemView)
from PyQt5.QtCore import Qt
from view.ui_widgets import SectionCard


class ExecutionTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(9)

        main = QVBoxLayout()
        main.setSpacing(9)

        # ══════════ ARCHIVO ══════════
        card_file = SectionCard("Rutina cargada")
        file_row = QHBoxLayout()
        file_row.setSpacing(12)

        self.lbl_file_icon = QLabel()          # icono asignado desde view.py
        self.lbl_file_icon.setFixedSize(45, 45)
        file_row.addWidget(self.lbl_file_icon)

        self.lbl_file = QLabel("Ninguna rutina cargada")
        self.lbl_file.setStyleSheet(
            "font-family:'IBM Plex Mono';font-size:17px;color:#e6e9ec;")
        file_row.addWidget(self.lbl_file, 1)

        self.lbl_points = QLabel("0 puntos")
        self.lbl_points.setProperty("role", "chip")
        file_row.addWidget(self.lbl_points)

        self.btn_load_file = QPushButton("  Cargar")
        self.btn_load_file.setToolTip("Cargar archivo de rutina en formato JSON.")
        self.btn_preview = QPushButton("  Ver contenido")
        self.btn_preview.setProperty("variant", "warning")
        self.btn_preview.setToolTip("Ver el contenido del archivo JSON cargado.")
        for b in (self.btn_load_file, self.btn_preview):
            b.setFixedHeight(38)
            file_row.addWidget(b)

        card_file.body.addLayout(file_row)
        main.addWidget(card_file)

        # ══════════ PROGRESO + TRANSPORTE ══════════
        self.lbl_progress_pct = QLabel("0%")
        self.lbl_progress_pct.setStyleSheet(
            "color:#4fc0ff;font-family:'IBM Plex Mono';font-size:20px;")
        card_run = SectionCard("Progreso", right_widget=self.lbl_progress_pct)

        self.lbl_step = QLabel("sin ejecutar")
        self.lbl_step.setStyleSheet(
            "color:#9aa4ae;font-family:'IBM Plex Mono';font-size:14px;")
        card_run.add_header_widget(self.lbl_step)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(14)
        card_run.body.addWidget(self.progress_bar)
        card_run.body.addSpacing(5)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        self.btn_play = QPushButton("  PLAY")
        self.btn_play.setProperty("variant", "success")
        self.btn_play.setToolTip("Ejecutar la rutina cargada.")
        self.btn_pause = QPushButton("  PAUSA")
        self.btn_pause.setProperty("variant", "warning")
        self.btn_pause.setToolTip("Pausar la rutina en ejecución.")
        self.btn_stop_run = QPushButton("  DETENER")
        self.btn_stop_run.setProperty("variant", "danger")
        self.btn_stop_run.setToolTip(
            "Detener la rutina en ejecución (no engancha la parada de emergencia).")
        self.btn_repeat = QPushButton("  REPETIR")
        self.btn_repeat.setProperty("variant", "primary")
        self.btn_repeat.setToolTip(
            "Ejecutar la rutina en bucle: N ciclos o de forma continua.")
        for b in (self.btn_play, self.btn_pause, self.btn_stop_run,
                  self.btn_repeat):
            b.setProperty("variant", b.property("variant"))
            b.setMinimumHeight(70)
        self.btn_play.setStyleSheet("")   # variantes vienen del stylesheet global
        self.btn_pause.setFixedWidth(176)
        self.btn_stop_run.setFixedWidth(176)
        self.btn_repeat.setFixedWidth(176)
        ctrl.addWidget(self.btn_play, 1)
        ctrl.addWidget(self.btn_repeat)
        ctrl.addWidget(self.btn_pause)
        ctrl.addWidget(self.btn_stop_run)
        card_run.body.addLayout(ctrl)
        main.addWidget(card_run)

        # ══════════ LOG ══════════
        card_log = SectionCard("Log de ejecución")
        self.txt_run_log = QTextEdit()
        self.txt_run_log.setReadOnly(True)
        self.txt_run_log.setPlaceholderText(
            "Los detalles de ejecución de la rutina aparecerán aquí…")
        card_log.body.addWidget(self.txt_run_log)
        main.addWidget(card_log, 1)

        root.addLayout(main, 1)

        # ══════════ SECUENCIA (nuevo) ══════════
        card_seq = SectionCard("Secuencia")
        card_seq.setFixedWidth(316)
        self.list_steps = QListWidget()
        self.list_steps.setSelectionMode(QAbstractItemView.NoSelection)
        self.list_steps.setStyleSheet(
            "QListWidget{background:transparent;border:0;}"
            "QListWidget::item{background:transparent;border:1px solid transparent;"
            "border-radius:7px;padding:8px 9px;margin-bottom:3px;color:#c7cfd4;"
            "font-family:'IBM Plex Mono';font-size:14px;}"
            "QListWidget::item[current='true']{background:#0e2b38;border-color:#2a7fb8;}")
        card_seq.body.addWidget(self.list_steps)
        root.addWidget(card_seq)

    # ---------- API opcional para el controlador ----------
    def set_sequence(self, points):
        """points: lista de dicts con x, y, z, g, v y, opcionalmente, n (nombre)."""
        self.list_steps.clear()
        for i, p in enumerate(points, start=1):
            garra = "ABR" if str(p.get("g", "")).upper().startswith("A") else "CER"
            coords = "X%3s  Y%3s  Z%3s   %s   %s%%" % (
                p.get("x", 0), p.get("y", 0), p.get("z", 0), garra, p.get("v", 50))
            # Si el punto tiene nombre, encabeza la línea: da contexto de un vistazo.
            nombre = str(p.get("n", "")).strip()
            txt = ("%02d  %s\n      %s" % (i, nombre, coords) if nombre
                   else "%02d   %s" % (i, coords))
            self.list_steps.addItem(QListWidgetItem(txt))
        self.lbl_points.setText("%d puntos" % len(points))

    def highlight_step(self, index):
        """Resalta el paso en curso (0-based)."""
        for i in range(self.list_steps.count()):
            it = self.list_steps.item(i)
            it.setForeground(Qt.white if i == index else Qt.gray)
            font = it.font()
            font.setBold(i == index)
            it.setFont(font)
        if 0 <= index < self.list_steps.count():
            self.list_steps.setCurrentRow(index)
