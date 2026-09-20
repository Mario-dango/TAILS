"""
BANNER DE ALARMA (nuevo en v2)
-------------------------------
Franja roja que aparece bajo el app bar cuando el sistema está bloqueado
(parada de emergencia, error de puerto, fin de carrera inesperado).
Antes esa información sólo existía como una línea más en la consola.

Uso desde el controlador:
    self.view.alarm.show_alarm("Parada de emergencia activa", "Los motores...")
    self.view.alarm.hide_alarm()
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton


class AlarmBanner(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("alarm_banner")
        self.setFixedHeight(0)          # oculto por defecto
        self.setVisible(False)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 9, 14, 9)
        lay.setSpacing(11)

        self.lbl_icon = QLabel()        # icono asignado desde view.py
        self.lbl_icon.setFixedSize(30, 30)
        lay.addWidget(self.lbl_icon)

        col = QVBoxLayout()
        col.setSpacing(2)
        self.lbl_title = QLabel("")
        self.lbl_title.setProperty("role", "section")
        self.lbl_body = QLabel("")
        self.lbl_body.setProperty("role", "hint")
        self.lbl_body.setWordWrap(True)
        col.addWidget(self.lbl_title)
        col.addWidget(self.lbl_body)
        lay.addLayout(col, 1)

        self.btn_rearm = QPushButton("Rearmar (:-R)")
        self.btn_rearm.setProperty("variant", "danger")
        self.btn_rearm.setFixedHeight(39)
        lay.addWidget(self.btn_rearm)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(39, 39)
        self.btn_close.setStyleSheet(
            "QPushButton{background:transparent;border:1px solid #6b2229;"
            "border-radius:6px;color:#ff9d9d;}"
            "QPushButton:hover{background:#4a1a1e;}")
        self.btn_close.clicked.connect(self.hide_alarm)
        lay.addWidget(self.btn_close)

    def show_alarm(self, title, body):
        self.lbl_title.setText(title.upper())
        self.lbl_body.setText(body)
        self.setFixedHeight(70)
        self.setVisible(True)

    def hide_alarm(self):
        self.setVisible(False)
        self.setFixedHeight(0)
