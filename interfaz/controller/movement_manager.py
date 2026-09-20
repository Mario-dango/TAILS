"""
MOVEMENT MANAGER (Gestor de Movimiento)
Se encarga de la lógica cinemática: Jogging manual, Homing, 
control de la garra, velocidad y parada de emergencia.
"""

from PyQt5.QtWidgets import QMessageBox

# Recorrido real de cada eje, en pasos. Es la misma fuente de verdad que usa la
# validación de la tabla de rutina y el visualizador del panel izquierdo.
from view.ui_widgets import RANGO_X, RANGO_Y, RANGO_Z

# Tope de cada eje para el jogging. El final de carrera sólo protege el extremo
# de HOME: del otro lado no había nada, ni acá ni en el firmware, y el brazo
# seguía de largo pasándose de X=580 / Y=130 / Z=60.
TOPES_EJE = {'x': RANGO_X, 'y': RANGO_Y, 'z': RANGO_Z}


class MovementManager:
    def __init__(self, main_controller):
        self.app = main_controller
        self.view = main_controller.view
        self.model = main_controller.model

        self.init_connections()

    def init_connections(self):
        """Conecta los botones de la pestaña Calibración y Aprendizaje"""
        
        # --- CALIBRACIÓN ---
        self.view.btn_home.clicked.connect(self.handle_home)
        self.view.btn_setzero.clicked.connect(self.handle_set_zero)
        self.view.chk_enable.toggled.connect(self.handle_enable_motor)
        
        # --- CONFIG GARRA (Ángulos) ---
        # Usamos lambdas para capturar el texto de los inputs al momento del click
        self.view.btn_set_open.clicked.connect(
            lambda: self.send_cmd(f":-A{self.view.input_angle_open.text()}")
        )
        self.view.btn_set_close.clicked.connect(
            lambda: self.send_cmd(f":-P{self.view.input_angle_close.text()}")
        )

        # --- JOGGING (Movimiento Manual) ---
        # Conectamos cada flecha a la función genérica handle_jog
        self.view.btn_x_plus.clicked.connect(lambda: self.handle_jog('x', 1))
        self.view.btn_x_minus.clicked.connect(lambda: self.handle_jog('x', -1))
        self.view.btn_y_plus.clicked.connect(lambda: self.handle_jog('y', 1))
        self.view.btn_y_minus.clicked.connect(lambda: self.handle_jog('y', -1))
        self.view.btn_z_plus.clicked.connect(lambda: self.handle_jog('z', 1))
        self.view.btn_z_minus.clicked.connect(lambda: self.handle_jog('z', -1))
        
        # Movimientos Rápidos a Cero (Home Parcial)
        self.view.btn_home_xy.clicked.connect(self.handle_go_zero_xy)
        self.view.btn_home_z.clicked.connect(self.handle_go_zero_z)

        # --- CONTROL MANUAL GARRA ---
        self.view.btn_open_grip.clicked.connect(lambda: self.handle_gripper('A'))
        self.view.btn_close_grip.clicked.connect(lambda: self.handle_gripper('C'))

        # --- VELOCIDAD ---
        self.view.slider_speed.valueChanged.connect(self.handle_speed_change)
        self.view.slider_speed.sliderReleased.connect(self.send_speed_command)

        # --- STOP EMERGENCIA / REARMAR ---
        self.view.btn_estop.clicked.connect(self.emergency_stop)
        self.view.btn_rearm.clicked.connect(self.rearm)

    # --- FUNCIONES HELPER ---
    def send_cmd(self, cmd):
        """Atajo para enviar comandos usando el ConnectionManager del jefe"""
        # Verificamos si el connection_mgr ya existe (podría no estar inicializado al arrancar)
        if hasattr(self.app, 'connection_mgr'):
            self.app.connection_mgr.send_command(cmd)
        else:
            print("Error: ConnectionManager no disponible")

    def log(self, prefix, msg):
        """Atajo para loguear en consola"""
        if hasattr(self.app, 'connection_mgr'):
            self.app.connection_mgr.log_console(prefix, msg)

    # --- LÓGICA DE MOVIMIENTO ---
    def handle_jog(self, axis, direction):
        if not self.model.is_connected():
            self.log("ERROR", "Conecta el robot primero.")
            return

        # 1. Obtener incremento seleccionado en la UI (1, 10 o 50 PASOS)
        step_pasos = self.view.step_group.checkedId()

        # 2. Calcular nueva posición basada en la memoria global del Jefe
        current_val = self.app.current_pos[axis]
        tope = TOPES_EJE[axis]
        new_val = current_val + (step_pasos * direction)

        # LÍMITES ARTICULARES: acotamos a [0, tope]. Si ya estábamos en el
        # extremo no reenviamos el mismo comando —sólo avisamos—: repetir un
        # destino ya alcanzado no mueve nada y ensucia la consola.
        new_val = max(0, min(tope, new_val))
        if new_val == current_val:
            extremo = "tope" if direction > 0 else "cero"
            self.log("WARN", "Eje %s ya está en su %s (%d pasos)."
                     % (axis.upper(), extremo, current_val))
            return

        # 3. Actualizar registro interno global
        self.app.current_pos[axis] = new_val
        
        # 4. Enviar Comando (Ej: :#X100)
        cmd = f":#{axis.upper()}{new_val}"
        self.send_cmd(cmd)
        
        # 5. Actualizar los números en pantalla
        self.update_lcds()

    def handle_go_zero_xy(self):
        """Manda X e Y a 0"""
        self.send_cmd(":#X0Y0")
        self.app.current_pos['x'] = 0
        self.app.current_pos['y'] = 0
        self.update_lcds()
        self.log("INFO", "Moviendo a X0 Y0...")

    def handle_go_zero_z(self):
        """Manda Z a 0"""
        self.send_cmd(":#Z0")
        self.app.current_pos['z'] = 0
        self.update_lcds()
        self.log("INFO", "Moviendo a Z0...")

    def handle_gripper(self, action):
        """Abre o cierra la garra (action = 'A' o 'C')"""
        self.app.gripper_state = action
        cmd = f":#{action}" 
        self.send_cmd(cmd)

    def handle_home(self):
        """Ejecuta la secuencia de Homing físico"""
        self.send_cmd(":-H")
        # Al hacer home, reiniciamos las coordenadas lógicas a 0
        self.app.current_pos = {'x': 0, 'y': 0, 'z': 0}
        self.update_lcds()

    def handle_set_zero(self):
        """Define la posición actual como el nuevo 0 (Zero offset)"""
        self.send_cmd(":-Z")
        self.app.current_pos = {'x': 0, 'y': 0, 'z': 0}
        self.update_lcds()

    def handle_enable_motor(self, checked):
        """Activa o desactiva el par de los motores"""
        self.send_cmd(":-E1" if checked else ":-E0")

    def emergency_stop(self):
        """Envía comando de parada prioritaria"""
        if self.model.is_connected():
            self.send_cmd(":-S")
            self.log("ALERTA", "STOP ENVIADO")
        else:
            self.log("ERROR", "Robot no conectado (STOP fallido).")

    def rearm(self):
        """Libera el bloqueo de parada de emergencia (envía :-R)"""
        if self.model.is_connected():
            self.send_cmd(":-R")
            self.log("INFO", "REARMADO (:-R). Recalibrar antes de operar.")
        else:
            self.log("ERROR", "Robot no conectado (rearme fallido).")

    # --- VELOCIDAD ---
    def handle_speed_change(self, value):
        # Solo actualiza el texto visualmente mientras arrastras el slider
        self.view.lbl_speed_val.setText(f"{value}%")

    def send_speed_command(self):
        # Se envía solo al soltar el slider para no saturar el puerto serie
        val = self.view.slider_speed.value()
        cmd = f":-V{val:03d}" # Formato de 3 dígitos (ej: 050)
        self.send_cmd(cmd)
        self.log("INFO", f"Velocidad ajustada a {val}%")

    # --- UTILIDADES VISUALES ---
    def update_lcds(self):
        """Refresca los displays numéricos con los datos de la memoria global"""
        pos = self.app.current_pos
        self.view.lcd_x.display(pos['x'])
        self.view.lcd_y.display(pos['y'])
        self.view.lcd_z.display(pos['z'])