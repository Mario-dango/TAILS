"""
PESTAÑA DE CALIBRACIÓN
Este widget contiene los controles para la inicialización del robot (Homing),
la definición del punto cero y la configuración de los límites de la garra.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QPushButton, QLineEdit, QLabel, QCheckBox

class CalibrationTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Layout principal de la pestaña (Vertical)
        self.layout = QVBoxLayout(self)
        
        # ==========================================
        # 1. GRUPO: INICIALIZACIÓN (Homing)
        # ==========================================
        self.grp_home = QGroupBox("Inicialización")
        self.lay_home = QHBoxLayout(self.grp_home)
        
        # Botón HOME ALL
        self.btn_home = QPushButton("HOME ALL (:-H)")
        self.btn_home.setToolTip("Ejecutar comando Home, para inicializar posiciones de referencia.")
        
        # Botón SET ZERO
        self.btn_setzero = QPushButton("Set Zero Here (:-Z)")
        self.btn_setzero.setToolTip("Setear nuevo Zero Home en posición actual.")
        
        self.lay_home.addWidget(self.btn_home)
        self.lay_home.addWidget(self.btn_setzero)
        
        self.layout.addWidget(self.grp_home)
        
        # ==========================================
        # 2. GRUPO: CONFIGURACIÓN DE GARRA
        # ==========================================
        self.grp_grip = QGroupBox("Configuración de Garra")
        # Usamos QGridLayout para alinear perfectamente los textos, inputs y botones
        self.lay_grip = QGridLayout(self.grp_grip)
        
        # Fila 0: Ángulo de Apertura
        self.input_angle_open = QLineEdit("90") # Valor por defecto
        self.btn_set_open = QPushButton("Set Apertura (:-A)")
        self.btn_set_open.setToolTip("Setear apertura de garra.")
        
        self.lay_grip.addWidget(QLabel("Ángulo Abierto:"), 0, 0)
        self.lay_grip.addWidget(self.input_angle_open, 0, 1)
        self.lay_grip.addWidget(self.btn_set_open, 0, 2)
        
        # Fila 1: Ángulo de Cierre
        self.input_angle_close = QLineEdit("0") # Valor por defecto
        self.btn_set_close = QPushButton("Set Cierre (:-P)")
        self.btn_set_close.setToolTip("Setear cierre de garra.")
        
        self.lay_grip.addWidget(QLabel("Ángulo Cerrado:"), 1, 0)
        self.lay_grip.addWidget(self.input_angle_close, 1, 1)
        self.lay_grip.addWidget(self.btn_set_close, 1, 2)
        
        self.layout.addWidget(self.grp_grip)
        
        # ==========================================
        # 3. HABILITACIÓN DE MOTORES (Enable)
        # ==========================================
        # Checkbox suelto al final del layout
        self.chk_enable = QCheckBox("Habilitar Motores (Enable)")
        self.chk_enable.setChecked(True) # Activado por defecto por seguridad
        
        self.layout.addWidget(self.chk_enable)
        
        # Espaciador al final para empujar todos los grupos hacia arriba 
        # y que no se estiren deformando la interfaz al maximizar la ventana
        self.layout.addStretch()