"""
CONTROLADOR PRINCIPAL (El Orquestador)
Este archivo inicializa la aplicación y delega las tareas específicas 
a sus 4 sub-controladores (Managers).
"""

import os
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox

# Importamos las capas principales desde sus respectivas carpetas
from model.model import Model
from view.view import View

# Importaremos los Managers paso a paso (Por ahora están comentados para no dar error)
from .connection_manager import ConnectionManager
from .movement_manager import MovementManager
from .learning_manager import LearningManager
from .execution_manager import ExecutionManager

class MainController:
    def __init__(self):
        # 1. Inicializamos las capas MVC principales
        self.model = Model()
        self.view = View()

        # 2. --- ESTADO GLOBAL COMPARTIDO (Shadow Registers) ---
        # Todos los managers leerán y modificarán estas variables para saber dónde está el robot
        self.current_pos = {'x': 0, 'y': 0, 'z': 0}
        self.gripper_state = 'A' # A = Abierto, C = Cerrado

        # 3. --- GESTIÓN DE RUTAS BASE ---
        base_path = os.getcwd()
        self.routines_path = os.path.join(base_path, "rutinas")
        if not os.path.exists(self.routines_path):
            try:
                os.makedirs(self.routines_path)
            except OSError as e:
                print(f"Error creando carpeta rutinas: {e}")

        # 4. --- TIMERS GLOBALES DE INTERFAZ ---
        # Timer para efecto blink del LED Finish
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.handle_finish_blink)
        self.blink_count = 0

        # Timer para parpadeo de alerta (HOME necesario)
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.handle_home_alert_blink)
        self.alert_blink_state = False

        # 5. --- INICIALIZACIÓN DE MANAGERS ---
        # Aquí le pasamos 'self' (este controlador entero) a cada manager.
        # Así, los managers podrán acceder a app.view, app.model y app.current_pos.
        
        self.connection_mgr = ConnectionManager(self)
        self.movement_mgr = MovementManager(self)
        self.learning_mgr = LearningManager(self)
        self.execution_mgr = ExecutionManager(self)

        # 6. Conexiones generales (Ayuda y UI) que no pertenecen a ningún manager en particular
        self.init_general_ui()
        
        # Mostramos la ventana al terminar de configurar todo
        self.view.show()

    def init_general_ui(self):
        """Conecta los botones de la barra de menú superior"""
        self.view.action_manual.triggered.connect(self.show_manual)
        self.view.action_about.triggered.connect(self.show_about)
        self.view.action_kawaii.toggled.connect(self.view.toggle_kawaii_mode)

    # --- FUNCIONES DE ALERTAS VISUALES GLOBALES ---
    def handle_finish_blink(self):
        """Hace parpadear el LED de FINISH al terminar una rutina"""
        self.blink_count += 1
        if self.blink_count % 2 != 0:
            self.view.lbl_status_finish.setProperty("class", "status_badge_finish_on")
        else:
            self.view.lbl_status_finish.setProperty("class", "status_badge_off")
            
        self.view.lbl_status_finish.style().unpolish(self.view.lbl_status_finish)
        self.view.lbl_status_finish.style().polish(self.view.lbl_status_finish)
        
        if self.blink_count >= 6:
            self.blink_timer.stop()
            self.view.lbl_status_finish.setProperty("class", "status_badge_off")
            self.view.lbl_status_finish.style().unpolish(self.view.lbl_status_finish)
            self.view.lbl_status_finish.style().polish(self.view.lbl_status_finish)

    def handle_home_alert_blink(self):
        """Hace parpadear el botón HOME en rojo si el robot pierde la calibración"""
        self.alert_blink_state = not self.alert_blink_state
        if self.alert_blink_state:
            self.view.lbl_status_home.setStyleSheet("background-color: #d32f2f; color: white; border-radius: 4px; border: 1px solid #ff5252;") 
            self.view.lbl_status_home.setText("REQ. HOMING")
        else:
            self.view.lbl_status_home.setStyleSheet("background-color: #333; color: #555; border-radius: 4px; border: 1px solid #444;")
            self.view.lbl_status_home.setText("HOME")

    # --- FUNCIONES DE LA BARRA DE AYUDA ---
    def show_manual(self):
        instrucciones = (
            "<b>Guía rápida de T.A.I.L.S.</b><br><br>"
            "<b>1. Calibración:</b> Asegúrate de hacer 'Home' antes de mover el robot.<br>"
            "<b>2. Aprendizaje:</b> Usa las flechas para mover el brazo. Haz clic en 'Guardar Punto' para crear una secuencia.<br>"
            "<b>3. Ejecución:</b> Carga tu rutina guardada y presiona Play.<br><br>"
            "<i>Nota: Si el indicador de sistema dice 'REQ. HOMING', ve a la pestaña de Calibración.</i>"
        )
        QMessageBox.information(self.view, "Manual de Usuario", instrucciones)

    def show_about(self):
        about_text = (
            "<h2>T.A.I.L.S.</h2>"
            "<p><b>Technical Articulated Intelligent Linkage System</b></p>"
            "<p>Interfaz de control robótico.</p>"
            "<p>Versión 1.0</p>"
        )
        QMessageBox.about(self.view, "Acerca de", about_text)