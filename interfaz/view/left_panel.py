"""
PANEL IZQUIERDO (Estado y Conexión)
Contiene los controles de conexión Serial, los displays LCD de posición,
los LEDs de estado de sensores y el botón de Parada de Emergencia.
"""

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QPushButton, QLCDNumber
from PyQt5.QtCore import Qt, QSize

class LeftPanel(QGroupBox):
    def __init__(self):
        super().__init__("Estado Global") # Título del recuadro principal
        
        # Layout vertical principal
        self.layout = QVBoxLayout(self)
        
        # --- SECCIÓN A: CONEXIÓN ---
        self.grp_conn = QGroupBox("Conexión")
        self.lay_conn = QVBoxLayout(self.grp_conn)

        # Sub-layout horizontal para el combo y el botón de refrescar
        self.h_lay_ports = QHBoxLayout() 

        self.combo_ports = QComboBox()
        self.combo_ports.setToolTip("Seleccionar puerto COM disponible.")

        self.btn_refresh = QPushButton() 
        self.btn_refresh.setFixedSize(64, 64) # Botón cuadrado     
        self.btn_refresh.setToolTip("Refrescar lista de puertos.") 

        self.h_lay_ports.addWidget(self.combo_ports)
        self.h_lay_ports.addWidget(self.btn_refresh)

        # Botón grande de conectar
        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.setFixedHeight(64)
        self.btn_connect.setToolTip("Conectar/Desconectar el brazo robótico.")
        self.btn_connect.setCheckable(True) # Permite que el botón se quede "presionado" visualmente

        self.lay_conn.addWidget(QLabel("Puerto COM:"))
        self.lay_conn.addLayout(self.h_lay_ports)
        self.lay_conn.addWidget(self.btn_connect)
        
        self.layout.addWidget(self.grp_conn)
        
        # --- SECCIÓN B: TELEMETRÍA (LCDs) ---
        self.grp_pos = QGroupBox("Posición Actual")
        self.lay_pos = QGridLayout(self.grp_pos)
        
        # Creamos los 3 displays digitales
        self.lcd_x = QLCDNumber()
        self.lcd_y = QLCDNumber()
        self.lcd_z = QLCDNumber()
        
        # Configuración visual de los LCDs
        for lcd in [self.lcd_x, self.lcd_y, self.lcd_z]:
            lcd.setDigitCount(4) # Mostrar hasta 4 dígitos (ej: 1800)
            lcd.setSegmentStyle(QLCDNumber.Flat) # Estilo moderno plano

        # Los ubicamos en una grilla (Fila, Columna)
        self.lay_pos.addWidget(QLabel("X:"), 0, 0); self.lay_pos.addWidget(self.lcd_x, 0, 1)
        self.lay_pos.addWidget(QLabel("Y:"), 1, 0); self.lay_pos.addWidget(self.lcd_y, 1, 1)
        self.lay_pos.addWidget(QLabel("Z:"), 2, 0); self.lay_pos.addWidget(self.lcd_z, 2, 1)
        
        self.layout.addWidget(self.grp_pos)

        # --- SECCIÓN C: SENSORES (LEDs Virtuales) ---
        self.grp_sens = QGroupBox("Sensores")
        self.lay_sens = QHBoxLayout(self.grp_sens)
        
        # Creamos Labels que usaremos como círculos de colores
        self.led_x = QLabel("X"); self.led_x.setAlignment(Qt.AlignCenter)
        self.led_y = QLabel("Y"); self.led_y.setAlignment(Qt.AlignCenter)
        self.led_z = QLabel("Z"); self.led_z.setAlignment(Qt.AlignCenter)
        
        # Forzamos tamaño fijo para que el border-radius de CSS los haga círculos perfectos
        self.led_x.setFixedSize(30, 30)
        self.led_y.setFixedSize(30, 30)
        self.led_z.setFixedSize(30, 30)
        
        # Asignamos ID de objeto para que style.css aplique el color gris (apagado)
        self.led_x.setObjectName("sensor_led_off")
        self.led_y.setObjectName("sensor_led_off")
        self.led_z.setObjectName("sensor_led_off")

        self.lay_sens.addWidget(self.led_x)
        self.lay_sens.addWidget(self.led_y)
        self.lay_sens.addWidget(self.led_z)
        
        self.layout.addWidget(self.grp_sens)

        # --- SECCIÓN D: INDICADORES DE SISTEMA ---
        self.grp_sys = QGroupBox("Sistema")
        self.lay_sys = QVBoxLayout(self.grp_sys)
        
        # Etiquetas de estado
        self.lbl_status_home = QLabel("HOME")
        self.lbl_status_wait = QLabel("WAIT / BUSY")
        self.lbl_status_finish = QLabel("FINISH")
        
        # Propiedades dinámicas para CSS (Badge de estado)
        self.lbl_status_home.setProperty("class", "status_badge_off")
        self.lbl_status_wait.setProperty("class", "status_badge_off")
        self.lbl_status_finish.setProperty("class", "status_badge_off")
        
        self.lay_sys.addWidget(self.lbl_status_home)
        self.lay_sys.addWidget(self.lbl_status_wait)
        self.lay_sys.addWidget(self.lbl_status_finish)
        
        self.layout.addWidget(self.grp_sys)

        # --- SECCIÓN E: STOP EMERGENCIA ---
        self.btn_estop = QPushButton("STOP EMERGENCIA")
        # Propiedad especial para que se ponga rojo (ver style.css)
        self.btn_estop.setProperty("class", "stop_button") 
        self.btn_estop.setMinimumHeight(64)
        
        self.layout.addWidget(self.btn_estop)
        
        # Espaciador final para empujar todo hacia arriba
        self.layout.addStretch()