"""
DIÁLOGO DE REPETICIÓN DE RUTINA
--------------------------------
Pregunta cuántas veces repetir la rutina cargada: una cantidad fija de ciclos o
de forma continua hasta que el operador la corte.

Uso:
    modo = RepeatDialog.pedir_ciclos(parent)
    if modo is None:            # canceló
        ...
    elif modo == RepeatDialog.CONTINUO:
        ...                     # bucle infinito
    else:
        ...                     # modo es un int: cantidad de ciclos
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QRadioButton, QSpinBox, QPushButton, QButtonGroup)
from PyQt5.QtCore import Qt


class RepeatDialog(QDialog):
    CONTINUO = -1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Repetir rutina")
        # Mismo "?" inútil de la barra de título que el panel de diagnóstico:
        # Windows lo agrega a todo QDialog y no tiene ninguna acción asociada.
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(460)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(14)

        titulo = QLabel("¿Cuántas veces querés repetir la rutina?")
        titulo.setProperty("role", "section")
        lay.addWidget(titulo)

        # --- opción 1: cantidad fija ---
        fila_n = QHBoxLayout()
        fila_n.setSpacing(10)
        self.radio_ciclos = QRadioButton("Cantidad de ciclos")
        self.radio_ciclos.setChecked(True)
        self.spin_ciclos = QSpinBox()
        self.spin_ciclos.setRange(1, 999)
        self.spin_ciclos.setValue(2)
        self.spin_ciclos.setSuffix("  ciclos")
        fila_n.addWidget(self.radio_ciclos)
        fila_n.addWidget(self.spin_ciclos)
        fila_n.addStretch()
        lay.addLayout(fila_n)

        # --- opción 2: continuo ---
        self.radio_continuo = QRadioButton("Modo continuo (sin límite)")
        lay.addWidget(self.radio_continuo)

        grupo = QButtonGroup(self)
        grupo.addButton(self.radio_ciclos)
        grupo.addButton(self.radio_continuo)
        self.radio_ciclos.toggled.connect(self.spin_ciclos.setEnabled)

        aviso = QLabel(
            "En modo continuo la rutina se repite hasta que la cortes con "
            "<b>DETENER</b>, con el <b>STOP EMERGENCIA</b> de la interfaz o con "
            "el pulsador físico de paro.")
        aviso.setProperty("role", "hint")
        aviso.setWordWrap(True)
        lay.addWidget(aviso)

        # --- botones ---
        botones = QHBoxLayout()
        botones.addStretch()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_ok = QPushButton("Iniciar")
        self.btn_ok.setProperty("variant", "primary")
        self.btn_ok.setDefault(True)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self.accept)
        botones.addWidget(self.btn_cancel)
        botones.addWidget(self.btn_ok)
        lay.addLayout(botones)

    def valor(self):
        """CONTINUO, o la cantidad de ciclos elegida."""
        if self.radio_continuo.isChecked():
            return self.CONTINUO
        return self.spin_ciclos.value()

    @classmethod
    def pedir_ciclos(cls, parent=None):
        """Muestra el diálogo. Devuelve None si el usuario canceló."""
        dlg = cls(parent)
        if dlg.exec_() != QDialog.Accepted:
            return None
        return dlg.valor()
