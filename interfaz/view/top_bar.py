"""
BARRA SUPERIOR (nueva en v2)
-----------------------------
La conexión serial dejó de vivir escondida dentro del panel izquierdo:
ahora está en el app bar, junto a un indicador de enlace y a la telemetría
condensada X/Y/Z. Así el estado del robot se lee sin buscar.

Expone: combo_ports, btn_refresh, btn_connect, lbl_link, val_x/val_y/val_z,
        btn_kawaii, btn_help
"""

from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel,
                             QComboBox, QPushButton)
from PyQt5.QtCore import Qt
from view.ui_widgets import C_PANEL, C_BORDER, C_SUNKEN


def _sep():
    f = QFrame()
    f.setFixedWidth(1)
    f.setStyleSheet("background:%s;" % C_BORDER)
    return f


class TopBar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(67)
        self.setObjectName("top_bar")
        self.setStyleSheet(
            "QFrame#top_bar{background:%s;border-bottom:1px solid %s;}" % (C_PANEL, C_BORDER)
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(14)

        # --- marca ---
        brand = QVBoxLayout()
        brand.setSpacing(2)
        t = QLabel("T.A.I.L.S.")
        t.setProperty("role", "title")
        s = QLabel("BRAZO ARTICULADO 3-DOF")
        s.setProperty("role", "subtitle")
        brand.addWidget(t)
        brand.addWidget(s)

        self.lbl_logo = QLabel()          # icono asignado desde view.py
        self.lbl_logo.setFixedSize(41, 41)
        lay.addWidget(self.lbl_logo)
        lay.addLayout(brand)
        lay.addWidget(_sep())

        # --- conexión ---
        lbl_port = QLabel("PUERTO")
        lbl_port.setProperty("role", "section")
        lay.addWidget(lbl_port)

        self.combo_ports = QComboBox()
        self.combo_ports.setFixedWidth(140)
        self.combo_ports.setProperty("role", "mono")
        self.combo_ports.setToolTip("Seleccionar puerto COM disponible.")
        lay.addWidget(self.combo_ports)

        self.btn_refresh = QPushButton()
        self.btn_refresh.setProperty("variant", "icon")
        self.btn_refresh.setFixedSize(43, 43)
        self.btn_refresh.setToolTip("Refrescar lista de puertos.")
        lay.addWidget(self.btn_refresh)

        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.setCheckable(True)
        self.btn_connect.setFixedHeight(43)
        self.btn_connect.setMinimumWidth(158)
        self.btn_connect.setToolTip("Conectar/Desconectar el brazo robótico.")
        lay.addWidget(self.btn_connect)

        self.lbl_link = QLabel("SIN ENLACE")
        self.lbl_link.setProperty("class", "status_badge_off")
        self.lbl_link.setFixedHeight(43)
        self.lbl_link.setMinimumWidth(132)
        self.lbl_link.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_link)

        lay.addStretch()

        # --- telemetría condensada ---
        tele = QFrame()
        tele.setFixedHeight(43)
        # Selector acotado: sin el #telemetry_box el borde se propagaba a los QLabel
        # hijos (QLabel hereda de QFrame) y cada celda dibujaba su propio marco.
        tele.setObjectName("telemetry_box")
        tele.setStyleSheet(
            "QFrame#telemetry_box{background:%s;border:1px solid %s;border-radius:8px;}"
            % (C_SUNKEN, "#2f353c")
        )
        tl = QHBoxLayout(tele)
        tl.setContentsMargins(6, 0, 6, 0)
        tl.setSpacing(0)

        self.val_x, self.val_y, self.val_z = QLabel("0"), QLabel("0"), QLabel("0")
        for axis, val, role in (("X", self.val_x, "axis_x"),
                                ("Y", self.val_y, "axis_y"),
                                ("Z", self.val_z, "axis_z")):
            if tl.count():
                tl.addWidget(_sep())
            cell = QHBoxLayout()
            cell.setContentsMargins(9, 0, 9, 0)
            cell.setSpacing(6)
            lab = QLabel(axis)
            lab.setProperty("role", role)
            val.setStyleSheet(
                "font-family:'IBM Plex Mono',Consolas,monospace;font-size:18px;color:#e6e9ec;"
            )
            cell.addWidget(lab)
            cell.addWidget(val)
            tl.addLayout(cell)
        lay.addWidget(tele)

        # Mostrar/ocultar la terminal de comandos. La terminal es un dock: este
        # botón la esconde y la trae de vuelta desde cualquier lado, también si
        # el operador la cerró con la ✕ del dock o la dejó flotando.
        self.btn_console = QPushButton()
        self.btn_console.setProperty("variant", "icon")
        self.btn_console.setCheckable(True)
        self.btn_console.setChecked(True)
        self.btn_console.setFixedSize(43, 43)
        self.btn_console.setToolTip("Mostrar u ocultar la terminal de comandos.")
        lay.addWidget(self.btn_console)

        self.btn_kawaii = QPushButton()
        self.btn_kawaii.setProperty("variant", "icon")
        self.btn_kawaii.setCheckable(True)
        self.btn_kawaii.setChecked(True)
        self.btn_kawaii.setFixedSize(43, 43)
        self.btn_kawaii.setToolTip("Modo Kawaii (iconos ilustrados).")
        lay.addWidget(self.btn_kawaii)

        self.btn_help = QPushButton()
        self.btn_help.setProperty("variant", "icon")
        self.btn_help.setFixedSize(43, 43)
        self.btn_help.setToolTip("Manual de usuario.")
        lay.addWidget(self.btn_help)

    # --- API para el controlador ---
    def set_link(self, connected):
        self.lbl_link.setText("EN LÍNEA" if connected else "SIN ENLACE")
        self.lbl_link.setProperty(
            "class", "status_badge_home_on" if connected else "status_badge_off")
        self.btn_connect.setText("Desconectar" if connected else "Conectar")
        self.lbl_link.style().unpolish(self.lbl_link)
        self.lbl_link.style().polish(self.lbl_link)

    def set_position(self, x, y, z):
        self.val_x.setText(str(x))
        self.val_y.setText(str(y))
        self.val_z.setText(str(z))
