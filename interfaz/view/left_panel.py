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
        # El número se dibuja con la fuente mono de role="value". Con el 26px
        # que tenía la hoja de estilos las cifras no entraban en la caja y se
        # cortaban por arriba y por abajo (peor todavía con la escala de
        # pantalla en 125 %). La fuente bajó a 20px en style.css y la caja subió
        # de 38 a 40: el número entra con aire y el rail sigue entrando entero.
        self.setFixedHeight(40)
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
    # 30 y no 28: style.css fija el LED en 30x30 (min/max-width y -height). Con
    # 28 el widget quedaba más chico que su propio estilo y la letra del eje se
    # dibujaba contra el borde.
    l.setFixedSize(30, 30)
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

    # Alto del botón de parada: el mínimo de siempre y el tope al que puede
    # crecer cuando el rail tiene espacio de sobra (ver _repartir_alto_libre).
    ESTOP_ALTO_MINIMO = 68
    ESTOP_ALTO_MAXIMO = 176

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
        # SIN stretch, a propósito. Los visores son un semidisco y una barra:
        # crecen hasta ArmPreview.ALTO_MAXIMO y de ahí no pasan (el radio lo
        # limita el ancho del rail, que es fijo). Con stretch, al cerrar la
        # terminal el dock le devolvía ~200px de alto al panel, la tarjeta se
        # estiraba y esos píxeles quedaban como un hueco vacío DENTRO del
        # recuadro. Ahora el sobrante va al addStretch() del final del rail y los
        # visores conservan su proporción; su sizeHint es el alto máximo, así que
        # siguen aprovechando todo el espacio que el rail sí puede darles.
        card_pos.body.addLayout(preview_row)

        root.addWidget(card_pos)

        # ---------- B. FINALES + SISTEMA (una sola fila) ----------
        row = QHBoxLayout()
        row.setSpacing(9)

        card_sens = SectionCard("Finales")
        card_sens.setFixedWidth(116)
        card_sens.setMaximumHeight(198)
        self.led_x, self.led_y, self.led_z = _led("X"), _led("Y"), _led("Z")
        for i, (letter, led) in enumerate((("X", self.led_x), ("Y", self.led_y),
                                           ("Z", self.led_z))):
            if i:
                # Separadores elásticos: cuando el rail tiene alto de sobra (la
                # terminal cerrada le devuelve ~200px) las filas se reparten el
                # espacio en vez de amontonarse arriba y dejar la tarjeta a medio
                # llenar. Con la ventana justa se colapsan a cero.
                card_sens.body.addStretch()
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
        card_sys.setMaximumHeight(198)
        self.lbl_status_home = QLabel("HOME")
        self.lbl_status_wait = QLabel("WAIT / BUSY")
        self.lbl_status_finish = QLabel("FINISH")
        for i, b in enumerate((self.lbl_status_home, self.lbl_status_wait,
                               self.lbl_status_finish)):
            if i:
                card_sys.body.addStretch()      # ver nota en la tarjeta 'Finales'
            b.setProperty("class", "status_badge_off")
            # 30 con 6px de padding en style.css (antes: 28 con 8px). El badge
            # lleva 13px de texto + padding + borde, y en los 28px de antes no
            # entraba: "WAIT / BUSY" se veía recortado por arriba.
            b.setFixedHeight(30)
            card_sys.body.addWidget(b)

        row.addWidget(card_sens)
        row.addWidget(card_sys, 1)
        # Stretch 1: esta fila es la que se queda con el alto libre del rail
        # (acotada por el máximo de las tarjetas). El addStretch() final recoge
        # lo que sobre en pantallas muy altas.
        root.addLayout(row, 1)

        root.addStretch()

        # ---------- C. PARADA DE EMERGENCIA (fuera del scroll) ----------
        self.btn_estop = QPushButton("  STOP EMERGENCIA")
        self.btn_estop.setProperty("class", "stop_button")
        self.btn_estop.setMinimumHeight(self.ESTOP_ALTO_MINIMO)
        self.btn_estop.setToolTip("Corta todo movimiento inmediatamente. Atajo: Esc")
        marco.addWidget(self.btn_estop)

        self.btn_rearm = QPushButton("Rearmar (:-R)")
        self.btn_rearm.setMinimumHeight(42)
        self.btn_rearm.setToolTip("Libera el bloqueo de parada de emergencia (envía :-R).")
        marco.addWidget(self.btn_rearm)

        # El área desplazable reserva el alto mínimo real de sus tarjetas. Sin
        # esta reserva el STOP —que también reclama espacio— le comía alto al
        # scroll y con la terminal abierta reaparecía la barra de
        # desplazamiento, justo lo que el rail tiene que evitar. Con la reserva,
        # el botón se queda sólo con lo que SOBRA. No se reserva el sizeHint
        # (que pide los visores en su alto máximo) porque en una ventana al
        # mínimo, y con la terminal abierta, no hay tanto alto: los visores se
        # achican y el rail entra igual.
        self.scroll.setMinimumHeight(tarjetas.minimumSizeHint().height())

    # --- REPARTO DEL ALTO LIBRE ---
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._repartir_alto_libre()

    def showEvent(self, event):
        # Qt no manda resizeEvent mientras el widget está oculto: sin esto, el
        # reparto recién se haría en el primer redimensionado de la ventana.
        super().showEvent(event)
        self._repartir_alto_libre()

    def _repartir_alto_libre(self):
        """Le da al STOP el alto que sobra después de las tarjetas.

        Los visores tienen tope (el semidisco no crece más allá de lo que da el
        ancho fijo del rail), así que al cerrar la terminal —que le devuelve
        ~200px de alto al panel— sobraba un bloque de fondo vacío entre las
        tarjetas y el botón. Ese sobrante se lo lleva ahora la parada de
        emergencia, que es el control al que conviene llegar rápido y sin
        apuntar. Si no sobra nada, el botón vuelve a su alto de siempre y el
        espacio queda para las tarjetas.

        Se calcula a mano en vez de con un stretch porque el reparto entre el
        área desplazable y el botón tiene una prioridad clara: primero las
        tarjetas, el resto para el STOP. Con los dos compitiendo por stretch,
        Qt le daba alto al botón mientras el rail mostraba barra de scroll.
        """
        tarjetas = self.scroll.widget()
        if tarjetas is None:
            return
        # Del botón Rearmar se toma su alto PREFERIDO y no el actual: la cuenta
        # también corre antes del primer layout, cuando height() todavía informa
        # el tamaño por defecto del widget y no el que va a tener.
        alto_rearm = max(self.btn_rearm.minimumHeight(),
                         self.btn_rearm.sizeHint().height())
        # Los tres widgets del marco (scroll, STOP y Rearmar) dejan dos huecos
        # de 6px entre ellos.
        fijos = (tarjetas.sizeHint().height() + alto_rearm
                 + self.ESTOP_ALTO_MINIMO + 2 * 6)
        sobra = self.height() - fijos
        alto = self.ESTOP_ALTO_MINIMO + max(
            0, min(self.ESTOP_ALTO_MAXIMO - self.ESTOP_ALTO_MINIMO, sobra))
        # Se compara contra el alto FIJADO y no contra height(): el segundo
        # todavía no refleja el setFixedHeight anterior (el layout se aplica
        # después) y el reparto se recalcularía en cada evento.
        if self.btn_estop.maximumHeight() != alto:
            self.btn_estop.setFixedHeight(alto)

    # --- helper opcional para el controlador: refresca las visualizaciones ---
    def update_preview(self, x, y, z):
        self.arm_preview.set_position(int(x), int(y))
        self.z_gauge.set_value(int(z))
