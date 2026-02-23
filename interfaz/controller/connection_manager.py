"""
CONNECTION MANAGER (Gestor de Comunicaciones)
Se encarga exclusivamente de abrir/cerrar el puerto serie, enviar comandos
y procesar (parsear) la información que llega del microcontrolador STM32.
"""

import time
from PyQt5.QtCore import QThread, pyqtSignal

# --- Hilo Trabajador Serial (Se queda aquí porque es exclusivo de la comunicación) ---
class SerialWorker(QThread):
    data_received = pyqtSignal(str) 
    
    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.is_running = True

    def run(self):
        while self.is_running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line: self.data_received.emit(line)
            except: break
            time.sleep(0.01)
            
    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()


class ConnectionManager:
    def __init__(self, main_controller):
        # Recibe el 'MainController' (el jefe) para poder acceder a la Vista y al Modelo
        self.app = main_controller 
        self.model = main_controller.model
        self.view = main_controller.view
        self.worker = None

        self.init_connections()
        self.update_ui_connection_state(False) # Inicialmente bloquea todo porque no hay conexión
        self.refresh_ports() # Busca los puertos automáticamente al abrir el programa

    def init_connections(self):
        """Conecta los botones específicos de comunicación y consola"""
        self.view.btn_refresh.clicked.connect(self.refresh_ports)
        self.view.btn_connect.clicked.connect(self.toggle_connection)
        
        # Consola Inferior
        self.view.btn_send_console.clicked.connect(self.handle_console_send)
        self.view.input_console.returnPressed.connect(self.handle_console_send)
        self.view.btn_clear_console.clicked.connect(self.view.txt_console.clear)

    # --- LÓGICA DE CONEXIÓN ---
    def refresh_ports(self):
        current = self.view.combo_ports.currentText()
        ports = self.model.get_available_ports()
        self.view.combo_ports.clear()
        self.view.combo_ports.addItems(ports)
        if current in ports: self.view.combo_ports.setCurrentText(current)

    def toggle_connection(self):
        if self.model.is_connected():
            if self.worker: self.worker.stop(); self.worker = None
            self.model.disconnect_port()
            self.view.btn_connect.setText("Conectar"); self.view.btn_connect.setChecked(False)
            self.view.combo_ports.setEnabled(True)
            self.update_ui_connection_state(False) # BLOQUEAR INTERFAZ
            self.log_console("INFO", "Desconectado.")
        else:
            port = self.view.combo_ports.currentText()
            if not port: return
            if self.model.connect_port(port):
                self.view.btn_connect.setText("Desconectar"); self.view.btn_connect.setChecked(True)
                self.view.combo_ports.setEnabled(False)
                self.update_ui_connection_state(True) # DESBLOQUEAR INTERFAZ
                self.log_console("INFO", f"Conectado a {port}")
                
                # Inicia el hilo que escucha el puerto
                self.worker = SerialWorker(self.model.serial_port)
                self.worker.data_received.connect(self.process_serial_data)
                self.worker.start()

    # --- LÓGICA DE ENVÍO Y CONSOLA ---
    def send_command(self, cmd):
        # Cláusula de guarda de seguridad
        if not self.model.is_connected():
            self.log_console("ERROR", "No conectado.")
            print(f"DEBUG: Intento de envío en modo offline: {cmd}")
            return False

        if self.model.send_data(cmd):
            self.log_console("TX", cmd)
            return True
        return False

    def handle_console_send(self):
        cmd = self.view.input_console.text()
        if cmd: 
            self.send_command(cmd)
            self.view.input_console.clear()

    def log_console(self, prefix, message):
        """Imprime mensajes con formato de colores en la terminal inferior"""
        color = "#ffffff"
        if prefix == "TX": color = "#00aaff"
        elif prefix == "RX": color = "#00ff00"
        elif prefix == "ERROR": color = "#ff3333"
        elif prefix == "ALERTA": color = "#ffff00"
        elif prefix == "INFO": color = "#ffffff"
        self.view.txt_console.append(f'<span style="color:{color}"><b>[{prefix}]</b> {message}</span>')

    # --- BLOQUEO VISUAL POR DESCONEXIÓN ---
    def update_ui_connection_state(self, is_connected):
        """Bloquea o desbloquea los botones de toda la UI según si hay USB conectado"""
        # Pestaña de Calibración
        self.view.btn_home.setEnabled(is_connected)
        self.view.btn_setzero.setEnabled(is_connected)
        self.view.chk_enable.setEnabled(is_connected)
        self.view.btn_set_open.setEnabled(is_connected)
        self.view.btn_set_close.setEnabled(is_connected)
        
        # Pestaña de Aprendizaje 
        self.view.btn_add_point.setEnabled(is_connected)
        self.view.btn_save_file.setEnabled(is_connected)
        self.view.btn_del_point.setEnabled(is_connected)
        self.view.btn_clear_all.setEnabled(is_connected)
        
        # Jogging
        self.view.btn_home_xy.setEnabled(is_connected)
        self.view.btn_home_z.setEnabled(is_connected)
        self.view.btn_x_plus.setEnabled(is_connected)
        self.view.btn_x_minus.setEnabled(is_connected)
        self.view.btn_y_plus.setEnabled(is_connected)
        self.view.btn_y_minus.setEnabled(is_connected)
        self.view.btn_z_plus.setEnabled(is_connected)
        self.view.btn_z_minus.setEnabled(is_connected)
        self.view.btn_open_grip.setEnabled(is_connected)
        self.view.btn_close_grip.setEnabled(is_connected)
        self.view.slider_speed.setEnabled(is_connected)
    
        # Pestaña de Ejecución      
        self.view.btn_play.setEnabled(is_connected)
        self.view.btn_pause.setEnabled(is_connected)
        self.view.btn_stop_run.setEnabled(is_connected)
        
        if not is_connected:
            self.view.lbl_file.setText("Archivo: Requiere Conexión")

    # --- LÓGICA DE RECEPCIÓN (EL PARSER) ---
    def process_serial_data(self, data):
        """Traduce la cadena STATUS|X:100... que manda el STM32 y actualiza la pantalla"""
        if not data.startswith("STATUS"):
            self.log_console("RX", data) 

        if data.startswith("STATUS|"):
            try:
                parts = data.split('|')
                
                # 1. Posiciones
                x = int(parts[1].split(':')[1])
                y = int(parts[2].split(':')[1])
                z = int(parts[3].split(':')[1])
                
                # 2. Sensores
                sensors = parts[4].split(':')[1]
                s_x = sensors[0] == '1'
                s_y = sensors[1] == '1'
                s_z = sensors[2] == '1'

                # 3. Estados Extra
                is_calibrated = False
                is_moving = False
                if len(parts) > 5:
                    is_calibrated = (parts[5].split(':')[1] == '1')
                    is_moving = (parts[6].split(':')[1] == '1')
                
                # --- ACTUALIZAR LA INTERFAZ ---
                
                # Actualizamos la memoria global del Jefe
                self.app.current_pos = {'x': x, 'y': y, 'z': z}

                # LCDs Visuales
                self.view.lcd_x.display(x)
                self.view.lcd_y.display(y)
                self.view.lcd_z.display(z)

                # LEDs de Finales de Carrera
                self.update_sensor_leds(s_x, s_y, s_z)

                # Etiqueta WAIT
                estilo_wait = "status_badge_wait_on" if is_moving else "status_badge_off"
                self.view.lbl_status_wait.setProperty("class", estilo_wait)
                self.view.lbl_status_wait.style().unpolish(self.view.lbl_status_wait)
                self.view.lbl_status_wait.style().polish(self.view.lbl_status_wait)

                # Lógica de Etiqueta HOME
                if is_calibrated:
                    self.app.stop_home_alert() # Le pide al jefe que apague la alarma
                    self.view.lbl_status_home.setStyleSheet("") 
                    self.view.lbl_status_home.setProperty("class", "status_badge_home_on")
                    self.view.lbl_status_home.setText("HOME OK")
                    self.view.btn_home.setStyleSheet("background-color: #2e7d32; color: white;")
                    self.view.btn_home.setText("HOME OK (:-H)")
                else:
                    self.app.start_home_alert() # Le pide al jefe que prenda la alarma
                    self.view.btn_home.setStyleSheet("") 
                    self.view.btn_home.setText("HOME ALL (:-H)")
                
                self.view.lbl_status_home.style().unpolish(self.view.lbl_status_home)
                self.view.lbl_status_home.style().polish(self.view.lbl_status_home)

            except Exception as e:
                pass # Ignorar tramas cortadas o corruptas

    def update_sensor_leds(self, x_active, y_active, z_active):
        """Pinta de gris o rojo los LEDs circulares de la interfaz"""
        style_on = "QLabel { background-color: #ff3333; border: 2px solid #ff0000; border-radius: 15px; }"
        style_off = "QLabel { background-color: #333; border: 2px solid #555; border-radius: 15px; }"
        
        self.view.led_x.setStyleSheet(style_on if x_active else style_off)
        self.view.led_y.setStyleSheet(style_on if y_active else style_off)
        self.view.led_z.setStyleSheet(style_on if z_active else style_off)