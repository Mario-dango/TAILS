"""
PESTAÑA APRENDIZAJE v2
-----------------------
Cambios respecto de la v1:
 · La cruz de jogging deja de compartir grilla con la columna Z (antes el
   separador "   |   " era una QLabel de texto); ahora son dos bloques con un
   divisor real, y los botones respiran (gap de 6px, alto 64px).
 · Incremento (1/10/50 pasos) pasa de tres radios sueltos a un segmented control
   dentro del encabezado de la tarjeta: una fila menos de alto.
 · Velocidad muestra el valor en grande y con rótulos de extremos.
 · La tabla de puntos gana columnas "#", "NOMBRE" y "ESPERA s", filas
   alternadas, y validación por celda (PointDelegate) contra el recorrido real
   de cada eje. "ESPERA s" es la pausa (0-60 s) que el robot mantiene al
   terminar ese paso antes de que la interfaz mande el siguiente; viaja al JSON
   en la clave "t" y el gestor de ejecución la suma a su intervalo base.
 · Atajos de teclado visibles sobre cada botón (Kbd).

Expone los mismos nombres que la v1 + step_group.
"""

from PyQt5.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QToolButton, QLabel, QSlider, QRadioButton,
                             QButtonGroup, QTableWidget, QHeaderView, QAbstractItemView,
                             QStyledItemDelegate, QSpinBox, QDoubleSpinBox,
                             QComboBox, QLineEdit)
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtCore import Qt
from view.ui_widgets import SectionCard, Kbd, C_BORDER, RANGO_X, RANGO_Y, RANGO_Z

# Columnas de table_points. Mismo orden que los COL_* de
# controller/learning_manager.py — si cambia acá, hay que cambiarlo allá
# (tests/ui/test_view_facade.py verifica que coincidan).
COL_NUM, COL_NAME, COL_X, COL_Y, COL_Z, COL_G, COL_V, COL_T = range(8)

# Rango admitido por celda. Los de los ejes salen de ui_widgets, que es la única
# fuente de verdad del recorrido real del robot.
RANGOS_CELDA = {
    COL_X: ("eje X", 0, RANGO_X),
    COL_Y: ("eje Y", 0, RANGO_Y),
    COL_Z: ("eje Z", 0, RANGO_Z),
    COL_V: ("la velocidad", 10, 100),
}

# Columnas con decimales. La espera es el tiempo que el robot se queda quieto
# DESPUÉS de completar el paso, antes de que la interfaz mande el siguiente:
# sirve para dejar asentar la pieza, esperar a que la garra termine de cerrar o
# darle tiempo al operador a sacar la mano. Se guarda en segundos (clave "t" del
# JSON) porque es la unidad en la que piensa quien opera el brazo.
ESPERA_MAXIMA_S = 60.0
ESPERA_DECIMALES = 1

RANGOS_DECIMALES = {
    COL_T: ("la espera", 0.0, ESPERA_MAXIMA_S),
}


class PointDelegate(QStyledItemDelegate):
    """Editores por columna para la tabla de rutina.

    Evita que se puedan escribir letras o valores fuera del recorrido físico:
    los ejes y la velocidad se editan con QSpinBox acotado y la garra con un
    desplegable A/C. El nombre queda como texto libre.
    """

    def createEditor(self, parent, option, index):
        col = index.column()
        if col in RANGOS_DECIMALES:
            _, minimo, maximo = RANGOS_DECIMALES[col]
            sb = QDoubleSpinBox(parent)
            sb.setDecimals(ESPERA_DECIMALES)
            sb.setRange(minimo, maximo)
            sb.setSingleStep(0.5)
            sb.setSuffix(" s")
            return sb
        if col in RANGOS_CELDA:
            _, minimo, maximo = RANGOS_CELDA[col]
            sb = QSpinBox(parent)
            sb.setRange(minimo, maximo)
            sb.setSuffix(" %" if col == COL_V else " pasos")
            return sb
        if col == COL_G:
            cb = QComboBox(parent)
            cb.addItem("A", "A")
            cb.addItem("C", "C")
            return cb
        if col == COL_NAME:
            le = QLineEdit(parent)
            le.setMaxLength(40)
            le.setPlaceholderText("opcional — ej. Tomar pieza")
            return le
        return None            # la columna "#" no se edita

    def setEditorData(self, editor, index):
        texto = (index.data() or "").strip()
        if isinstance(editor, QDoubleSpinBox):
            try:
                editor.setValue(float(texto.replace(",", ".")))
            except ValueError:
                editor.setValue(editor.minimum())
        elif isinstance(editor, QSpinBox):
            try:
                editor.setValue(int(texto))
            except ValueError:
                editor.setValue(editor.minimum())
        elif isinstance(editor, QComboBox):
            i = editor.findData("C" if texto.upper().startswith("C") else "A")
            editor.setCurrentIndex(max(0, i))
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QDoubleSpinBox):
            editor.interpretText()
            model.setData(index, "%.*f" % (ESPERA_DECIMALES, editor.value()),
                          Qt.EditRole)
        elif isinstance(editor, QSpinBox):
            editor.interpretText()
            model.setData(index, str(editor.value()), Qt.EditRole)
        elif isinstance(editor, QComboBox):
            model.setData(index, editor.currentData(), Qt.EditRole)
        else:
            super().setModelData(editor, model, index)


def _jog(label, tooltip, variant="jog"):
    """Botón de jogging: icono ARRIBA y etiqueta abajo.

    Es un QToolButton y no un QPushButton por una razón concreta: QPushButton
    sólo sabe dibujar el icono AL LADO del texto. El estilo pedía "icono arriba,
    etiqueta abajo", pero lo que se veía era un icono de 41px peleando el ancho
    con el rótulo dentro de un botón de 100px — recortados los dos. QToolButton
    sí tiene ToolButtonTextUnderIcon.

    Conserva clicked/click()/setIcon/setIconSize, así que el controlador, los
    atajos de teclado y view.set_btn_icon() lo usan sin cambio alguno.
    """
    b = QToolButton()
    b.setText(label)
    b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    b.setProperty("variant", variant)
    b.setMinimumHeight(88)
    b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    b.setToolTip(tooltip)
    return b


def _shortcut(btn, key):
    """Superpone la etiqueta de atajo en la esquina SUPERIOR DERECHA del botón.

    Antes iba en (4, 4) y quedaba justo encima del icono, que ahora se dibuja
    centrado arriba. Se reposiciona en cada resize porque el ancho del botón lo
    decide el layout.
    """
    k = Kbd(key, btn)
    k.adjustSize()

    def reubicar(_=None, b=btn, chip=k):
        chip.move(max(2, b.width() - chip.width() - 4), 3)
        chip.raise_()

    reubicar()
    btn.resizeEvent = _con_reubicacion(btn.resizeEvent, reubicar)
    return k


def _con_reubicacion(original, reubicar):
    """Envuelve un resizeEvent para reposicionar el chip del atajo."""
    def manejador(event):
        original(event)
        reubicar()
    return manejador


class TeachingTab(QWidget):
    def __init__(self):
        super().__init__()
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(9)

        # ══════════ IZQUIERDA: JOGGING ══════════
        col = QVBoxLayout()
        col.setSpacing(9)

        # -- segmented control de incremento, dentro del encabezado --
        step_box = QFrame()
        # Selector acotado: sin él el borde alcanzaba a cada QRadioButton hijo.
        step_box.setObjectName("step_box")
        step_box.setStyleSheet(
            "QFrame#step_box{background:#101316;border:1px solid #2f353c;"
            "border-radius:6px;}")
        sl = QHBoxLayout(step_box)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        # El incremento es en PASOS, igual que el firmware (:#X<n>). Los nombres
        # radio_*deg vienen de la v1, cuando se rotulaban en grados por error.
        self.radio_1deg = QRadioButton("1 paso")
        self.radio_10deg = QRadioButton("10 pasos")
        self.radio_50deg = QRadioButton("50 pasos")
        self.radio_10deg.setChecked(True)
        for r in (self.radio_1deg, self.radio_10deg, self.radio_50deg):
            # se dibujan como botones, no como radios
            r.setStyleSheet(
                "QRadioButton{color:#8b949e;font-family:'IBM Plex Mono';font-size:12px;"
                "font-weight:600;padding:7px 14px;}"
                "QRadioButton::indicator{width:0;height:0;}"
                "QRadioButton:checked{background:#2a7fb8;color:#ffffff;border-radius:5px;}")
            sl.addWidget(r)

        self.step_group = QButtonGroup(self)
        self.step_group.addButton(self.radio_1deg, 1)
        self.step_group.addButton(self.radio_10deg, 10)
        self.step_group.addButton(self.radio_50deg, 50)

        card_jog = SectionCard("Control manual", right_widget=step_box)

        pad_row = QHBoxLayout()
        pad_row.setSpacing(12)

        # cruz X/Y
        grid = QGridLayout()
        grid.setSpacing(6)
        self.btn_y_plus = _jog("Y+", "Incrementar posición Y.  [↑]")
        self.btn_y_minus = _jog("Y−", "Reducir posición Y.  [↓]")
        self.btn_x_plus = _jog("X+", "Incrementar posición X.  [→]")
        self.btn_x_minus = _jog("X−", "Reducir posición X.  [←]")
        self.btn_home_xy = _jog("Hxy", "Mandar a home los motores X e Y.", "home")

        grid.addWidget(self.btn_y_plus, 0, 1)
        grid.addWidget(self.btn_x_minus, 1, 0)
        grid.addWidget(self.btn_home_xy, 1, 1)
        grid.addWidget(self.btn_x_plus, 1, 2)
        grid.addWidget(self.btn_y_minus, 2, 1)
        pad_row.addLayout(grid, 1)

        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background:%s;" % C_BORDER)
        pad_row.addWidget(divider)

        # columna Z
        zcol = QVBoxLayout()
        zcol.setSpacing(6)
        self.btn_z_plus = _jog("Z+", "Incrementar posición Z.  [W]")
        self.btn_home_z = _jog("Hz", "Mandar a home al motor Z.", "home")
        self.btn_z_minus = _jog("Z−", "Reducir posición Z.  [S]")
        for b in (self.btn_z_plus, self.btn_home_z, self.btn_z_minus):
            b.setFixedWidth(104)
            zcol.addWidget(b)
        pad_row.addLayout(zcol)

        card_jog.body.addLayout(pad_row)
        col.addWidget(card_jog)

        # atajos visibles
        self.kbd_hints = [
            _shortcut(self.btn_y_plus, "↑"), _shortcut(self.btn_y_minus, "↓"),
            _shortcut(self.btn_x_plus, "→"), _shortcut(self.btn_x_minus, "←"),
            _shortcut(self.btn_z_plus, "W"), _shortcut(self.btn_z_minus, "S"),
        ]

        # -- velocidad --
        self.lbl_speed_val = QLabel("50%")
        self.lbl_speed_val.setStyleSheet(
            "color:#4fc0ff;font-family:'IBM Plex Mono';font-size:14px;")
        card_speed = SectionCard("Velocidad", right_widget=self.lbl_speed_val)

        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(10, 100)
        self.slider_speed.setValue(50)
        self.slider_speed.setTickPosition(QSlider.NoTicks)
        card_speed.body.addWidget(self.slider_speed)

        ends = QHBoxLayout()
        for txt, align in (("10%", Qt.AlignLeft), ("100%", Qt.AlignRight)):
            l = QLabel(txt)
            l.setAlignment(align | Qt.AlignVCenter)
            l.setStyleSheet(
                "color:#5e6871;font-family:'IBM Plex Mono';font-size:12px;")
            ends.addWidget(l, 1)
        card_speed.body.addLayout(ends)
        col.addWidget(card_speed)

        # -- garra --
        card_grip = SectionCard("Garra")
        grip_row = QHBoxLayout()
        grip_row.setSpacing(7)
        self.btn_open_grip = QPushButton("  Abrir")
        self.btn_open_grip.setToolTip("Abrir garra según ángulo seteado.")
        self.btn_close_grip = QPushButton("  Cerrar")
        self.btn_close_grip.setToolTip("Cerrar garra según ángulo seteado.")
        for b in (self.btn_open_grip, self.btn_close_grip):
            b.setMinimumHeight(46)
            grip_row.addWidget(b)
        card_grip.body.addLayout(grip_row)
        col.addWidget(card_grip)

        col.addStretch()
        left = QWidget()
        left.setFixedWidth(392)
        left.setLayout(col)
        root.addWidget(left)

        # ══════════ DERECHA: RUTINA ══════════
        card_list = SectionCard("Rutina actual")
        self.lbl_count = QLabel("0 puntos")
        self.lbl_count.setProperty("role", "chip")
        card_list.add_header_widget(self.lbl_count)

        self.table_points = QTableWidget()
        self.table_points.setColumnCount(8)
        self.table_points.setHorizontalHeaderLabels(
            ["#", "NOMBRE", "X", "Y", "Z", "GARRA", "VEL %", "ESPERA s"])
        self.table_points.setAlternatingRowColors(True)
        self.table_points.setShowGrid(False)
        self.table_points.verticalHeader().setVisible(False)
        self.table_points.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_points.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_points.setItemDelegate(PointDelegate(self.table_points))
        self.table_points.setToolTip(
            "Doble clic en una celda para editarla. ESPERA s es la pausa del "
            "robot al terminar ese paso, antes de arrancar el siguiente.")
        hh = self.table_points.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(COL_NUM, QHeaderView.Fixed)
        hh.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        # La espera lleva coma decimal y el rótulo más largo de la fila: con la
        # columna en modo Stretch el encabezado salía recortado ("ESPER…").
        hh.setSectionResizeMode(COL_T, QHeaderView.Fixed)
        self.table_points.setColumnWidth(COL_NUM, 56)
        self.table_points.setColumnWidth(COL_T, 112)
        self.table_points.verticalHeader().setDefaultSectionSize(46)
        card_list.body.addWidget(self.table_points)

        # DOS filas de acciones. Con los seis botones en una sola, a 1280px de
        # ancho (el mínimo de la ventana) Qt recortaba los rótulos a "Captu",
        # "Borr", "Limp"… En dos filas entran los textos completos.
        #   · fila 1 — editar la lista: capturar, borrar y reordenar
        #   · fila 2 — acciones sobre la rutina entera: limpiar y exportar
        self.btn_add_point = QPushButton("  Capturar punto")
        self.btn_add_point.setProperty("variant", "primary")
        self.btn_add_point.setToolTip("Agregar la posición actual a la rutina.")
        self.btn_del_point = QPushButton("  Borrar")
        self.btn_del_point.setToolTip("Borrar la fila seleccionada.")
        # Reordenar: el orden de la tabla es el orden de ejecución, así que un
        # punto capturado fuera de lugar obligaba a borrarlo y volver a llevar el
        # brazo hasta esa posición para recapturarlo.
        self.btn_move_up = QPushButton("▲ Subir")
        self.btn_move_up.setToolTip("Adelantar el punto seleccionado un lugar.")
        self.btn_move_down = QPushButton("▼ Bajar")
        self.btn_move_down.setToolTip("Atrasar el punto seleccionado un lugar.")
        for b in (self.btn_move_up, self.btn_move_down):
            b.setEnabled(False)     # sin fila seleccionada no hay nada que mover
        self.btn_clear_all = QPushButton("  Limpiar todo")
        self.btn_clear_all.setProperty("variant", "danger")
        self.btn_clear_all.setToolTip("Borrar todas las posiciones de la rutina.")
        self.btn_save_file = QPushButton("  Guardar rutina JSON")
        self.btn_save_file.setProperty("variant", "success")
        self.btn_save_file.setToolTip("Exportar la rutina a un archivo .json.")

        fila_edicion = QHBoxLayout()
        fila_edicion.setSpacing(7)
        # "Capturar punto" es la acción principal y además la de rótulo más
        # largo: se lleva más ancho que las otras tres.
        for b, peso in ((self.btn_add_point, 3), (self.btn_del_point, 2),
                        (self.btn_move_up, 2), (self.btn_move_down, 2)):
            b.setProperty("role", "compact")
            b.setMinimumHeight(40)
            fila_edicion.addWidget(b, peso)
        card_list.body.addLayout(fila_edicion)

        fila_rutina = QHBoxLayout()
        fila_rutina.setSpacing(7)
        for b in (self.btn_clear_all, self.btn_save_file):
            b.setMinimumHeight(40)
        fila_rutina.addWidget(self.btn_clear_all)
        fila_rutina.addStretch()
        fila_rutina.addWidget(self.btn_save_file)
        card_list.body.addLayout(fila_rutina)

        root.addWidget(card_list, 1)
