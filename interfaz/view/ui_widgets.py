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
from PyQt5.QtCore import Qt, QRectF, QPointF, QSize
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


def _ancho_texto(fm, texto):
    """Ancho en px de un texto. QFontMetrics.width() quedó obsoleta en Qt 5.11."""
    medir = getattr(fm, "horizontalAdvance", None)
    return medir(texto) if medir is not None else fm.width(texto)


def _fuente_que_entra(p, texto, ancho, minimo=6):
    """Achica la fuente del QPainter hasta que `texto` entre en `ancho`.

    Los rótulos de los visores se dibujan a mano: si el texto es más ancho que el
    recuadro, Qt lo recorta sin avisar (era lo que pasaba con las coordenadas
    cuando los dos ejes marcaban tres cifras). Devuelve la métrica final.
    """
    f = p.font()
    while _ancho_texto(p.fontMetrics(), texto) > ancho and f.pointSize() > minimo:
        f.setPointSize(f.pointSize() - 1)
        p.setFont(f)
    return p.fontMetrics()


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

    # Alto máximo del visor. El dibujo es un SEMIDISCO y su radio no puede pasar
    # de la mitad del ancho; el rail tiene ancho FIJO, así que a partir de cierto
    # alto el semidisco ya no crece y todo lo que sobra es hueco muerto dentro del
    # recuadro. Eso era lo que se veía al cerrar la terminal (el dock le devuelve
    # ~200px de alto al panel): los dos visores se estiraban y el dibujo quedaba
    # flotando en un marco enorme. Con el tope, el sobrante queda como espacio
    # libre del rail y los visores conservan su proporción.
    ALTO_MAXIMO = 188
    # El MÍNIMO es chico a propósito: con la terminal abierta el rail entero
    # tiene que entrar en una ventana de 940px de alto sin barra de scroll. El
    # sizeHint, en cambio, es el máximo: cuando hay lugar, el visor lo usa.
    ALTO_MINIMO = 84

    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_pasos = 0
        self.y_pasos = 0
        self.setMinimumHeight(self.ALTO_MINIMO)
        self.setMaximumHeight(self.ALTO_MAXIMO)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def sizeHint(self):
        # QWidget no define sizeHint: sin esto el layout lo mide por su mínimo y
        # el visor nunca llegaba a usar el alto que tiene disponible.
        return QSize(220, self.ALTO_MAXIMO)

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

        # --- BANDAS DE TEXTO ---
        # El alto de cada rótulo sale de la MÉTRICA de la fuente, no de un 12
        # fijo como antes: con cualquier escala de pantalla mayor al 100 % el
        # texto de coordenadas no entraba en esos 12px y Qt lo recortaba por
        # abajo (se veían las cifras cortadas por la mitad).
        f_rot = p.font()
        f_rot.setFamily("IBM Plex Mono")
        f_rot.setPointSize(9)
        p.setFont(f_rot)
        alto_rotulo = p.fontMetrics().height()

        banda_sup = alto_rotulo + 12                 # debajo del titulo
        banda_inf = r.height() - alto_rotulo - 8     # encima de las coordenadas

        cx = r.width() / 2.0
        # El radio nunca pasa de la mitad del ancho ni del alto libre. Cuando
        # sobra alto, el semidisco se CENTRA en la banda en vez de quedar pegado
        # abajo dejando un hueco muerto arriba.
        reach_max = max(24.0, min(cx - 14.0, banda_inf - banda_sup))
        cy = (banda_sup + banda_inf + reach_max) / 2.0

        # Arcos concéntricos, rotulados con el valor de Y que representan: sin la
        # escala impresa no había forma de leer a que distancia real está el gripper.
        f_esc = p.font()
        f_esc.setFamily("IBM Plex Mono")
        f_esc.setPointSize(7)
        p.setFont(f_esc)
        alto_esc = p.fontMetrics().height()
        ultimo_y = None
        for k in (1.0, 0.75, 0.5, 0.25):
            rr = reach_max * (RADIO_MINIMO + (1.0 - RADIO_MINIMO) * k)
            p.setPen(QPen(QColor(255, 255, 255, 16), 1))
            p.drawArc(QRectF(cx - rr, cy - rr, rr * 2, rr * 2), 0, 180 * 16)

            # El rótulo de un arco se saltea si se montaría sobre el anterior.
            # Con el visor chico (la terminal abierta le deja poco alto al rail)
            # los cuatro arcos caen a pocos píxeles uno de otro y las cifras se
            # pisaban entre sí. Se recorren de afuera hacia adentro para que,
            # cuando hay que descartar, sobrevivan las marcas más separadas.
            y = cy - rr
            if ultimo_y is not None and abs(ultimo_y - y) < alto_esc + 1:
                continue
            ultimo_y = y
            p.setFont(f_esc)
            p.setPen(QColor(C_FAINT))
            # Rotulados a la DERECHA del eje vertical, como las marcas de una
            # regla. Centrados sobre el vértice del arco se montaban encima del
            # título "VISTA SUP.".
            p.drawText(QRectF(cx + 5, y - alto_esc / 2.0, 44, alto_esc),
                       Qt.AlignLeft | Qt.AlignVCenter, "%d" % round(RANGO_Y * k))

        # ejes de referencia
        p.setPen(QPen(QColor(C_GRID), 1))
        p.drawLine(int(cx), int(cy), int(cx), int(cy - reach_max))
        p.drawLine(12, int(cy), r.width() - 12, int(cy))

        # Brazo: la base barre 180 grados a lo largo de su recorrido en pasos. Con
        # X_HOME_A_LA_DERECHA, la posición 0 queda a 0 grados (derecha) y el tope a
        # 180 (izquierda); con el flag en False el barrido va al revés.
        avance_x = _norm(self.x_pasos, RANGO_X)
        if not X_HOME_A_LA_DERECHA:
            avance_x = 1.0 - avance_x
        ang = math.radians(180.0 * avance_x)

        # La extensión es PROPORCIONAL a Y en todo el recorrido: con Y=0 el gripper
        # queda sobre el origen y con Y=RANGO_Y en el arco exterior.
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

        # --- RÓTULOS ---
        p.setFont(f_rot)
        p.setPen(QColor(C_FAINT))
        p.drawText(QRectF(9, 4, r.width() - 18, alto_rotulo + 4),
                   Qt.AlignLeft | Qt.AlignVCenter, "VISTA SUP. \u00b7 X/Y")

        # Coordenadas: el ancho útil es el del widget menos los márgenes, y la
        # fuente se achica sola si el texto no entra (posiciones de tres cifras en
        # los dos ejes). Antes se dibujaba con la fuente fija en un rectángulo de
        # 12px de alto: se cortaba arriba y abajo.
        texto = "X %d/%d \u00b7 Y %d/%d" % (self.x_pasos, RANGO_X,
                                            self.y_pasos, RANGO_Y)
        ancho_util = r.width() - 18
        fm = _fuente_que_entra(p, texto, ancho_util)
        p.setPen(QColor(C_ACCENT))
        p.drawText(QRectF(9, r.height() - fm.height() - 5, ancho_util, fm.height()),
                   Qt.AlignRight | Qt.AlignVCenter, texto)
        p.end()


class ZGauge(QWidget):
    """Barra vertical con el valor del eje Z, en pasos (0..RANGO_Z)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        # Acompaña el alto de ArmPreview para que los dos visores queden parejos
        # (mismo mínimo y mismo tope: ver la nota de ArmPreview.ALTO_MAXIMO).
        self.setFixedWidth(64)
        self.setMinimumHeight(ArmPreview.ALTO_MINIMO)
        self.setMaximumHeight(ArmPreview.ALTO_MAXIMO)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def sizeHint(self):
        return QSize(64, ArmPreview.ALTO_MAXIMO)

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

        # Igual que en ArmPreview: las bandas de texto salen de la métrica de la
        # fuente. El valor de Z no entraba en los 12px fijos de antes.
        f = p.font()
        f.setFamily("IBM Plex Mono")
        f.setPointSize(9)
        p.setFont(f)
        alto_rotulo = p.fontMetrics().height()

        p.setPen(QColor(C_FAINT))
        p.drawText(QRectF(0, 4, r.width(), alto_rotulo), Qt.AlignCenter, "Z")

        tope = alto_rotulo + 12
        piso = r.height() - alto_rotulo - 8
        track = QRectF(r.width() / 2 - 5.5, tope, 11, max(10.0, piso - tope))
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

        texto = "%d/%d" % (self.value, RANGO_Z)
        fm = _fuente_que_entra(p, texto, r.width() - 8)
        p.setPen(QColor(C_Z))
        p.drawText(QRectF(4, r.height() - fm.height() - 5, r.width() - 8, fm.height()),
                   Qt.AlignCenter, texto)
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
