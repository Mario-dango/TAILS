"""
PANEL IZQUIERDO v2 (Estado del robot)
--------------------------------------
Reorganización respecto de la v1:
 · "Conexión" se mudó al app bar (view/top_bar.py) — ya no vive acá.
 · Los QLCDNumber de 7 segmentos (que se veían vacíos/ilegibles en la captura
   original) se reemplazan por AxisReadout: número monoespaciado grande con
   barra de color por eje. Mantiene .display(valor) para no romper el
   controlador existente.
 · "Finales de carrera" y "Sistema" comparten una fila: se elimina el hueco
   vertical muerto que había entre los grupos.
 · Se agrega la vista superior del brazo + gauge de Z (ArmPreview / ZGauge).
 · El STOP de emergencia queda anclado abajo, siempre visible.

Expone (compatibilidad con el controlador):
  lcd_x, lcd_y, lcd_z .............. .display(v)
  led_x, led_y, led_z .............. QLabel (objectName sensor_led_on/off)
  lbl_status_home / _wait / _finish  QLabel con property "class"
  btn_estop, btn_rearm
Nuevo: arm_preview, z_gauge
"""

from PyQt5.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt
from view.ui_widgets import (SectionCard, ArmPreview, ZGauge,
                             C_SUNKEN, C_X, C_Y, C_Z)


class AxisReadout(QFrame):
    """Lectura de un eje. Drop-in de QLCDNumber: expone .display(valor)."""

    def __init__(self, axis, color):
        super().__init__()
        self.setFixedHeight(38)
        # OJO: el selector va acotado con #axis_readout. Un "QFrame{...}" pelado
        # alcanza también a los QLabel hijos (QLabel hereda de QFrame), y cada uno
        # dibujaba su propio marco redondeado: eran los "corchetes" de colores.
        self.setObjectName("axis_readout")
        self.setStyleSheet(
            "QFrame#axis_readout{background:%s;border:1px solid #262c32;"
            "border-left:3px solid %s;border-radius:6px;}" % (C_SUNKEN, color)
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(9)

        lbl = QLabel(axis)
        lbl.setFixedWidth(17)
        lbl.setStyleSheet("color:%s;font-weight:700;font-size:14px;" % color)

        self.value = QLabel("0")
        self.value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value.setProperty("role", "value")

        unit = QLabel("pasos")
        unit.setStyleSheet("color:#5e6871;font-family:'IBM Plex Mono';font-size:12px;")

        lay.addWidget(lbl)
        lay.addWidget(self.value, 1)
        lay.addWidget(unit)

    def display(self, v):
        # La posición siempre es un entero de pasos: nada de decimales ni grados.
        try:
            self.value.setText("%d" % int(float(v)))
        except (TypeError, ValueError):
            self.value.setText(str(v))

    def setDigitCount(self, *_):        # no-op: compatibilidad con QLCDNumber
        pass

    def setSegmentStyle(self, *_):
        pass


def _led(letter):
    l = QLabel(letter)
    l.setAlignment(Qt.AlignCenter)
    l.setFixedSize(28, 28)
    l.setObjectName("sensor_led_off")
    return l


class LeftPanel(QWidget):
    """Rail de estado. El STOP de emergencia va FUERA del área desplazable.

    Antes el panel entero vivía dentro de un QScrollArea de view.py y la ventana
    tenía un alto mínimo calculado para que la barra no llegara a aparecer. Ese
    presupuesto es frágil: cualquier cosa que crezca (los visores, la terminal
    que ahora es un dock con su barra de título) empuja al STOP fuera de la
    pantalla, que es justo lo que no puede pasar. Ahora scrollean las tarjetas
    informativas y el STOP queda anclado abajo pase lo que pase.
    """

    def __init__(self):
        super().__init__()
        self.setFixedWidth(336)

        marco = QVBoxLayout(self)
        marco.setContentsMargins(0, 0, 0, 0)
        marco.setSpacing(6)

        tarjetas = QWidget()
        root = QVBoxLayout(tarjetas)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        self.scroll = QScrollArea()
        self.scroll.setWidget(tarjetas)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        marco.addWidget(self.scroll, 1)

        # ---------- A. POSICIÓN + VISTA ----------
        unit = QLabel("PASOS")
        unit.setStyleSheet("color:#5e6871;font-family:'IBM Plex Mono';font-size:12px;")
        card_pos = SectionCard("Posición actual", right_widget=unit)

        self.lcd_x = AxisReadout("X", C_X)
        self.lcd_y = AxisReadout("Y", C_Y)
        self.lcd_z = AxisReadout("Z", C_Z)
        for w in (self.lcd_x, self.lcd_y, self.lcd_z):
            card_pos.body.addWidget(w)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(9)
        self.arm_preview = ArmPreview()
        self.z_gauge = ZGauge()
        preview_row.addWidget(self.arm_preview, 1)
        preview_row.addWidget(self.z_gauge)
        card_pos.body.addSpacing(4)
        # Stretch 1: sin él la fila de visores recibe sólo su alto mínimo y todo
        # el espacio libre del rail se lo lleva el addStretch() de más abajo.
        card_pos.body.addLayout(preview_row, 1)

        # Stretch 1: la tarjeta de posición se queda con el espacio sobrante del
        # rail (y se lo pasa a los visores). Sin esto se lo llevaba entero el
        # addStretch() de más abajo y los visores quedaban en su alto mínimo.
        root.addWidget(card_pos, 1)

        # ---------- B. FINALES + SISTEMA (una sola fila) ----------
        row = QHBoxLayout()
        row.setSpacing(9)

        card_sens = SectionCard("Finales")
        card_sens.setFixedWidth(116)
        self.led_x, self.led_y, self.led_z = _led("X"), _led("Y"), _led("Z")
        for letter, led in (("X", self.led_x), ("Y", self.led_y), ("Z", self.led_z)):
            line = QHBoxLayout()
            line.setSpacing(8)
            line.addWidget(led)
            tag = QLabel(letter)
            tag.setStyleSheet(
                "color:#79838d;font-family:'IBM Plex Mono';font-size:14px;")
            line.addWidget(tag)
            line.addStretch()
            card_sens.body.addLayout(line)

        card_sys = SectionCard("Sistema")
        self.lbl_status_home = QLabel("HOME")
        self.lbl_status_wait = QLabel("WAIT / BUSY")
        self.lbl_status_finish = QLabel("FINISH")
        for b in (self.lbl_status_home, self.lbl_status_wait, self.lbl_status_finish):
            b.setProperty("class", "status_badge_off")
            b.setFixedHeight(28)
            card_sys.body.addWidget(b)

        row.addWidget(card_sens)
        row.addWidget(card_sys, 1)
        root.addLayout(row)

        root.addStretch()

        # ---------- C. PARADA DE EMERGENCIA (fuera del scroll) ----------
        self.btn_estop = QPushButton("  STOP EMERGENCIA")
        self.btn_estop.setProperty("class", "stop_button")
        self.btn_estop.setMinimumHeight(68)
        self.btn_estop.setToolTip("Corta todo movimiento inmediatamente. Atajo: Esc")
        marco.addWidget(self.btn_estop)

        self.btn_rearm = QPushButton("Rearmar (:-R)")
        self.btn_rearm.setMinimumHeight(42)
        self.btn_rearm.setToolTip("Libera el bloqueo de parada de emergencia (envía :-R).")
        marco.addWidget(self.btn_rearm)

    # --- helper opcional para el controlador: refresca las visualizaciones ---
    def update_preview(self, x, y, z):
        self.arm_preview.set_position(int(x), int(y))
        self.z_gauge.set_value(int(z))
