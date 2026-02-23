# from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
#                              QGridLayout, QLabel, QComboBox, QPushButton, 
#                              QTabWidget, QGroupBox, QLCDNumber, QTextEdit, 
#                              QLineEdit, QCheckBox, QRadioButton, QButtonGroup,
#                              QTableWidget, QProgressBar, QHeaderView, QSlider,
#                              QSpacerItem, QSizePolicy)
# from PyQt5.QtCore import Qt, QSize
# from PyQt5.QtGui import QIcon
# import os

# class View(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Technical Articulated Intelligent Linkage System (T.A.I.L.S.)")
#         # --- NUEVAS VARIABLES MODO KAWAII ---
#         self.is_kawaii = True          # Empieza con iconos encendidos
#         self.icon_registry = {}        # Diccionario para "recordar" qué icono va en qué botón
#         # ------------------------------------
#         self.resize(1100, 750) 
#         ruta_icono = os.path.join("resources/", "TAILS.ico") 
#         if os.path.exists(ruta_icono):
#             self.setWindowIcon(QIcon(ruta_icono))
#         else:
#             print(f"Advertencia: No se encontró el ícono en {ruta_icono}")
        
#         # 1. Llamamos a la creación del menú
#         self.setup_menu_bar()

#         # Widget Central Principal
#         central_widget = QWidget()
#         self.setCentralWidget(central_widget)
        
#         self.main_layout = QVBoxLayout(central_widget)
#         self.main_layout.setContentsMargins(5, 5, 5, 5)
#         self.main_layout.setSpacing(5)

#         # --- SECCIÓN SUPERIOR (Paneles) ---
#         top_section = QWidget()
#         top_layout = QHBoxLayout(top_section)
#         top_layout.setContentsMargins(0, 0, 0, 0)
        
#         # 1. Panel Izquierdo (Status)
#         self.panel_left = self.setup_left_panel()
        
#         # 2. Panel Central (Tabs)
#         self.panel_tabs = self.setup_central_tabs()
        
#         top_layout.addWidget(self.panel_left, 1) # 25% ancho
#         top_layout.addWidget(self.panel_tabs, 3) # 75% ancho
        
#         self.main_layout.addWidget(top_section)

#         # --- SECCIÓN INFERIOR (Consola Desplegable) ---
#         self.console_container = self.setup_bottom_console()
        
#         # Botón pequeño para mostrar/ocultar consola
#         self.btn_toggle_console = QPushButton("Mostrar/Ocultar Terminal de Comandos")
#         self.btn_toggle_console.setCheckable(True)
#         self.btn_toggle_console.setChecked(True)
#         self.set_btn_icon(self.btn_toggle_console, "showHide.png")
#         self.btn_toggle_console.setFixedHeight(64)
#         self.btn_toggle_console.setToolTip("Consola de comandos") # Ayuda visual
#         self.btn_toggle_console.clicked.connect(self.toggle_console)
#         # self.btn_toggle_console.setMaximumHeight(20)
        
#         self.main_layout.addWidget(self.btn_toggle_console)
#         self.main_layout.addWidget(self.console_container)
        
#         self.set_stylesheet()

#     def set_stylesheet(self):
#         try:
#             # ¡EL CAMBIO ESTÁ AQUÍ! Agregamos encoding='utf-8'
#             with open("style.css", "r", encoding='utf-8') as file:
#                 self.setStyleSheet(file.read())
#         except FileNotFoundError:
#             print("Archivo style.css no encontrado")

#     def toggle_console(self):
#         is_visible = self.btn_toggle_console.isChecked()
#         self.console_container.setVisible(is_visible)

#     def setup_menu_bar(self):
#         """Crea la barra de menús superior"""
#         menu_bar = self.menuBar()
        
#         # Menú "Ayuda"
#         help_menu = menu_bar.addMenu("Ayuda")
        
#         # Acciones dentro del menú
#         self.action_manual = help_menu.addAction("Manual de Usuario")
#         # Opcional: le puedes poner un icono al menú también
#         self.set_btn_icon(self.action_manual, "help.png") 

#         # --- NUEVO: BOTÓN MODO KAWAII ---
#         self.action_kawaii = help_menu.addAction("Modo Kawaii (Iconos)")
#         self.action_kawaii.setCheckable(True) # Para que tenga una "palomita/tick" de activado
#         self.action_kawaii.setChecked(True)   # Activado por defecto
#         self.set_btn_icon(self.action_kawaii, "kawaii.png") # Ponle un icono lindo si tienes

#         help_menu.addSeparator() # Una línea divisoria
#         self.action_about = help_menu.addAction("Acerca de T.A.I.L.S.")
#         self.set_btn_icon(self.action_about, "TAILS_icono.png")

#     # --- FUNCIÓN AUXILIAR PARA ICONOS (Agrégala dentro de la clase View) ---
#     def set_btn_icon(self, item, icon_name, size=64):
#         """Asigna un icono y lo guarda en el registro para el Modo Kawaii"""

#         # 1. Guardamos la configuración en la memoria (item es la llave)
#         self.icon_registry[item] = {"name": icon_name, "size": size}
        
#         # 2. Solo lo mostramos si el modo Kawaii está activo
#         if self.is_kawaii:
#             path = os.path.join("resources", icon_name)
#             if os.path.exists(path):
#                 item.setIcon(QIcon(path))
#                 if hasattr(item, 'setIconSize'):
#                     item.setIconSize(QSize(size, size))
#             else:
#                 print(f"Advertencia: No se encontró icono {icon_name}")

#     # --- APLICANDO ICONOS EN LOS PANELES ---

#     # ==========================================
#     #   1. PANEL IZQUIERDO: ESTADO Y CONEXIÓN
#     # ==========================================
#     def setup_left_panel(self):
#         panel = QGroupBox("Estado Global")
#         layout = QVBoxLayout(panel)
        
#         # A. Conexión
#         grp_conn = QGroupBox("Conexión")
#         lay_conn = QVBoxLayout(grp_conn)

#         # Layout horizontal para combo y botón de refrescar
#         h_lay_ports = QHBoxLayout() 

#         self.combo_ports = QComboBox()
#         # Botón Refresh
#         self.btn_refresh = QPushButton() # Quitamos la "R" de texto si el icono es claro
#         self.set_btn_icon(self.btn_refresh, "refresh.png")
#         self.btn_refresh.setFixedSize(64, 64)     
#         self.btn_refresh.setToolTip("Refrescar Puertos") # Ayuda visual

#         h_lay_ports.addWidget(self.combo_ports)
#         h_lay_ports.addWidget(self.btn_refresh)

#         self.btn_connect = QPushButton("Conectar")
#         self.set_btn_icon(self.btn_connect, "plug.png")
#         self.btn_connect.setFixedHeight(64)
#         self.btn_refresh.setToolTip("Conectar/Desconectar Puertos") # Ay
#         self.btn_connect.setCheckable(True) 

#         lay_conn.addWidget(QLabel("Puerto COM:"))
#         lay_conn.addLayout(h_lay_ports) # Agregamos el layout horizontal
#         lay_conn.addWidget(self.btn_connect)
#         layout.addWidget(grp_conn)

#         # self.combo_ports = QComboBox()
#         # self.btn_connect = QPushButton("Conectar")
#         # self.btn_connect.setCheckable(True) 
#         # lay_conn.addWidget(QLabel("Puerto COM:"))
#         # lay_conn.addWidget(self.combo_ports)
#         # lay_conn.addWidget(self.btn_connect)
#         # layout.addWidget(grp_conn)
        
#         # B. Telemetría (LCDs)
#         grp_pos = QGroupBox("Posición Actual")
#         lay_pos = QGridLayout(grp_pos)
        
#         self.lcd_x = QLCDNumber()
#         self.lcd_y = QLCDNumber()
#         self.lcd_z = QLCDNumber()
#         # Estilo "Flat" para LCDs
#         for lcd in [self.lcd_x, self.lcd_y, self.lcd_z]:
#             lcd.setDigitCount(4)
#             lcd.setSegmentStyle(QLCDNumber.Flat)

#         lay_pos.addWidget(QLabel("X:"), 0, 0); lay_pos.addWidget(self.lcd_x, 0, 1)
#         lay_pos.addWidget(QLabel("Y:"), 1, 0); lay_pos.addWidget(self.lcd_y, 1, 1)
#         lay_pos.addWidget(QLabel("Z:"), 2, 0); lay_pos.addWidget(self.lcd_z, 2, 1)
#         layout.addWidget(grp_pos)

#         # C. Sensores y Garra
#         grp_sens = QGroupBox("Sensores")
#         lay_sens = QHBoxLayout(grp_sens)
        
#         # Simulamos LEDs con Labels redondos
#         self.led_x = QLabel("X"); self.led_x.setAlignment(Qt.AlignCenter)
#         self.led_y = QLabel("Y"); self.led_y.setAlignment(Qt.AlignCenter)
#         self.led_z = QLabel("Z"); self.led_z.setAlignment(Qt.AlignCenter)
        
#         # --- AGREGAR ESTAS LINEAS PARA FORZAR TAMAÑO VISIBLE ---
#         self.led_x.setFixedSize(30, 30)
#         self.led_y.setFixedSize(30, 30)
#         self.led_z.setFixedSize(30, 30)
#         # -------------------------------------------------------
        
#         # Asignar nombres de objeto para CSS ID
#         self.led_x.setObjectName("sensor_led_off")
#         self.led_y.setObjectName("sensor_led_off")
#         self.led_z.setObjectName("sensor_led_off")

#         lay_sens.addWidget(self.led_x)
#         lay_sens.addWidget(self.led_y)
#         lay_sens.addWidget(self.led_z)
#         layout.addWidget(grp_sens)

#         # --- D. NUEVO: INDICADORES DE SISTEMA (HOME, WAIT, FINISH) ---
#         grp_sys = QGroupBox("Sistema")
#         lay_sys = QVBoxLayout(grp_sys)
        
#         # Creamos las 3 etiquetas
#         self.lbl_status_home = QLabel("HOME")
#         self.lbl_status_wait = QLabel("WAIT / BUSY")
#         self.lbl_status_finish = QLabel("FINISH")
        
#         # Estado inicial: Apagado (Clase definida en CSS)
#         self.lbl_status_home.setProperty("class", "status_badge_off")
#         self.lbl_status_wait.setProperty("class", "status_badge_off")
#         self.lbl_status_finish.setProperty("class", "status_badge_off")
        
#         lay_sys.addWidget(self.lbl_status_home)
#         lay_sys.addWidget(self.lbl_status_wait)
#         lay_sys.addWidget(self.lbl_status_finish)
        
#         layout.addWidget(grp_sys)
#         # -------------------------------------------------------------

#         # E. STOP
#         self.btn_estop = QPushButton("STOP EMERGENCIA")
#         self.btn_estop.setProperty("class", "stop_button") # Para CSS
#         self.btn_estop.setMinimumHeight(64)
#         self.set_btn_icon(self.btn_estop, "alert.png") 
#         # self.btn_estop.setIconSize(QSize(32, 32)) # Icono más grande
#         layout.addWidget(self.btn_estop)
        
#         layout.addStretch() # Empujar todo arriba
#         return panel

#     # ==========================================
#     #   2. PANEL CENTRAL: PESTAÑAS
#     # ==========================================
#     def setup_central_tabs(self):
#         tabs = QTabWidget()
        
#         # Crear las 3 pestañas
#         self.tab_calib = QWidget()
#         self.setup_tab_calibration(self.tab_calib)
        
#         self.tab_teach = QWidget()
#         self.setup_tab_teaching(self.tab_teach)
        
#         self.tab_run = QWidget()
#         self.setup_tab_execution(self.tab_run)
        
#         tabs.addTab(self.tab_calib, "CALIBRACIÓN")
#         tabs.addTab(self.tab_teach, "APRENDIZAJE")
#         tabs.addTab(self.tab_run, "EJECUCIÓN")
        
#         return tabs

#     def setup_tab_calibration(self, parent):
#         layout = QVBoxLayout(parent)
        
#         # 1. Homing
#         grp_home = QGroupBox("Inicialización")
#         lay_home = QHBoxLayout(grp_home)
#         self.btn_home = QPushButton("HOME ALL (:-H)")
#         self.set_btn_icon(self.btn_home, "home.png")
#         # self.btn_home.setFixedWidth(50)
#         self.btn_home.setToolTip("Ejecutar comando Home, para inicializar posiciones de referencia.") # Ayuda visual

#         self.btn_setzero = QPushButton("Set Zero Here (:-Z)")
#         self.set_btn_icon(self.btn_setzero, "zero.png")
#         # self.btn_setzero.setFixedWidth(50)
#         self.btn_setzero.setToolTip("Setear nuevo Zero Home en posición actual.") # Ayuda visual

#         lay_home.addWidget(self.btn_home)
#         lay_home.addWidget(self.btn_setzero)
#         layout.addWidget(grp_home)
        
#         # 2. Config Garra
#         grp_grip = QGroupBox("Configuración de Garra")
#         lay_grip = QGridLayout(grp_grip)
        
#         self.input_angle_open = QLineEdit("90")
#         self.btn_set_open = QPushButton("Set Apertura (:-A)")
#         self.set_btn_icon(self.btn_set_open, "open.png")
#         # self.btn_set_open.setFixedWidth(30)
#         self.btn_set_open.setToolTip("Setear apertura de garra.") # Ayuda visual
        
#         self.input_angle_close = QLineEdit("0")
#         self.btn_set_close = QPushButton("Set Cierre (:-P)")
#         self.set_btn_icon(self.btn_set_close, "close.png")
#         # self.btn_set_close.setFixedWidth(30)
#         self.btn_set_close.setToolTip("Setear cierre de garra.") # Ayuda visual
        
#         lay_grip.addWidget(QLabel("Ángulo Abierto:"), 0, 0)
#         lay_grip.addWidget(self.input_angle_open, 0, 1)
#         lay_grip.addWidget(self.btn_set_open, 0, 2)
        
#         lay_grip.addWidget(QLabel("Ángulo Cerrado:"), 1, 0)
#         lay_grip.addWidget(self.input_angle_close, 1, 1)
#         lay_grip.addWidget(self.btn_set_close, 1, 2)
#         layout.addWidget(grp_grip)
        
#         # 3. Enable
#         self.chk_enable = QCheckBox("Habilitar Motores (Enable)")
#         self.chk_enable.setChecked(True)
#         layout.addWidget(self.chk_enable)
        
#         layout.addStretch()

#     def setup_tab_teaching(self, parent):
#         layout = QHBoxLayout(parent)

#         # Columna Izq: Jogging
#         col_jog = QVBoxLayout()
#         grp_jog = QGroupBox("Control Manual (Jogging)")
#         grid_jog = QGridLayout(grp_jog)
        
#         # Botones Jog
#         self.btn_x_plus = QPushButton("X+")
#         self.set_btn_icon(self.btn_x_plus, "x+.png")
#         self.btn_x_plus.setMinimumHeight(64)
#         self.btn_x_plus.setToolTip("Incrementar posición X.") # Ayuda visual
#         self.btn_x_minus = QPushButton("X-")
#         self.set_btn_icon(self.btn_x_minus, "x-.png")
#         self.btn_x_minus.setMinimumHeight(64)
#         self.btn_x_minus.setToolTip("Reducir posición X.") # Ayuda visual
#         self.btn_y_plus = QPushButton("Y+")
#         self.set_btn_icon(self.btn_y_plus, "y+.png")
#         self.btn_y_plus.setMinimumHeight(64)
#         self.btn_y_plus.setToolTip("Incrementar posición X.") # Ayuda visual
#         self.btn_y_minus = QPushButton("Y-")
#         self.set_btn_icon(self.btn_y_minus, "y-.png")
#         self.btn_y_minus.setMinimumHeight(64)
#         self.btn_y_minus.setToolTip("Reducir posición Y.") # Ayuda visual
        
#         # NUEVO: Botón Central Hxy (Ir a X0 Y0)
#         self.btn_home_xy = QPushButton("Hxy")
#         self.set_btn_icon(self.btn_home_xy, "homexy.png")
#         self.btn_home_xy.setMinimumHeight(64)
#         self.btn_home_xy.setToolTip("Mandar a home los motores X e Y.") # Ayuda visual
#         self.btn_home_xy.setStyleSheet("background-color: #00bcd4; color: black; font-weight: bold;")
        
        
#         self.btn_z_plus = QPushButton("Z+")
#         self.set_btn_icon(self.btn_z_plus, "z+.png")
#         self.btn_z_plus.setMinimumHeight(64)
#         self.btn_z_plus.setToolTip("Incrementar posición Z.") # Ayuda visual
#         self.btn_z_minus = QPushButton("Z-")
#         self.set_btn_icon(self.btn_z_minus, "z-.png")
#         self.btn_z_minus.setMinimumHeight(64)
#         self.btn_z_minus.setToolTip("Reducir posición Z.") # Ayuda visual
        
#         # NUEVO: Botón Central Hz (Ir a Z0)
#         self.btn_home_z = QPushButton("Hz")
#         self.set_btn_icon(self.btn_home_z, "homez.png")
#         # self.btn_home_z.setMinimumHeight(64)
#         self.btn_home_z.setToolTip("Mandar a home al motor Z.") # Ayuda visual
#         self.btn_home_z.setStyleSheet("background-color: #00bcd4; color: black; font-weight: bold;")

#         # Grilla X/Y
#         grid_jog.addWidget(self.btn_y_plus, 0, 1)
#         grid_jog.addWidget(self.btn_x_minus, 1, 0)
#         grid_jog.addWidget(self.btn_home_xy, 1, 1) # <--- AQUÍ ESTÁ EL CENTRO
#         grid_jog.addWidget(self.btn_x_plus, 1, 2)
#         grid_jog.addWidget(self.btn_y_minus, 2, 1)
        
#         # GRUPO VELOCIDAD
#         grp_speed = QGroupBox("Velocidad de Movimiento (%)")
#         lay_speed = QHBoxLayout(grp_speed)
        
#         self.slider_speed = QSlider(Qt.Horizontal)
#         self.slider_speed.setMinimum(10)
#         self.slider_speed.setMaximum(100)
#         self.slider_speed.setValue(50) # Valor inicial
#         self.slider_speed.setTickPosition(QSlider.TicksBelow)
#         self.slider_speed.setTickInterval(10)
        
#         self.lbl_speed_val = QLabel("50%")
#         self.lbl_speed_val.setFixedWidth(35)
        
#         lay_speed.addWidget(self.slider_speed)
#         lay_speed.addWidget(self.lbl_speed_val)
        
#         # Agregar este grupo a la columna izquierda (col_jog)
#         col_jog.addWidget(grp_speed)
        
        
#         # Separador y Columna Z
#         grid_jog.addWidget(QLabel("   |   "), 1, 3) 
#         grid_jog.addWidget(self.btn_z_plus, 0, 4)
#         grid_jog.addWidget(self.btn_home_z, 1, 4) # <--- AQUÍ EN MEDIO DE Z
#         grid_jog.addWidget(self.btn_z_minus, 2, 4)
        
#         col_jog.addWidget(grp_jog)
        
#         # Pasos (Modificado a Grados)
#         grp_step = QGroupBox("Incremento (Grados)")
#         lay_step = QHBoxLayout(grp_step)
        
#         self.radio_1deg = QRadioButton("1°")
#         self.radio_10deg = QRadioButton("10°")
#         self.radio_50deg = QRadioButton("50°")
#         self.radio_10deg.setChecked(True) # Default
        
#         self.step_group = QButtonGroup()
#         self.step_group.addButton(self.radio_1deg, 1)
#         self.step_group.addButton(self.radio_10deg, 10)
#         self.step_group.addButton(self.radio_50deg, 50)
        
#         lay_step.addWidget(self.radio_1deg)
#         lay_step.addWidget(self.radio_10deg)
#         lay_step.addWidget(self.radio_50deg)
#         col_jog.addWidget(grp_step)
        
#         # Garra Manual
#         grp_man_grip = QGroupBox("Garra")
#         lay_man_grip = QHBoxLayout(grp_man_grip)
#         self.btn_open_grip = QPushButton("Abrir")
#         self.set_btn_icon(self.btn_open_grip, "open.png")
#         # self.btn_open_grip.setFixedWidth(30)
#         self.btn_open_grip.setToolTip("Abrir garra según ángulo seteado.") # Ayuda visual
#         self.btn_close_grip = QPushButton("Cerrar")
#         self.set_btn_icon(self.btn_close_grip, "close.png")
#         # self.btn_close_grip.setFixedWidth(30)
#         self.btn_close_grip.setToolTip("Cerrar garra según ángulo seteado.") # Ayuda visual
#         lay_man_grip.addWidget(self.btn_open_grip)
#         lay_man_grip.addWidget(self.btn_close_grip)
#         col_jog.addWidget(grp_man_grip)
        
#         col_jog.addStretch()
        
#         # Columna Der: Tabla de Puntos
#         col_list = QVBoxLayout()
#         self.table_points = QTableWidget()
#         self.table_points.setColumnCount(4)
#         self.table_points.setHorizontalHeaderLabels(["X", "Y", "Z", "G"])
#         self.table_points.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
#         col_list.addWidget(QLabel("Rutina Actual:"))
#         col_list.addWidget(self.table_points)
        
#         lay_btns_list = QHBoxLayout()
#         self.btn_add_point = QPushButton("Guardar Punto Actual")
#         self.set_btn_icon(self.btn_add_point, "add.png")
#         # self.btn_add_point.setFixedWidth(30)
#         self.btn_add_point.setToolTip("Agregar punto actual a la lista de posiciones para la rutina.") # Ayuda visual

#         self.btn_del_point = QPushButton("Borrar Seleccionado")
#         self.set_btn_icon(self.btn_del_point, "clear.png")
#         # self.btn_del_point.setFixedWidth(30)
#         self.btn_del_point.setToolTip("Borrar fila de posición seleccionada.") # Ayuda visual
        
#         # --- NUEVO BOTÓN: BORRAR TODO ---
#         self.btn_clear_all = QPushButton("Limpiar Todo")
#         self.set_btn_icon(self.btn_clear_all, "clean.png")
#         # self.btn_clear_all.setFixedWidth(30)
#         self.btn_clear_all.setToolTip("Borrar todas las posiciones cargadas en el panel.") # Ayuda visual
#         self.btn_clear_all.setStyleSheet("background-color: #d32f2f; font-weight: bold;") # Rojo oscuro
        
#         self.btn_save_file = QPushButton("Guardar Rutina JSON")
#         self.set_btn_icon(self.btn_save_file, "save.png")
#         # self.btn_save_file.setFixedWidth(30)
#         self.btn_save_file.setToolTip("Guardar conjunto de posiciones en una rutina con formato JSON.") # Ayuda visual
        
#         lay_btns_list.addWidget(self.btn_add_point)
#         lay_btns_list.addWidget(self.btn_del_point)
#         lay_btns_list.addWidget(self.btn_clear_all) 
#         lay_btns_list.addWidget(self.btn_save_file)
#         col_list.addLayout(lay_btns_list)
        
#         layout.addLayout(col_jog, 1)
#         layout.addLayout(col_list, 2)

#     def setup_tab_execution(self, parent):
#         layout = QVBoxLayout(parent)
        
#         # Archivo
#         lay_file = QHBoxLayout()
#         self.lbl_file = QLabel("Archivo: Ninguno cargado")
#         self.btn_load_file = QPushButton("Cargar Rutina")
#         self.set_btn_icon(self.btn_load_file, "load.png")
#         # self.btn_load_file.setFixedWidth(30)
#         self.btn_load_file.setToolTip("Cargar archivo de rutina en formato JSON.") # Ayuda visual
        
#         # --- NUEVO BOTÓN: PREVISUALIZAR ---
#         self.btn_preview = QPushButton("Ver Contenido")
#         self.set_btn_icon(self.btn_preview, "read.png")
#         # self.btn_preview.setFixedWidth(30)
#         self.btn_preview.setToolTip("Ver contenido del archivo JSON cargado.") # Ayuda visual
#         self.btn_preview.setStyleSheet("background-color: #FF9800; color: black;") # Naranja
        
#         lay_file.addWidget(self.lbl_file)
#         lay_file.addWidget(self.btn_load_file)
#         lay_file.addWidget(self.btn_preview) # <--- Agregarlo al layout
#         layout.addLayout(lay_file)
        
#         # Progreso
#         self.progress_bar = QProgressBar()
#         layout.addWidget(self.progress_bar)
        
#         # Controles
#         lay_ctrl = QHBoxLayout()
#         self.btn_play = QPushButton("PLAY")
#         self.set_btn_icon(self.btn_play, "play.png")
#         # self.btn_play.setFixedWidth(30)
#         self.btn_play.setToolTip("Ejecutar rutina seleccionada y cargada.") # Ayuda visual
#         self.btn_pause = QPushButton("PAUSA")
#         self.set_btn_icon(self.btn_pause, "pause.png")
#         # self.btn_pause.setFixedWidth(30)
#         self.btn_pause.setToolTip("Pausar rutina que se está ejecutando.") # Ayuda visual
#         self.btn_stop_run = QPushButton("DETENER")
#         self.set_btn_icon(self.btn_stop_run, "stop.png")
#         # self.btn_stop_run.setFixedWidth(30)
#         self.btn_stop_run.setToolTip("Detener rutina que se ejecuta actualmente.") # Ayuda visual
        
#         # Estilos botones play
#         self.btn_play.setStyleSheet("background-color: #2e7d32; font-weight: bold;") # Verde
#         self.btn_stop_run.setStyleSheet("background-color: #c62828; font-weight: bold;") # Rojo
        
#         lay_ctrl.addWidget(self.btn_play)
#         lay_ctrl.addWidget(self.btn_pause)
#         lay_ctrl.addWidget(self.btn_stop_run)
#         layout.addLayout(lay_ctrl)
        
#         # Log de ejecución grande
#         self.txt_run_log = QTextEdit()
#         self.txt_run_log.setReadOnly(True)
#         self.txt_run_log.setPlaceholderText("Detalles de ejecución aparecerán aquí...")
#         layout.addWidget(self.txt_run_log)

#     # ==========================================
#     #   3. CONSOLA INFERIOR
#     # ==========================================
#     def setup_bottom_console(self):
#         container = QWidget()
#         layout = QVBoxLayout(container)
#         layout.setContentsMargins(0, 0, 0, 0)
        
#         self.txt_console = QTextEdit()
#         self.txt_console.setReadOnly(True)
#         self.txt_console.setMaximumHeight(150)
#         self.txt_console.setStyleSheet("font-family: Consolas; font-size: 11px; background-color: #111; color: #0f0;")
        
#         lay_input = QHBoxLayout()
#         self.input_console = QLineEdit()
#         self.input_console.setPlaceholderText("Escribe un comando manual (ej: :-H, :#X100)...")
#         self.input_console.setMinimumHeight(64)
#         self.btn_send_console = QPushButton("Enviar")
#         self.set_btn_icon(self.btn_send_console, "send.png")
#         self.btn_send_console.setMinimumHeight(64)
#         self.btn_send_console.setToolTip("Enviar comando ingresado a la consola.") # Ayuda visual
#         self.btn_clear_console = QPushButton("Limpiar")
#         self.set_btn_icon(self.btn_clear_console, "erase.png")
#         self.btn_clear_console.setMinimumHeight(164)
#         self.btn_clear_console.setToolTip("Limpiar la consola de comandos.") # Ayuda visual
        
#         lay_input.addWidget(QLabel(">_"))
#         lay_input.addWidget(self.input_console)
#         lay_input.addWidget(self.btn_send_console)
#         lay_input.addWidget(self.btn_clear_console)
        
#         layout.addWidget(self.txt_console)
#         layout.addLayout(lay_input)
        
#         return container
    
#     def toggle_kawaii_mode(self, state):
#         """Activa o desactiva todos los iconos de la interfaz"""

#         self.is_kawaii = state
        
#         # Recorremos todos los botones que guardamos en la memoria
#         for item, config in self.icon_registry.items():
#             if self.is_kawaii:
#                 # Restaurar icono
#                 path = os.path.join("resources", config["name"])
#                 if os.path.exists(path):
#                     item.setIcon(QIcon(path))
#                     if hasattr(item, 'setIconSize'):
#                         item.setIconSize(QSize(config["size"], config["size"]))
#             else:
#                 # Borrar icono (ponemos un QIcon vacío)
#                 item.setIcon(QIcon())