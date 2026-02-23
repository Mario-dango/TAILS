"""
PANEL DE CONSOLA (Terminal Inferior)
Este widget encapsula la terminal de texto negro y la línea de entrada de comandos.
Hereda de QWidget para poder ser incrustado en cualquier parte de la ventana principal.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt

class ConsolePanel(QWidget):
    def __init__(self):
        super().__init__()
        
        # Configuramos el layout principal del panel (Vertical)
        # setContentsMargins(0,0,0,0) elimina bordes extraños al incrustarlo
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. ÁREA DE TEXTO (LOG)
        # Usamos QTextEdit en modo solo lectura para mostrar el historial
        self.txt_console = QTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setMaximumHeight(150) # Altura máxima para no comerse toda la pantalla
        
        # Estilo CSS "Hardcoded" para asegurar que siempre parezca una terminal 
        # independientemente del tema general
        self.txt_console.setStyleSheet("""
            font-family: Consolas, Monospace; 
            font-size: 11px; 
            background-color: #111; 
            color: #0f0;
        """)
        
        # 2. ÁREA DE INPUT (Línea de comandos y botones)
        self.lay_input = QHBoxLayout()
        
        # Etiqueta decorativa estilo prompt
        self.lbl_prompt = QLabel(">_")
        
        # Campo de texto para escribir
        self.input_console = QLineEdit()
        self.input_console.setPlaceholderText("Escribe un comando manual (ej: :-H, :#X100)...")
        self.input_console.setMinimumHeight(64) # Altura táctil cómoda
        
        # Botón ENVIAR
        self.btn_send = QPushButton("Enviar")
        self.btn_send.setMinimumHeight(64)
        self.btn_send.setToolTip("Enviar comando ingresado a la consola.") 
        
        # Botón LIMPIAR
        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setMinimumHeight(64)
        self.btn_clear.setToolTip("Limpiar la consola de comandos.") 
        
        # Agregamos los widgets al layout horizontal
        self.lay_input.addWidget(self.lbl_prompt)
        self.lay_input.addWidget(self.input_console)
        self.lay_input.addWidget(self.btn_send)
        self.lay_input.addWidget(self.btn_clear)
        
        # 3. ENSAMBLAJE FINAL
        self.layout.addWidget(self.txt_console)
        self.layout.addLayout(self.lay_input)