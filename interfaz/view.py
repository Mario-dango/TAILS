from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QLabel, QComboBox, QPushButton, 
                             QTabWidget, QGroupBox, QLCDNumber, QTextEdit, 
                             QLineEdit, QCheckBox, QRadioButton, QButtonGroup,
                             QTableWidget, QProgressBar, QHeaderView, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class View(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Control Interface - STM32")
        self.resize(1100, 750) 
        
        # Widget Central Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        # --- SECCIÓN SUPERIOR (Paneles) ---
        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Panel Izquierdo (Status)
        self.panel_left = self.setup_left_panel()
        
        # 2. Panel Central (Tabs)
        self.panel_tabs = self.setup_central_tabs()
        
        top_layout.addWidget(self.panel_left, 1) # 25% ancho
        top_layout.addWidget(self.panel_tabs, 3) # 75% ancho
        
        self.main_layout.addWidget(top_section)

        # --- SECCIÓN INFERIOR (Consola Desplegable) ---
        self.console_container = self.setup_bottom_console()
        
        # Botón pequeño para mostrar/ocultar consola
        self.btn_toggle_console = QPushButton("Mostrar/Ocultar Terminal de Comandos")
        self.btn_toggle_console.setCheckable(True)
        self.btn_toggle_console.setChecked(True)
        self.btn_toggle_console.clicked.connect(self.toggle_console)
        self.btn_toggle_console.setMaximumHeight(20)
        
        self.main_layout.addWidget(self.btn_toggle_console)
        self.main_layout.addWidget(self.console_container)
        
        self.set_stylesheet()

    def set_stylesheet(self):
        try:
            with open("style.css", "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            print("Archivo style.css no encontrado")

    def toggle_console(self):
        is_visible = self.btn_toggle_console.isChecked()
        self.console_container.setVisible(is_visible)

    # ==========================================
    #   1. PANEL IZQUIERDO: ESTADO Y CONEXIÓN
    # ==========================================
    def setup_left_panel(self):
        panel = QGroupBox("Estado Global")
        layout = QVBoxLayout(panel)
        
        # A. Conexión
        grp_conn = QGroupBox("Conexión")
        lay_conn = QVBoxLayout(grp_conn)

        # Layout horizontal para combo y botón de refrescar
        h_lay_ports = QHBoxLayout() 

        self.combo_ports = QComboBox()
        self.btn_refresh = QPushButton("R") # R de Refresh (o usa un icono)
        self.btn_refresh.setFixedWidth(30)  # Botón pequeño

        h_lay_ports.addWidget(self.combo_ports)
        h_lay_ports.addWidget(self.btn_refresh)

        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.setCheckable(True) 

        lay_conn.addWidget(QLabel("Puerto COM:"))
        lay_conn.addLayout(h_lay_ports) # Agregamos el layout horizontal
        lay_conn.addWidget(self.btn_connect)
        layout.addWidget(grp_conn)

        # self.combo_ports = QComboBox()
        # self.btn_connect = QPushButton("Conectar")
        # self.btn_connect.setCheckable(True) 
        # lay_conn.addWidget(QLabel("Puerto COM:"))
        # lay_conn.addWidget(self.combo_ports)
        # lay_conn.addWidget(self.btn_connect)
        # layout.addWidget(grp_conn)
        
        # B. Telemetría (LCDs)
        grp_pos = QGroupBox("Posición Actual")
        lay_pos = QGridLayout(grp_pos)
        
        self.lcd_x = QLCDNumber()
        self.lcd_y = QLCDNumber()
        self.lcd_z = QLCDNumber()
        # Estilo "Flat" para LCDs
        for lcd in [self.lcd_x, self.lcd_y, self.lcd_z]:
            lcd.setDigitCount(4)
            lcd.setSegmentStyle(QLCDNumber.Flat)

        lay_pos.addWidget(QLabel("X:"), 0, 0); lay_pos.addWidget(self.lcd_x, 0, 1)
        lay_pos.addWidget(QLabel("Y:"), 1, 0); lay_pos.addWidget(self.lcd_y, 1, 1)
        lay_pos.addWidget(QLabel("Z:"), 2, 0); lay_pos.addWidget(self.lcd_z, 2, 1)
        layout.addWidget(grp_pos)

        # C. Sensores y Garra
        grp_sens = QGroupBox("Sensores")
        lay_sens = QHBoxLayout(grp_sens)
        
        # Simulamos LEDs con Labels redondos (se estilizarán en CSS o lógica)
        self.led_x = QLabel("X"); self.led_x.setAlignment(Qt.AlignCenter)
        self.led_y = QLabel("Y"); self.led_y.setAlignment(Qt.AlignCenter)
        self.led_z = QLabel("Z"); self.led_z.setAlignment(Qt.AlignCenter)
        
        # Asignar nombres de objeto para CSS ID
        self.led_x.setObjectName("sensor_led_off")
        self.led_y.setObjectName("sensor_led_off")
        self.led_z.setObjectName("sensor_led_off")

        lay_sens.addWidget(self.led_x)
        lay_sens.addWidget(self.led_y)
        lay_sens.addWidget(self.led_z)
        layout.addWidget(grp_sens)

        # D. STOP
        self.btn_estop = QPushButton("STOP EMERGENCIA")
        self.btn_estop.setProperty("class", "stop_button") # Para CSS
        self.btn_estop.setMinimumHeight(60)
        layout.addWidget(self.btn_estop)
        
        layout.addStretch() # Empujar todo arriba
        return panel

    # ==========================================
    #   2. PANEL CENTRAL: PESTAÑAS
    # ==========================================
    def setup_central_tabs(self):
        tabs = QTabWidget()
        
        # Crear las 3 pestañas
        self.tab_calib = QWidget()
        self.setup_tab_calibration(self.tab_calib)
        
        self.tab_teach = QWidget()
        self.setup_tab_teaching(self.tab_teach)
        
        self.tab_run = QWidget()
        self.setup_tab_execution(self.tab_run)
        
        tabs.addTab(self.tab_calib, "CALIBRACIÓN")
        tabs.addTab(self.tab_teach, "APRENDIZAJE")
        tabs.addTab(self.tab_run, "EJECUCIÓN")
        
        return tabs

    def setup_tab_calibration(self, parent):
        layout = QVBoxLayout(parent)
        
        # 1. Homing
        grp_home = QGroupBox("Inicialización")
        lay_home = QHBoxLayout(grp_home)
        self.btn_home = QPushButton("HOME ALL (:-H)")
        self.btn_setzero = QPushButton("Set Zero Here (:-Z)")
        lay_home.addWidget(self.btn_home)
        lay_home.addWidget(self.btn_setzero)
        layout.addWidget(grp_home)
        
        # 2. Config Garra
        grp_grip = QGroupBox("Configuración de Garra")
        lay_grip = QGridLayout(grp_grip)
        
        self.input_angle_open = QLineEdit("90")
        self.btn_set_open = QPushButton("Set Apertura (:-A)")
        
        self.input_angle_close = QLineEdit("0")
        self.btn_set_close = QPushButton("Set Cierre (:-P)")
        
        lay_grip.addWidget(QLabel("Ángulo Abierto:"), 0, 0)
        lay_grip.addWidget(self.input_angle_open, 0, 1)
        lay_grip.addWidget(self.btn_set_open, 0, 2)
        
        lay_grip.addWidget(QLabel("Ángulo Cerrado:"), 1, 0)
        lay_grip.addWidget(self.input_angle_close, 1, 1)
        lay_grip.addWidget(self.btn_set_close, 1, 2)
        layout.addWidget(grp_grip)
        
        # 3. Enable
        self.chk_enable = QCheckBox("Habilitar Motores (Enable)")
        self.chk_enable.setChecked(True)
        layout.addWidget(self.chk_enable)
        
        layout.addStretch()

    def setup_tab_teaching(self, parent):
        layout = QHBoxLayout(parent)
        
        # Columna Izq: Jogging
        col_jog = QVBoxLayout()
        grp_jog = QGroupBox("Control Manual (Jogging)")
        grid_jog = QGridLayout(grp_jog)
        
        # Botones Jog
        self.btn_y_plus = QPushButton("Y+")
        self.btn_y_minus = QPushButton("Y-")
        self.btn_x_plus = QPushButton("X+")
        self.btn_x_minus = QPushButton("X-")
        
        # NUEVO: Botón Central Hxy (Ir a X0 Y0)
        self.btn_home_xy = QPushButton("Hxy")
        self.btn_home_xy.setStyleSheet("background-color: #00bcd4; color: black; font-weight: bold;")
        
        self.btn_z_plus = QPushButton("Z+")
        self.btn_z_minus = QPushButton("Z-")
        
        # NUEVO: Botón Central Hz (Ir a Z0)
        self.btn_home_z = QPushButton("Hz")
        self.btn_home_z.setStyleSheet("background-color: #00bcd4; color: black; font-weight: bold;")

        # Grilla X/Y
        grid_jog.addWidget(self.btn_y_plus, 0, 1)
        grid_jog.addWidget(self.btn_x_minus, 1, 0)
        grid_jog.addWidget(self.btn_home_xy, 1, 1) # <--- AQUÍ ESTÁ EL CENTRO
        grid_jog.addWidget(self.btn_x_plus, 1, 2)
        grid_jog.addWidget(self.btn_y_minus, 2, 1)
        
        # Separador y Columna Z
        grid_jog.addWidget(QLabel("   |   "), 1, 3) 
        grid_jog.addWidget(self.btn_z_plus, 0, 4)
        grid_jog.addWidget(self.btn_home_z, 1, 4) # <--- AQUÍ EN MEDIO DE Z
        grid_jog.addWidget(self.btn_z_minus, 2, 4)
        
        col_jog.addWidget(grp_jog)
        
        # Pasos (Modificado a Grados)
        grp_step = QGroupBox("Incremento (Grados)")
        lay_step = QHBoxLayout(grp_step)
        
        self.radio_1deg = QRadioButton("1°")
        self.radio_10deg = QRadioButton("10°")
        self.radio_50deg = QRadioButton("50°")
        self.radio_10deg.setChecked(True) # Default
        
        self.step_group = QButtonGroup()
        self.step_group.addButton(self.radio_1deg, 1)
        self.step_group.addButton(self.radio_10deg, 10)
        self.step_group.addButton(self.radio_50deg, 50)
        
        lay_step.addWidget(self.radio_1deg)
        lay_step.addWidget(self.radio_10deg)
        lay_step.addWidget(self.radio_50deg)
        col_jog.addWidget(grp_step)
        
        # Garra Manual
        grp_man_grip = QGroupBox("Garra")
        lay_man_grip = QHBoxLayout(grp_man_grip)
        self.btn_open_grip = QPushButton("Abrir")
        self.btn_close_grip = QPushButton("Cerrar")
        lay_man_grip.addWidget(self.btn_open_grip)
        lay_man_grip.addWidget(self.btn_close_grip)
        col_jog.addWidget(grp_man_grip)
        
        col_jog.addStretch()
        
        # Columna Der: Tabla de Puntos
        col_list = QVBoxLayout()
        self.table_points = QTableWidget()
        self.table_points.setColumnCount(4)
        self.table_points.setHorizontalHeaderLabels(["X", "Y", "Z", "G"])
        self.table_points.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        col_list.addWidget(QLabel("Rutina Actual:"))
        col_list.addWidget(self.table_points)
        
        lay_btns_list = QHBoxLayout()
        self.btn_add_point = QPushButton("Guardar Punto Actual")
        self.btn_del_point = QPushButton("Borrar Seleccionado")
        self.btn_save_file = QPushButton("Guardar Rutina JSON")
        
        lay_btns_list.addWidget(self.btn_add_point)
        lay_btns_list.addWidget(self.btn_del_point)
        lay_btns_list.addWidget(self.btn_save_file)
        col_list.addLayout(lay_btns_list)
        
        layout.addLayout(col_jog, 1)
        layout.addLayout(col_list, 2)

    def setup_tab_execution(self, parent):
        layout = QVBoxLayout(parent)
        
        # Archivo
        lay_file = QHBoxLayout()
        self.lbl_file = QLabel("Archivo: Ninguno cargado")
        self.btn_load_file = QPushButton("Cargar Rutina")
        lay_file.addWidget(self.lbl_file)
        lay_file.addWidget(self.btn_load_file)
        layout.addLayout(lay_file)
        
        # Progreso
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Controles
        lay_ctrl = QHBoxLayout()
        self.btn_play = QPushButton("PLAY")
        self.btn_pause = QPushButton("PAUSA")
        self.btn_stop_run = QPushButton("DETENER")
        
        # Estilos botones play
        self.btn_play.setStyleSheet("background-color: #2e7d32; font-weight: bold;") # Verde
        self.btn_stop_run.setStyleSheet("background-color: #c62828; font-weight: bold;") # Rojo
        
        lay_ctrl.addWidget(self.btn_play)
        lay_ctrl.addWidget(self.btn_pause)
        lay_ctrl.addWidget(self.btn_stop_run)
        layout.addLayout(lay_ctrl)
        
        # Log de ejecución grande
        self.txt_run_log = QTextEdit()
        self.txt_run_log.setReadOnly(True)
        self.txt_run_log.setPlaceholderText("Detalles de ejecución aparecerán aquí...")
        layout.addWidget(self.txt_run_log)

    # ==========================================
    #   3. CONSOLA INFERIOR
    # ==========================================
    def setup_bottom_console(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.txt_console = QTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setMaximumHeight(150)
        self.txt_console.setStyleSheet("font-family: Consolas; font-size: 11px; background-color: #111; color: #0f0;")
        
        lay_input = QHBoxLayout()
        self.input_console = QLineEdit()
        self.input_console.setPlaceholderText("Escribe un comando manual (ej: :-H, :#X100)...")
        self.btn_send_console = QPushButton("Enviar")
        self.btn_clear_console = QPushButton("Limpiar")
        
        lay_input.addWidget(QLabel(">"))
        lay_input.addWidget(self.input_console)
        lay_input.addWidget(self.btn_send_console)
        lay_input.addWidget(self.btn_clear_console)
        
        layout.addWidget(self.txt_console)
        layout.addLayout(lay_input)
        
        return container