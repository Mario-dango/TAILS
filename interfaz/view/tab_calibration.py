"""
PESTAÑA CALIBRACIÓN v2
-----------------------
Cambios respecto de la v1:
 · Los dos botones de inicialización dejan de ser cajas gigantes vacías:
   ahora son tarjetas de acción con nombre + comando G-code debajo.
 · Se numeran los pasos (1 · Inicialización, 2 · Garra) porque esta pestaña es
   un procedimiento, no un panel de opciones sueltas.
 · "Habilitar motores" pasa de checkbox perdido al pie a un toggle con
   explicación de la consecuencia.
 · Se agrega GripRange: se ve el recorrido real entre cerrado y abierto.

Expone: btn_home, btn_setzero, input_angle_open, btn_set_open,
        input_angle_close, btn_set_close, chk_enable  (+ grip_range)
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QLabel, QCheckBox, QFrame)
from PyQt5.QtCore import Qt
from view.ui_widgets import SectionCard, GripRange


def _action(title, command, tooltip):
    """Botón grande de dos líneas: acción + comando serial."""
    b = QPushButton()
    b.setMinimumHeight(56)
    b.setToolTip(tooltip)
    lay = QVBoxLayout(b)
    lay.setContentsMargins(52, 8, 12, 8)
    lay.setSpacing(3)
    t = QLabel(title)
    t.setStyleSheet("font-size:17px;font-weight:600;color:#e6e9ec;background:transparent;")
    c = QLabel(command)
    c.setStyleSheet("font-family:'IBM Plex Mono';font-size:14px;color:#6b757e;background:transparent;")
    lay.addWidget(t)
    lay.addWidget(c)
    return b


class CalibrationTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(9)

        # ══════════ PASO 1 ══════════
        top = QHBoxLayout()
        top.setSpacing(9)

        card_init = SectionCard("Paso 1 · Inicialización")
        hint = QLabel(
            "Antes de mover el brazo hay que buscar los finales de carrera. "
            "HOME ALL lleva los tres ejes a su referencia; Set Zero declara la "
            "posición actual como cero.")
        hint.setProperty("role", "hint")
        hint.setWordWrap(True)
        card_init.body.addWidget(hint)
        card_init.body.addSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(9)
        self.btn_home = _action(
            "HOME ALL", ":-H",
            "Ejecutar comando Home para inicializar las posiciones de referencia.")
        self.btn_setzero = _action(
            "Set Zero Here", ":-Z",
            "Setear un nuevo Zero Home en la posición actual.")
        row.addWidget(self.btn_home)
        row.addWidget(self.btn_setzero)
        card_init.body.addLayout(row)
        top.addWidget(card_init, 1)

        # motores
        card_mot = SectionCard("Motores")
        card_mot.setFixedWidth(250)
        self.chk_enable = QCheckBox("Motores habilitados")
        self.chk_enable.setChecked(True)
        self.chk_enable.setStyleSheet("font-size:17px;font-weight:600;")
        card_mot.body.addWidget(self.chk_enable)
        mot_hint = QLabel(
            "Con los motores deshabilitados el brazo se puede mover a mano, "
            "pero pierde la referencia.")
        mot_hint.setProperty("role", "hint")
        mot_hint.setWordWrap(True)
        card_mot.body.addWidget(mot_hint)
        card_mot.body.addStretch()
        top.addWidget(card_mot)

        root.addLayout(top)

        # ══════════ PASO 2 ══════════
        card_grip = SectionCard("Paso 2 · Configuración de garra")
        grid = QHBoxLayout()
        grid.setSpacing(16)

        fields = QVBoxLayout()
        fields.setSpacing(9)

        self.input_angle_open = QLineEdit("90")
        self.input_angle_open.setProperty("role", "numeric")
        self.input_angle_open.setFixedWidth(78)
        self.btn_set_open = QPushButton("Set apertura  :-A")
        self.btn_set_open.setToolTip("Setear la apertura de la garra.")

        self.input_angle_close = QLineEdit("0")
        self.input_angle_close.setProperty("role", "numeric")
        self.input_angle_close.setFixedWidth(78)
        self.btn_set_close = QPushButton("Set cierre  :-P")
        self.btn_set_close.setToolTip("Setear el cierre de la garra.")

        for label, field, button in (("Ángulo abierto", self.input_angle_open, self.btn_set_open),
                                     ("Ángulo cerrado", self.input_angle_close, self.btn_set_close)):
            block = QVBoxLayout()
            block.setSpacing(4)
            l = QLabel(label)
            l.setStyleSheet("font-size:16px;font-weight:600;color:#c7cfd6;")
            block.addWidget(l)
            line = QHBoxLayout()
            line.setSpacing(7)
            line.addWidget(field)
            deg = QLabel("°")
            deg.setStyleSheet("color:#6b757e;font-family:'IBM Plex Mono';")
            line.addWidget(deg)
            button.setFixedHeight(34)
            line.addWidget(button)
            line.addStretch()
            block.addLayout(line)
            fields.addLayout(block)

        grid.addLayout(fields, 1)

        vis = QVBoxLayout()
        vis.setSpacing(6)
        vlbl = QLabel("RECORRIDO DE GARRA")
        vlbl.setProperty("role", "section")
        self.grip_range = GripRange()
        self.grip_range.set_range(0, 90)
        vis.addWidget(vlbl)
        vis.addWidget(self.grip_range)
        vis.addStretch()
        holder = QFrame()
        holder.setFixedWidth(270)
        holder.setLayout(vis)
        grid.addWidget(holder)

        card_grip.body.addLayout(grid)
        root.addWidget(card_grip)
        root.addStretch()

        # mantener la visualización sincronizada con los campos
        self.input_angle_open.textChanged.connect(self._sync_range)
        self.input_angle_close.textChanged.connect(self._sync_range)

    def _sync_range(self):
        def val(w, d):
            try:
                return max(0, min(180, int(float(w.text()))))
            except ValueError:
                return d
        self.grip_range.set_range(val(self.input_angle_close, 0),
                                  val(self.input_angle_open, 90))
