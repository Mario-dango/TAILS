"""
VISTA PRINCIPAL (Main Window)
Ensambla todos los sub-paneles (LeftPanel, ConsolePanel y las Pestañas).
Actúa como fachada para que el Controlador acceda fácilmente a los botones,
y gestiona globalmente los iconos (Modo Kawaii) y la hoja de estilos.
"""

from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import os

# Importamos nuestros módulos visuales recién creados
from view.left_panel import LeftPanel
from view.console_panel import ConsolePanel
from view.tab_calibration import CalibrationTab
from view.tab_teaching import TeachingTab
from view.tab_execution import ExecutionTab

class View(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Technical Articulated Intelligent Linkage System (T.A.I.L.S.)")
        self.resize(1100, 750) 
        
        # Modo Kawaii
        self.is_kawaii = True          
        self.icon_registry = {}        

        # Icono de la ventana principal
        ruta_icono = os.path.join("images/icons", "TAILS_icono.png") 
        if os.path.exists(ruta_icono):
            self.setWindowIcon(QIcon(ruta_icono))

        # 1. Menú superior
        self.setup_menu_bar()

        # 2. Ensamblar la Interfaz
        self.setup_ui_structure()
        
        # 3. Exponer los botones al Controlador (Patrón Fachada)
        self.expose_widgets_to_controller()

        # 4. Asignar los iconos centralizados
        self.assign_all_icons()
        
        # 5. Cargar CSS
        self.set_stylesheet()

    def setup_ui_structure(self):
        """Crea el layout principal y acomoda los paneles importados"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        # --- Mitad Superior ---
        top_section = QWidget()
        top_layout = QHBoxLayout(top_section)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Instanciamos los sub-paneles
        self.panel_left = LeftPanel()
        
        self.tabs = QTabWidget()
        self.tab_calib = CalibrationTab()
        self.tab_teach = TeachingTab()
        self.tab_run = ExecutionTab()
        
        self.tabs.addTab(self.tab_calib, "CALIBRACIÓN")
        self.tabs.addTab(self.tab_teach, "APRENDIZAJE")
        self.tabs.addTab(self.tab_run, "EJECUCIÓN")
        
        top_layout.addWidget(self.panel_left, 1) # 25% ancho
        top_layout.addWidget(self.tabs, 3)       # 75% ancho
        
        self.main_layout.addWidget(top_section)

        # --- Mitad Inferior (Consola) ---
        self.console_container = ConsolePanel()
        
        self.btn_toggle_console = QPushButton("Mostrar/Ocultar Terminal de Comandos")
        self.btn_toggle_console.setCheckable(True)
        self.btn_toggle_console.setChecked(True)
        self.btn_toggle_console.setFixedHeight(35) # Barra sutil
        self.btn_toggle_console.clicked.connect(self.toggle_console)
        
        self.main_layout.addWidget(self.btn_toggle_console)
        self.main_layout.addWidget(self.console_container)

    def expose_widgets_to_controller(self):
        """
        ¡MAGIA NEGRA! Aquí vinculamos los componentes internos de los paneles 
        como atributos directos de View. Así, el Controller no necesita saber 
        que dividimos los archivos y puede seguir usando 'self.view.btn_home'.
        """
        # Panel Izquierdo
        self.btn_refresh = self.panel_left.btn_refresh
        self.combo_ports = self.panel_left.combo_ports
        self.btn_connect = self.panel_left.btn_connect
        self.lcd_x = self.panel_left.lcd_x
        self.lcd_y = self.panel_left.lcd_y
        self.lcd_z = self.panel_left.lcd_z
        self.led_x = self.panel_left.led_x
        self.led_y = self.panel_left.led_y
        self.led_z = self.panel_left.led_z
        self.lbl_status_home = self.panel_left.lbl_status_home
        self.lbl_status_wait = self.panel_left.lbl_status_wait
        self.lbl_status_finish = self.panel_left.lbl_status_finish
        self.btn_estop = self.panel_left.btn_estop

        # Consola (Renombramos los botones internos para que coincidan con el Controlador)
        self.txt_console = self.console_container.txt_console
        self.input_console = self.console_container.input_console
        self.btn_send_console = self.console_container.btn_send
        self.btn_clear_console = self.console_container.btn_clear

        # Pestaña 1: Calibración
        self.btn_home = self.tab_calib.btn_home
        self.btn_setzero = self.tab_calib.btn_setzero
        self.input_angle_open = self.tab_calib.input_angle_open
        self.btn_set_open = self.tab_calib.btn_set_open
        self.input_angle_close = self.tab_calib.input_angle_close
        self.btn_set_close = self.tab_calib.btn_set_close
        self.chk_enable = self.tab_calib.chk_enable

        # Pestaña 2: Aprendizaje
        self.btn_x_plus = self.tab_teach.btn_x_plus
        self.btn_x_minus = self.tab_teach.btn_x_minus
        self.btn_y_plus = self.tab_teach.btn_y_plus
        self.btn_y_minus = self.tab_teach.btn_y_minus
        self.btn_z_plus = self.tab_teach.btn_z_plus
        self.btn_z_minus = self.tab_teach.btn_z_minus
        self.btn_home_xy = self.tab_teach.btn_home_xy
        self.btn_home_z = self.tab_teach.btn_home_z
        self.slider_speed = self.tab_teach.slider_speed
        self.lbl_speed_val = self.tab_teach.lbl_speed_val
        self.step_group = self.tab_teach.step_group
        self.btn_open_grip = self.tab_teach.btn_open_grip
        self.btn_close_grip = self.tab_teach.btn_close_grip
        self.table_points = self.tab_teach.table_points
        self.btn_add_point = self.tab_teach.btn_add_point
        self.btn_del_point = self.tab_teach.btn_del_point
        self.btn_clear_all = self.tab_teach.btn_clear_all
        self.btn_save_file = self.tab_teach.btn_save_file

        # Pestaña 3: Ejecución
        self.lbl_file = self.tab_run.lbl_file
        self.btn_load_file = self.tab_run.btn_load_file
        self.btn_preview = self.tab_run.btn_preview
        self.progress_bar = self.tab_run.progress_bar
        self.btn_play = self.tab_run.btn_play
        self.btn_pause = self.tab_run.btn_pause
        self.btn_stop_run = self.tab_run.btn_stop_run
        self.txt_run_log = self.tab_run.txt_run_log

    def assign_all_icons(self):
        """Asigna los gráficos a cada botón expuesto para alimentar el Modo Kawaii"""
        # Menú y UI base
        self.set_btn_icon(self.action_manual, "help.png", size=64)
        self.set_btn_icon(self.action_kawaii, "kawaii.png", size=64)
        self.set_btn_icon(self.action_about, "TAILS_icono.png", size=64)
        self.set_btn_icon(self.btn_toggle_console, "showHide.png", size=64)
        
        # Panel Izquierdo
        self.set_btn_icon(self.btn_refresh, "refresh.png", size=64)
        self.set_btn_icon(self.btn_connect, "plug.png", size=64)
        self.set_btn_icon(self.btn_estop, "alert.png", size=64)
        
        # Consola
        self.set_btn_icon(self.btn_send_console, "send.png", size=64)
        self.set_btn_icon(self.btn_clear_console, "erase.png", size=64)
        
        # Calibración
        self.set_btn_icon(self.btn_home, "home.png", size=64)
        self.set_btn_icon(self.btn_setzero, "zero.png", size=64)
        self.set_btn_icon(self.btn_set_open, "open.png", size=64)
        self.set_btn_icon(self.btn_set_close, "close.png", size=64)

        # Aprendizaje
        self.set_btn_icon(self.btn_x_plus, "x+.png", size=64)
        self.set_btn_icon(self.btn_x_minus, "x-.png", size=64)
        self.set_btn_icon(self.btn_y_plus, "y+.png", size=64)
        self.set_btn_icon(self.btn_y_minus, "y-.png", size=64)
        self.set_btn_icon(self.btn_z_plus, "z+.png", size=64)
        self.set_btn_icon(self.btn_z_minus, "z-.png", size=64)
        self.set_btn_icon(self.btn_home_xy, "homexy.png", size=64)
        self.set_btn_icon(self.btn_home_z, "homez.png", size=64)
        self.set_btn_icon(self.btn_open_grip, "open.png", size=64)
        self.set_btn_icon(self.btn_close_grip, "close.png", size=64)
        
        self.set_btn_icon(self.btn_add_point, "add.png", size=64)
        self.set_btn_icon(self.btn_del_point, "clear.png", size=64)
        self.set_btn_icon(self.btn_clear_all, "clean.png", size=64)
        self.set_btn_icon(self.btn_save_file, "save.png", size=64)

        # Ejecución
        self.set_btn_icon(self.btn_load_file, "load.png", size=64)
        self.set_btn_icon(self.btn_preview, "read.png", size=64)
        self.set_btn_icon(self.btn_play, "play.png", size=64)
        self.set_btn_icon(self.btn_pause, "pause.png", size=64)
        self.set_btn_icon(self.btn_stop_run, "stop.png", size=64)

    def setup_menu_bar(self):
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("Ayuda")
        
        self.action_manual = help_menu.addAction("Manual de Usuario")
        self.action_kawaii = help_menu.addAction("Modo Kawaii (Iconos)")
        self.action_kawaii.setCheckable(True) 
        self.action_kawaii.setChecked(True)   
        
        help_menu.addSeparator() 
        self.action_about = help_menu.addAction("Acerca de T.A.I.L.S.")

    def set_btn_icon(self, item, icon_name, size=64):
        self.icon_registry[item] = {"name": icon_name, "size": size}
        
        if self.is_kawaii:
            path = os.path.join("images/icons", icon_name)
            if os.path.exists(path):
                item.setIcon(QIcon(path))
                if hasattr(item, 'setIconSize'):
                    item.setIconSize(QSize(size, size))
            else:
                print(f"Advertencia: No se encontró icono {icon_name}")

    def toggle_kawaii_mode(self, state):
        self.is_kawaii = state
        for item, config in self.icon_registry.items():
            if self.is_kawaii:
                path = os.path.join("images/icons", config["name"])
                if os.path.exists(path):
                    item.setIcon(QIcon(path))
                    if hasattr(item, 'setIconSize'):
                        item.setIconSize(QSize(config["size"], config["size"]))
            else:
                item.setIcon(QIcon())

    def toggle_console(self):
        is_visible = self.btn_toggle_console.isChecked()
        self.console_container.setVisible(is_visible)

    def set_stylesheet(self):
        try:
            with open("style.css", "r", encoding='utf-8') as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            print("Archivo style.css no encontrado")