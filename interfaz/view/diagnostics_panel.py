"""
PANEL DE TEST / DIAGNÓSTICO (Ventana emergente)
Herramienta para probar el hardware pieza por pieza sin depender de una rutina
ni de la calibración: prende/apaga cada LED y mueve cada motor de forma
independiente y relativa. Ideal para verificar conexiones y cableado.

Usa los comandos de test del firmware (prefijo :*):
    :*L<H|W|F|P><0|1>      -> LED on/off
    :*M<X|Y|Z><+|-><nnn>   -> mover un motor (pasos relativos)
    :*G<A|C>               -> garra abrir/cerrar

Es autocontenido: recibe una función `send_cmd(cmd)` y cablea sus propios
botones. Los resultados de cada prueba aparecen en la consola inferior.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
                             QPushButton, QLabel, QSpinBox, QCheckBox)


class TestPanel(QDialog):
    def __init__(self, send_cmd, parent=None):
        super().__init__(parent)
        self.send_cmd = send_cmd  # callable: envía un comando al robot

        self.setWindowTitle("Panel de Test / Diagnóstico — T.A.I.L.S.")
        self.resize(540, 660)

        layout = QVBoxLayout(self)

        # --- GUÍA RÁPIDA ---
        guia = QLabel(
            "<b>Guía rápida</b><br>"
            "Probá el hardware de a una parte por vez.<br>"
            "• <b>LEDs:</b> ON/OFF para verificar cada indicador de la placa.<br>"
            "• <b>Motores:</b> elegí los pasos y movés cada eje con + / − "
            "(movimiento relativo, no necesita Home).<br>"
            "• <b>Garra:</b> abrir/cerrar el servo.<br>"
            "<i>Ojo:</i> requiere estar conectado y NO estar en Paro de Emergencia. "
            "Cada resultado se ve en la consola inferior."
        )
        guia.setWordWrap(True)
        guia.setStyleSheet("background-color:#20232a; color:#ddd; padding:8px; border-radius:6px;")
        layout.addWidget(guia)

        # --- LEDS ---
        grp_led = QGroupBox("LEDs (prender / apagar)")
        gl = QGridLayout(grp_led)
        leds = [("Home", "H"), ("Wait / Busy", "W"), ("Finish", "F"), ("LED Placa (PC13)", "P")]
        for row, (name, code) in enumerate(leds):
            gl.addWidget(QLabel(name), row, 0)
            b_on = QPushButton("ON")
            b_on.setStyleSheet("background-color:#2e7d32; color:white; font-weight:bold;")
            b_on.clicked.connect(lambda _=False, c=code: self.send_cmd(f":*L{c}1"))
            b_off = QPushButton("OFF")
            b_off.clicked.connect(lambda _=False, c=code: self.send_cmd(f":*L{c}0"))
            gl.addWidget(b_on, row, 1)
            gl.addWidget(b_off, row, 2)
        layout.addWidget(grp_led)

        # --- MOTORES ---
        grp_mot = QGroupBox("Motores (movimiento relativo independiente)")
        gm = QGridLayout(grp_mot)

        gm.addWidget(QLabel("Pasos por pulsación:"), 0, 0)
        self.spin_steps = QSpinBox()
        self.spin_steps.setRange(1, 9999)
        self.spin_steps.setValue(100)
        gm.addWidget(self.spin_steps, 0, 1, 1, 2)

        for row, axis in enumerate(["X", "Y", "Z"], start=1):
            gm.addWidget(QLabel(f"Eje {axis}"), row, 0)
            b_minus = QPushButton(f"{axis} −")
            b_minus.setMinimumHeight(40)
            b_minus.clicked.connect(lambda _=False, a=axis: self.jog(a, '-'))
            b_plus = QPushButton(f"{axis} +")
            b_plus.setMinimumHeight(40)
            b_plus.clicked.connect(lambda _=False, a=axis: self.jog(a, '+'))
            gm.addWidget(b_minus, row, 1)
            gm.addWidget(b_plus, row, 2)
        layout.addWidget(grp_mot)

        # --- GARRA + ENABLE ---
        grp_extra = QGroupBox("Garra y Torque")
        ge = QHBoxLayout(grp_extra)
        b_open = QPushButton("Garra Abrir")
        b_open.clicked.connect(lambda: self.send_cmd(":*GA"))
        b_close = QPushButton("Garra Cerrar")
        b_close.clicked.connect(lambda: self.send_cmd(":*GC"))
        self.chk_enable = QCheckBox("Torque motores (Enable)")
        self.chk_enable.setChecked(True)
        self.chk_enable.toggled.connect(lambda on: self.send_cmd(":-E1" if on else ":-E0"))
        ge.addWidget(b_open)
        ge.addWidget(b_close)
        ge.addWidget(self.chk_enable)
        layout.addWidget(grp_extra)

        layout.addStretch()
        nota = QLabel("<i>Los resultados de cada prueba aparecen en la consola inferior.</i>")
        nota.setWordWrap(True)
        layout.addWidget(nota)

    def jog(self, axis, sign):
        """Envía un movimiento relativo de prueba al eje indicado."""
        steps = self.spin_steps.value()
        self.send_cmd(f":*M{axis}{sign}{steps:03d}")
