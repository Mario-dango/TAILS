"""
PANEL DE CONSOLA v2
--------------------
Cambios respecto de la v1:
 · Ya no es texto verde #0f0 sobre negro: gris claro legible, y el color se
   reserva para la etiqueta de severidad (INFO / TX / RX / OK / WARN / ERR).
 · Cabecera propia con el botón de mostrar/ocultar, contador de líneas y el
   estado del puerto; antes el toggle era una barra gris de 35px sin contexto.
 · append_line() formatea con timestamp + tag coloreado, así el controlador no
   tiene que armar HTML.

Expone: txt_console, input_console, btn_send, btn_clear,
        btn_toggle (nuevo), lbl_count, lbl_port
"""

from PyQt5.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QLineEdit, QPushButton, QLabel)
from PyQt5.QtCore import Qt
from view.ui_widgets import C_BORDER

MAX_HISTORIAL = 46


class CommandLineEdit(QLineEdit):
    """Caja de comandos con historial navegable, al estilo de una terminal.

    `↑` retrocede hacia comandos más viejos y `↓` avanza hacia los más nuevos;
    pasado el último, la línea queda vacía. Lo que se estaba escribiendo se
    conserva mientras se navega, así que salir del historial no pierde el borrador.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._historial = []
        self._idx = 0          # len(historial) == "no estoy navegando"
        self._borrador = ""

    def push_history(self, cmd):
        cmd = (cmd or "").strip()
        if not cmd:
            return
        # Sin repetidos consecutivos: repetir un comando no ensucia el historial.
        if not self._historial or self._historial[-1] != cmd:
            self._historial.append(cmd)
            del self._historial[:-MAX_HISTORIAL]
        self._idx = len(self._historial)
        self._borrador = ""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self._navegar(-1)
        elif event.key() == Qt.Key_Down:
            self._navegar(+1)
        else:
            super().keyPressEvent(event)

    def _navegar(self, paso):
        if not self._historial:
            return
        # Al entrar al historial guardamos lo que se estaba escribiendo
        if self._idx == len(self._historial):
            self._borrador = self.text()

        nuevo = max(0, min(len(self._historial), self._idx + paso))
        if nuevo == self._idx:
            return
        self._idx = nuevo
        self.setText(self._borrador if nuevo == len(self._historial)
                     else self._historial[nuevo])
        self.end(False)   # cursor al final, como una terminal


TAG_COLORS = {
    "INFO":   "#4fc0ff",
    "TX":     "#c8a2ff",
    "RX":     "#4ec97a",
    "OK":     "#4ec97a",
    "WARN":   "#f2b13c",
    "ERR":    "#ff7b7b",
    # Etiquetas que emite connection_manager.log_console(): sin estas entradas
    # los errores caían al gris neutro y dejaban de leerse como errores.
    "ERROR":  "#ff7b7b",
    "ALERTA": "#f2b13c",
}


class ConsolePanel(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------- cabecera ----------
        head = QFrame()
        head.setFixedHeight(46)
        # Selectores acotados (ver nota en left_panel.AxisReadout): un "border-top"
        # sin selector se propagaba a cada QLabel de la cabecera.
        head.setObjectName("console_head")
        head.setStyleSheet(
            "QFrame#console_head{background:#171a1e;border-top:1px solid %s;}" % C_BORDER)
        hl = QHBoxLayout(head)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(10)

        # Desde que la terminal es un QDockWidget, el nombre lo pone la barra de
        # título del dock: este botón sólo pliega el cuerpo dentro del dock, así
        # que se rotula por lo que hace y no repite el título.
        self.btn_toggle = QPushButton("  Plegar   ▾")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setChecked(True)
        self.btn_toggle.setFixedHeight(33)
        self.btn_toggle.setToolTip("Mostrar u ocultar la terminal de comandos.")
        hl.addWidget(self.btn_toggle)

        self.lbl_count = QLabel("0 líneas")
        self.lbl_count.setProperty("role", "chip")
        hl.addWidget(self.lbl_count)
        hl.addStretch()

        self.lbl_port = QLabel("sin puerto abierto")
        self.lbl_port.setStyleSheet(
            "color:#5e6871;font-family:'IBM Plex Mono';font-size:13px;")
        hl.addWidget(self.lbl_port)
        root.addWidget(head)

        # ---------- cuerpo ----------
        self.body = QFrame()
        self.body.setObjectName("console_body")
        self.body.setStyleSheet(
            "QFrame#console_body{background:#171a1e;border-top:1px solid %s;}" % C_BORDER)
        bl = QVBoxLayout(self.body)
        bl.setContentsMargins(12, 8, 12, 8)
        bl.setSpacing(8)

        self.txt_console = QTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setMinimumHeight(78)
        bl.addWidget(self.txt_console)

        row = QHBoxLayout()
        row.setSpacing(7)
        self.lbl_prompt = QLabel(">")
        self.lbl_prompt.setProperty("role", "prompt")
        row.addWidget(self.lbl_prompt)

        self.input_console = CommandLineEdit()
        self.input_console.setPlaceholderText(
            "Comando manual — ej. :-H, :#X100   ·   ↑ ↓ recorren el historial")
        self.input_console.setProperty("role", "mono")
        self.input_console.setFixedHeight(46)
        row.addWidget(self.input_console, 1)

        self.btn_send = QPushButton("  Enviar")
        self.btn_send.setProperty("variant", "primary")
        self.btn_send.setFixedHeight(46)
        self.btn_send.setToolTip("Enviar el comando ingresado.")
        row.addWidget(self.btn_send)

        self.btn_clear = QPushButton()
        self.btn_clear.setProperty("variant", "icon")
        self.btn_clear.setFixedSize(46, 46)
        self.btn_clear.setToolTip("Limpiar la consola.")
        row.addWidget(self.btn_clear)

        bl.addLayout(row)
        root.addWidget(self.body)

        self._lines = 0
        self.btn_toggle.clicked.connect(self._toggle)

    # ---------- API ----------
    def _toggle(self):
        visible = self.btn_toggle.isChecked()
        self.body.setVisible(visible)
        self.btn_toggle.setText("  %s   %s" % ("Plegar" if visible else "Desplegar",
                                               "▾" if visible else "▸"))

    def append_line(self, tag, message):
        color = TAG_COLORS.get(tag.upper(), "#8b949e")
        from PyQt5.QtCore import QTime
        stamp = QTime.currentTime().toString("HH:mm:ss")
        self.txt_console.append(
            "<span style='color:#4d565e'>%s</span>&nbsp;&nbsp;"
            "<span style='color:%s;font-weight:600'>%-4s</span>&nbsp;&nbsp;"
            "<span style='color:#c3ccd4'>%s</span>"
            % (stamp, color, tag.upper(), message))
        self._lines += 1
        self.lbl_count.setText("%d líneas" % self._lines)

    def clear_console(self):
        self.txt_console.clear()
        self._lines = 0
        self.lbl_count.setText("0 líneas")

    def set_port(self, text):
        self.lbl_port.setText(text)

    def push_history(self, cmd):
        """Registra un comando enviado para poder recuperarlo con ↑."""
        self.input_console.push_history(cmd)
