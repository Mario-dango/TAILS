"""
WIDGETS AUXILIARES DE LA UI v2
--------------------------------
Piezas visuales reutilizables que no existían en la v1:

* SectionCard  : tarjeta con encabezado en versalitas (reemplaza al QGroupBox
                 con título flotante, que comía 20px de margen superior).
* ArmPreview   : vista superior polar del brazo, dibujada con QPainter.
* ZGauge       : barra vertical con la altura del eje Z.
* GripRange    : barra que muestra el recorrido entre ángulo cerrado y abierto.
* Kbd          : etiqueta pequeña tipo tecla, para los atajos de jogging.

Ninguna depende del controlador: son puramente visuales.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QSizePolicy
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient
import math

# Paleta compartida con style.css (única fuente de verdad para los QPainter)
C_CANVAS   = "#14171b"
C_PANEL    = "#191d21"
C_SUNKEN   = "#0d1013"
C_BORDER   = "#2b3138"
C_GRID     = "#262c32"
C_TEXT     = "#e6e9ec"
C_MUTED    = "#79838d"
C_FAINT    = "#4d565e"
C_ACCENT   = "#4fc0ff"
C_ACCENT_D = "#2a7fb8"
C_X        = "#e05c68"
C_Y        = "#5fbf7e"
C_Z        = "#4fa8e0"
C_OK       = "#4ec97a"
C_WARN     = "#f2b12c"
C_ERR      = "#e5484d"

# Recorrido real de cada articulación, en PASOS. El firmware trabaja siempre en
# pasos (`:#X<n>` y la telemetría `STATUS|X:<pasos>`), así que la interfaz no
# convierte a grados en ningún punto.
#
# Estos valores son la ÚNICA fuente de verdad de los rangos: los usan tanto el
# visualizador de este módulo como la validación de celdas de la tabla de rutina
# (view/tab_teaching.py). Si cambia el recorrido de un eje, se toca sólo acá.
RANGO_X = 580     # giro de la base
RANGO_Y = 130     # extensión del brazo
RANGO_Z = 60      # altura

# El home de X (posición 0) se dibuja a la DERECHA del visualizador. Poner en
# False para espejar el barrido si se invierte el montaje de la base.
X_HOME_A_LA_DERECHA = True

# Radio que ocupa el gripper con Y=0, como fracción del alcance máximo. No es 0
# para que el brazo siga viéndose como un segmento y no como un punto, pero es lo
# bastante chico para que "recogido" se lea como recogido.
RADIO_MINIMO = 0.10


def _norm(valor, maximo):
    """Normaliza a 0..1 saturando fuera de rango (evita dibujar fuera del widget)."""
    if maximo <= 0:
        return 0.0
    return max(0.0, min(1.0, float(valor) / float(maximo)))


class SectionCard(QFrame):
    """Tarjeta con encabezado. Usar .body para agregar contenido."""

    def __init__(self, title, right_widget=None, parent=None):
        super().__init__(parent)
        self.setObjectName("section_card")
        self.setStyleSheet(
            "QFrame#section_card{background:%s;border:1px solid %s;border-radius:10px;}"
            % (C_PANEL, C_BORDER)
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(11, 9, 11, 10)
        outer.setSpacing(7)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)
        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setProperty("role", "section")
        head.addWidget(self.lbl_title)
        head.addStretch()
        if right_widget is not None:
            head.addWidget(right_widget)
        self._head = head
        outer.addLayout(head)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(5)
        outer.addLayout(self.body)

    def add_header_widget(self, w, after_title=True):
        """Agrega un widget al encabezado (junto al título o al extremo derecho)."""
        self._head.insertWidget(1 if after_title else self._head.count(), w)
        return w


class Kbd(QLabel):
    """Etiqueta tipo tecla, ej. Kbd("←")."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(
            "background:#2b3037;border:1px solid #3a4048;border-radius:3px;"
            "color:%s;font-family:'IBM Plex Mono',Consolas,monospace;font-size:12px;"
            "font-weight:600;padding:1px 3px;" % C_MUTED
        )


class ArmPreview(QWidget):
    """
    Vista superior del brazo, en PASOS. X = giro de la base (0..RANGO_X),
    Y = extensión (0..RANGO_Y). set_position(x, y) redibuja.

    Es una representación PROPORCIONAL y orientada, no un modelo cinemático: no
    considera largos de eslabón ni relaciones de transmisión, así que no describe
    la pose física exacta de cada articulación.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_pasos = 0
        self.y_pasos = 0
        # El alto manda: el dibujo es un SEMIDISCO, así que con 86px de alto en
        # un rail de ~300px de ancho el barrido quedaba achatado contra el borde
        # inferior (reach_max = min(ancho*0.42, alto-34) -> lo limitaba el alto).
        # Con política Expanding en vertical la tarjeta le cede el espacio libre
        # del panel y el semidisco recupera su proporción.
        # El MÍNIMO se mantiene moderado (el rail tiene que seguir entrando
        # entero en 1280x940, con el botón de STOP a la vista); lo que cambia es
        # la política vertical: con Expanding el visor se queda con el espacio
        # libre del panel en cuanto la ventana da de sí.
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_position(self, x_pasos, y_pasos):
        self.x_pasos, self.y_pasos = x_pasos, y_pasos
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()

        # fondo hundido
        p.setPen(QPen(QColor(C_GRID), 1))
        p.setBrush(QBrush(QColor(C_SUNKEN)))
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)

        cx = r.width() / 2.0
        cy = r.height() - 18.0
        reach_max = min(r.width() * 0.42, r.height() - 34)

        # Arcos concéntricos, rotulados con el valor de Y que representan: sin la
        # escala impresa no había forma de leer a qué distancia real está el gripper.
        f_esc = p.font(); f_esc.setFamily("IBM Plex Mono"); f_esc.setPointSize(6)
        for k in (0.25, 0.5, 0.75, 1.0):
            rr = reach_max * (RADIO_MINIMO + (1.0 - RADIO_MINIMO) * k)
            p.setPen(QPen(QColor(255, 255, 255, 16), 1))
            p.drawArc(QRectF(cx - rr, cy - rr, rr * 2, rr * 2), 0, 180 * 16)
            p.setFont(f_esc)
            p.setPen(QColor(C_FAINT))
            # Rotulados a la DERECHA del eje vertical, como las marcas de una
            # regla. Centrados sobre el vértice del arco se montaban encima del
            # título "VISTA SUP. · X/Y", sobre todo ahora que el visor es más alto.
            p.drawText(QRectF(cx + 5, cy - rr - 6, 40, 11),
                       Qt.AlignLeft | Qt.AlignVCenter, "%d" % round(RANGO_Y * k))

        # ejes de referencia
        p.setPen(QPen(QColor(C_GRID), 1))
        p.drawLine(int(cx), int(cy), int(cx), int(cy - reach_max))
        p.drawLine(12, int(cy), r.width() - 12, int(cy))

        # Brazo: la base barre 180° a lo largo de su recorrido en pasos. Con
        # X_HOME_A_LA_DERECHA, la posición 0 queda a 0° (derecha) y el tope a 180°
        # (izquierda); con el flag en False el barrido va al revés.
        avance_x = _norm(self.x_pasos, RANGO_X)
        if not X_HOME_A_LA_DERECHA:
            avance_x = 1.0 - avance_x
        ang = math.radians(180.0 * avance_x)

        # La extensión es PROPORCIONAL a Y en todo el recorrido: con Y=0 el gripper
        # queda sobre el origen y con Y=RANGO_Y en el arco exterior. Antes la
        # fórmula era (0.55 + 0.45·Y), o sea que en Y=0 ya arrancaba a mitad de
        # camino y la distancia dibujada no se correspondía con la real.
        avance_y = _norm(self.y_pasos, RANGO_Y)
        reach = reach_max * (RADIO_MINIMO + (1.0 - RADIO_MINIMO) * avance_y)
        tip = QPointF(cx + reach * math.cos(ang), cy - reach * math.sin(ang))

        grad = QLinearGradient(QPointF(cx, cy), tip)
        grad.setColorAt(0.0, QColor(C_ACCENT_D))
        grad.setColorAt(1.0, QColor("#a8e4ff"))
        p.setPen(QPen(QBrush(grad), 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(cx, cy), tip)

        # punta
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(168, 228, 255, 70))
        p.drawEllipse(tip, 8, 8)
        p.setBrush(QColor("#a8e4ff"))
        p.drawEllipse(tip, 4.5, 4.5)

        # base
        p.setPen(QPen(QColor("#4a5560"), 2))
        p.setBrush(QColor("#1c2126"))
        p.drawEllipse(QPointF(cx, cy), 5.5, 5.5)

        # rótulos
        f = p.font(); f.setFamily("IBM Plex Mono"); f.setPointSize(10); p.setFont(f)
        p.setPen(QColor(C_FAINT))
        p.drawText(9, 17, "VISTA SUP. · X/Y")
        # Alineado a la derecha del widget en vez de a un offset fijo de 150px:
        # con posiciones de tres cifras el rótulo se salía del recuadro.
        p.setPen(QColor(C_ACCENT))
        p.drawText(QRectF(0, r.height() - 19, r.width() - 9, 12),
                   Qt.AlignRight | Qt.AlignVCenter,
                   "X %d/%d · Y %d/%d" % (self.x_pasos, RANGO_X,
                                          self.y_pasos, RANGO_Y))
        p.end()


class ZGauge(QWidget):
    """Barra vertical con el valor del eje Z, en pasos (0..RANGO_Z)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        # Acompaña el alto de ArmPreview para que los dos visores queden parejos.
        self.setFixedWidth(64)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def set_value(self, v):
        self.value = v
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        p.setPen(QPen(QColor(C_GRID), 1))
        p.setBrush(QBrush(QColor(C_SUNKEN)))
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)

        f = p.font(); f.setFamily("IBM Plex Mono"); f.setPointSize(10); p.setFont(f)
        p.setPen(QColor(C_FAINT))
        p.drawText(QRectF(0, 5, r.width(), 12), Qt.AlignCenter, "Z")

        track = QRectF(r.width() / 2 - 5.5, 22, 11, r.height() - 44)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#171b1f"))
        p.drawRoundedRect(track, 6, 6)

        pct = _norm(self.value, RANGO_Z)
        h = track.height() * pct
        if h > 1:
            fill = QRectF(track.x(), track.bottom() - h, track.width(), h)
            grad = QLinearGradient(fill.topLeft(), fill.bottomLeft())
            grad.setColorAt(0.0, QColor(C_Z))
            grad.setColorAt(1.0, QColor(C_ACCENT_D))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(fill, 6, 6)

        p.setPen(QColor(C_Z))
        p.drawText(QRectF(0, r.height() - 17, r.width(), 12), Qt.AlignCenter, str(self.value))
        p.end()


class GripRange(QWidget):
    """Recorrido de la garra entre el ángulo cerrado y el abierto (0..180)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lo, self.hi = 0, 90
        self.setFixedHeight(76)

    def set_range(self, lo, hi):
        self.lo, self.hi = min(lo, hi), max(lo, hi)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        p.setPen(QPen(QColor(C_GRID), 1))
        p.setBrush(QBrush(QColor(C_SUNKEN)))
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)

        track = QRectF(12, 20, r.width() - 24, 12)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#171b1f"))
        p.drawRoundedRect(track, 6, 6)

        x0 = track.x() + track.width() * (self.lo / 180.0)
        x1 = track.x() + track.width() * (self.hi / 180.0)
        if x1 - x0 > 1:
            fill = QRectF(x0, track.y(), x1 - x0, track.height())
            grad = QLinearGradient(fill.topLeft(), fill.topRight())
            grad.setColorAt(0.0, QColor(C_ACCENT_D))
            grad.setColorAt(1.0, QColor(C_ACCENT))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(fill, 6, 6)

        f = p.font(); f.setFamily("IBM Plex Mono"); f.setPointSize(10); p.setFont(f)
        p.setPen(QColor(C_MUTED))
        p.drawText(QRectF(12, 38, 40, 12), Qt.AlignLeft, "0°")
        p.drawText(QRectF(r.width() - 52, 38, 40, 12), Qt.AlignRight, "180°")
        p.setPen(QColor(C_ACCENT))
        p.drawText(QRectF(0, 38, r.width(), 12), Qt.AlignCenter, "%d° → %d°" % (self.lo, self.hi))
        p.end()
