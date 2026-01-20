from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer # <--- Agrega QTimer
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QFileDialog # <--- Agrega QFileDialog
from view import View
from model import Model
import time

# --- Hilo Trabajador Serial (Sin cambios) ---
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

class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()
        self.worker = None 

        # Variables de Ejecución
        self.loaded_routine = []
        self.execution_index = 0
        self.is_executing = False
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.execute_next_step)

        # --- ESTADO INTERNO DEL ROBOT (Shadow Registers) ---
        # Asumimos que al conectar o hacer Home estamos en 0,0,0
        self.current_pos = {'x': 0, 'y': 0, 'z': 0}
        self.gripper_state = 'A' # A = Abierto, C = Cerrado

        # Timer para efecto blink del LED Finish
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.handle_finish_blink)
        self.blink_count = 0

        # Timer para parpadeo de alerta (HOME necesario)
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.handle_home_alert_blink)
        self.alert_blink_state = False

        self.init_control()
        self.update_ui_connection_state(False)

    def init_control(self):
        self.view.show()
        self.refresh_ports()

        # --- CONEXIONES BASICAS ---
        
        # Conectar acciones de velocidad
        self.view.slider_speed.valueChanged.connect(self.handle_speed_change)
        self.view.slider_speed.sliderReleased.connect(self.send_speed_command)

        # --- 2. CONEXIONES DE HARDWARE Y CONSOLA ---
        self.view.btn_connect.clicked.connect(self.toggle_connection)
        self.view.btn_send_console.clicked.connect(self.handle_console_send)
        self.view.input_console.returnPressed.connect(self.handle_console_send)
        self.view.btn_clear_console.clicked.connect(self.view.txt_console.clear)
        self.view.btn_estop.clicked.connect(self.emergency_stop)
        self.view.btn_refresh.clicked.connect(self.refresh_ports)
        
        # --- 3. CALIBRACIÓN Y CONFIGURACIÓN ---
        self.view.btn_home.clicked.connect(self.handle_home)
        self.view.btn_setzero.clicked.connect(self.handle_set_zero)
        self.view.chk_enable.toggled.connect(self.handle_enable_motor)
        self.view.btn_set_open.clicked.connect(lambda: self.send_command(f":-A{self.view.input_angle_open.text()}"))
        self.view.btn_set_close.clicked.connect(lambda: self.send_command(f":-P{self.view.input_angle_close.text()}"))

        # --- 4. MOVIMIENTO MANUAL (JOGGING) ---
        self.view.btn_x_plus.clicked.connect(lambda: self.handle_jog('x', 1))
        self.view.btn_x_minus.clicked.connect(lambda: self.handle_jog('x', -1))
        self.view.btn_y_plus.clicked.connect(lambda: self.handle_jog('y', 1))
        self.view.btn_y_minus.clicked.connect(lambda: self.handle_jog('y', -1))
        self.view.btn_z_plus.clicked.connect(lambda: self.handle_jog('z', 1))
        self.view.btn_z_minus.clicked.connect(lambda: self.handle_jog('z', -1))
        self.view.btn_open_grip.clicked.connect(lambda: self.handle_gripper('A'))
        self.view.btn_close_grip.clicked.connect(lambda: self.handle_gripper('C'))

        # --- 5. GESTIÓN DE RUTINAS Y PUNTOS ---
        self.view.btn_add_point.clicked.connect(self.add_point_to_table)
        self.view.btn_del_point.clicked.connect(self.delete_point_from_table)
        self.view.btn_save_file.clicked.connect(self.save_routine_json)
        self.view.btn_home_xy.clicked.connect(self.handle_go_zero_xy)
        self.view.btn_home_z.clicked.connect(self.handle_go_zero_z)
        self.view.btn_clear_all.clicked.connect(self.clear_all_table)

        # --- 6. PANEL DE EJECUCIÓN ---
        self.view.btn_load_file.clicked.connect(self.load_routine_dialog)
        self.view.btn_play.clicked.connect(self.start_execution)
        self.view.btn_stop_run.clicked.connect(self.stop_execution)
        self.view.btn_pause.clicked.connect(self.pause_execution)
        # Nuevo: Previsualizar ejecución
        self.view.btn_preview.clicked.connect(self.preview_loaded_routine)

    def update_ui_connection_state(self, is_connected):
        """Bloquea o desbloquea los controles según el estado del hardware."""
        
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
        # Joggin
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
        # self.view.btn_load_file.setEnabled(is_connected)
        # self.view.btn_preview.setEnabled(is_connected)        
        self.view.btn_play.setEnabled(is_connected)
        self.view.btn_pause.setEnabled(is_connected)
        self.view.btn_stop_run.setEnabled(is_connected)
        
        # Si se desconecta, limpiar el label de archivo
        if not is_connected:
            self.view.lbl_file.setText("Archivo: Requiere Conexión")

    # --- LÓGICA DE MOVIMIENTO (JOGGING) ---
    def handle_jog(self, axis, direction):
        if not self.model.is_connected():
            self.log_console("ERROR", "Conecta el robot primero.")
            return

        # 1. Obtener incremento seleccionado (1, 10, 50)
        step_deg = self.view.step_group.checkedId()
        
        # 2. Calcular nueva posición
        # Nota: Aquí sumamos el incremento a la posición que 'creemos' que tiene el robot
        new_val = self.current_pos[axis] + (step_deg * direction)
        
        # (Opcional) Limitar rangos si quisieras (ej: 0 a 180)
        if new_val < 0: new_val = 0
        
        # 3. Actualizar registro interno
        self.current_pos[axis] = new_val
        
        # 4. Enviar Comando (Ej: :#X100)
        # Nota: Usamos el modo ejecución (#) con velocidad por defecto
        cmd = f":#{axis.upper()}{new_val}"
        self.send_command(cmd)
        
        # 5. Actualizar Displays (Visualmente)
        self.update_lcds()

    def handle_go_zero_xy(self):
        # Mover a X0 Y0 (Ejecución absoluta)
        cmd = ":#X0Y0"
        self.send_command(cmd)
        # Actualizamos registros sombra
        self.current_pos['x'] = 0
        self.current_pos['y'] = 0
        self.update_lcds()
        self.log_console("INFO", "Moviendo a X0 Y0...")

    def handle_go_zero_z(self):
        # Mover a Z0
        cmd = ":#Z0"
        self.send_command(cmd)
        self.current_pos['z'] = 0
        self.update_lcds()
        self.log_console("INFO", "Moviendo a Z0...")

    def handle_gripper(self, action):
        # action es 'A' o 'C'
        self.gripper_state = action
        cmd = f":#{action}" # :#A o :#C
        self.send_command(cmd)

    def handle_home(self):
        self.send_command(":-H")
        # Al hacer home, asumimos que todo vuelve a 0
        self.current_pos = {'x': 0, 'y': 0, 'z': 0}
        self.update_lcds()

    def handle_set_zero(self):
        self.send_command(":-Z")
        self.current_pos = {'x': 0, 'y': 0, 'z': 0}
        self.update_lcds()

    def update_lcds(self):
        self.view.lcd_x.display(self.current_pos['x'])
        self.view.lcd_y.display(self.current_pos['y'])
        self.view.lcd_z.display(self.current_pos['z'])

    # --- GESTIÓN DE LA TABLA DE PUNTOS ---
    def add_point_to_table(self):

        # Validación de conexión previa a la captura
        if not self.model.is_connected():
            QMessageBox.warning(self.view, "Error de Conexión", 
            "Debe conectar el robot para capturar una posición válida.")
            return
     
        # Obtener datos actuales   
        x = self.current_pos['x']
        y = self.current_pos['y']
        z = self.current_pos['z']
        g = self.gripper_state
        
        row_pos = self.view.table_points.rowCount()
        self.view.table_points.insertRow(row_pos)
        
        # Insertar celdas
        self.view.table_points.setItem(row_pos, 0, QTableWidgetItem(str(x)))
        self.view.table_points.setItem(row_pos, 1, QTableWidgetItem(str(y)))
        self.view.table_points.setItem(row_pos, 2, QTableWidgetItem(str(z)))
        self.view.table_points.setItem(row_pos, 3, QTableWidgetItem(g))
        
        self.log_console("INFO", f"Punto agregado: X{x} Y{y} Z{z} {g}")

    def delete_point_from_table(self):
        current_row = self.view.table_points.currentRow()
        if current_row >= 0:
            self.view.table_points.removeRow(current_row)

    def save_routine_json(self):

        if not self.model.is_connected():
            self.log_console("ERROR", "No se puede guardar la rutina: Conexión inactiva.")
            QMessageBox.critical(self.view, "Error", "Debe estar conectado para exportar una rutina válida.")
            return

        rows = self.view.table_points.rowCount()
        if rows == 0:
            QMessageBox.warning(self.view, "Aviso", "La lista está vacía.")
            return

        routine = []
        for i in range(rows):
            p = {
                "type": "MOV",
                "x": int(self.view.table_points.item(i, 0).text()),
                "y": int(self.view.table_points.item(i, 1).text()),
                "z": int(self.view.table_points.item(i, 2).text()),
                "g": self.view.table_points.item(i, 3).text()
            }
            routine.append(p)
            
        # ABRIR DIÁLOGO DE SISTEMA
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, 
            "Guardar Rutina", 
            "", 
            "Archivos JSON (*.json);;Todos (*)", 
            options=options
        )
        
        if file_path:
            # Asegurar extensión
            if not file_path.endswith('.json'):
                file_path += '.json'
                
            if self.model.save_routine_to_file(file_path, routine):
                self.log_console("INFO", f"Rutina guardada en: {file_path}")
            else:
                self.log_console("ERROR", "No se pudo guardar el archivo.")
    
    # --- FUNCIONES BASE ---
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
            self.update_ui_connection_state(False) # <--- BLOQUEAR
            self.log_console("INFO", "Desconectado.")
        else:
            port = self.view.combo_ports.currentText()
            if not port: return
            if self.model.connect_port(port):
                self.view.btn_connect.setText("Desconectar"); self.view.btn_connect.setChecked(True)
                self.view.combo_ports.setEnabled(False)
                self.update_ui_connection_state(True) # <--- DESBLOQUEAR
                self.log_console("INFO", f"Conectado a {port}")
                self.worker = SerialWorker(self.model.serial_port)
                self.worker.data_received.connect(self.process_serial_data)
                self.worker.start()

    def send_command(self, cmd):
        
        # Cláusula de guarda: Si no hay conexión, no hacemos nada ni logueamos error serial
        if not self.model.is_connected():
            # Opcional: Loguear solo en debug interno, no en la consola principal
            self.log_console("ERROR", "No conectado.")
            print(f"DEBUG: Intento de envío en modo offline: {cmd}")
            return False

        if self.model.send_data(cmd):
            self.log_console("TX", cmd)
            return True
        return False

    def handle_console_send(self):
        cmd = self.view.input_console.text()
        if cmd: self.send_command(cmd); self.view.input_console.clear()
        
    def handle_enable_motor(self, checked):
        self.send_command(":-E1" if checked else ":-E0")

    def emergency_stop(self):
        if self.model.is_connected():
            self.send_command(":-S")
            self.log_console("ALERTA", "STOP ENVIADO")
        else:
            # Informamos al usuario sin intentar una transmisión fallida
            self.log_console("ERROR", "Robot no conectado.")

    def process_serial_data(self, data):
            # La trama ahora es: STATUS|X:100|Y:0|Z:50|S:001|C:1|M:0
            
            # Filtrar log: Solo mostrar si NO es status repetitivo (opcional)
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

                    # 3. NUEVO: Estados Extra (Calibrado y Moviendo)
                    # Usamos un try/except interno por si tienes una versión vieja de firmware cargada
                    is_calibrated = False
                    is_moving = False
                    if len(parts) > 5:
                        is_calibrated = (parts[5].split(':')[1] == '1') # C:1
                        is_moving = (parts[6].split(':')[1] == '1')     # M:1
                    
                    # --- ACTUALIZAR GUI ---
                    # --- LÓGICA DE ALERTA HOME ---
                    if is_calibrated:
                        self.stop_home_alert() # Robot ya sabe dónde está
                        
                        # Pintar verde fijo (Lógica normal)
                        self.view.lbl_status_home.setStyleSheet("") # Limpiar estilo manual del parpadeo
                        self.view.lbl_status_home.setProperty("class", "status_badge_home_on")
                        self.view.lbl_status_home.setText("HOME OK")
                    else:
                        # Si NO está calibrado, iniciar parpadeo de alerta
                        self.start_home_alert()
                    
                    self.view.lbl_status_home.style().unpolish(self.view.lbl_status_home)
                    self.view.lbl_status_home.style().polish(self.view.lbl_status_home)

                    # 2. WAIT LED (Directo del STM32)
                    estilo_wait = "status_badge_wait_on" if is_moving else "status_badge_off"
                    self.view.lbl_status_wait.setProperty("class", estilo_wait)
                    self.view.lbl_status_wait.style().unpolish(self.view.lbl_status_wait)
                    self.view.lbl_status_wait.style().polish(self.view.lbl_status_wait)

                    # LCDs y Registros
                    self.view.lcd_x.display(x)
                    self.view.lcd_y.display(y)
                    self.view.lcd_z.display(z)
                    self.current_pos = {'x': x, 'y': y, 'z': z}

                    # LEDs Sensores
                    self.update_sensor_leds(s_x, s_y, s_z)

                    # INDICADORES VISUALES DE ESTADO
                    # 1. Indicador de HOME (C)
                    # Cambiamos el color del botón HOME según el estado
                    if is_calibrated:
                        self.view.btn_home.setStyleSheet("background-color: #2e7d32; color: white;") # Verde
                        self.view.btn_home.setText("HOME OK (:-H)")
                    else:
                        self.view.btn_home.setStyleSheet("") # Color default
                        self.view.btn_home.setText("HOME ALL (:-H)")

                    # 2. Indicador de WAIT/MOVIENDO (M)
                    # Podemos deshabilitar los controles manuales si se está moviendo
                    # O poner un borde amarillo a la ventana
                    if is_moving:
                        # self.view.setStyleSheet("QMainWindow { border: 2px solid yellow; background-color: #2b2b2b; }")
                        pass # Ya el LED virtual "WAIT" hace el trabajo visual
                    else:
                        # Restaurar estilo normal (solo fondo, sin borde amarillo)
                        # Nota: Esto es un ejemplo simple, mejor sería tener un Label de estado.
                        pass 

                except Exception as e:
                    pass # Evitar crash por tramas corruptas

    def update_sensor_leds(self, x_active, y_active, z_active):
        # Estilos definidos en style.css
        style_on = "QLabel { background-color: #ff3333; border: 2px solid #ff0000; border-radius: 15px; }"
        style_off = "QLabel { background-color: #333; border: 2px solid #555; border-radius: 15px; }"
        
        self.view.led_x.setStyleSheet(style_on if x_active else style_off)
        self.view.led_y.setStyleSheet(style_on if y_active else style_off)
        self.view.led_z.setStyleSheet(style_on if z_active else style_off)

    def log_console(self, prefix, message):
        color = "#ffffff"
        if prefix == "TX": color = "#00aaff"
        elif prefix == "RX": color = "#00ff00"
        elif prefix == "ERROR": color = "#ff3333"
        elif prefix == "ALERTA": color = "#ffff00"
        elif prefix == "INFO": color = "#ffffff"
        self.view.txt_console.append(f'<span style="color:{color}"><b>[{prefix}]</b> {message}</span>')

        # --- LÓGICA DE EJECUCIÓN ---
    def load_routine_dialog(self):

        # if not self.model.is_connected():
        #     QMessageBox.critical(self.view, "Error de Hardware", "No se puede acceder al sistema de archivos sin un robot vinculado.")
        #     return
        
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, 
            "Cargar Rutina", 
            "", 
            "Archivos JSON (*.json)", 
            options=options
        )
        
        if file_path:
            data = self.model.load_routine_from_file(file_path)
            if data is not None:
                self.loaded_routine = data
                self.view.lbl_file.setText(f"Archivo: {file_path.split('/')[-1]}")
                self.view.progress_bar.setValue(0)
                self.view.txt_run_log.append(f"Rutina cargada: {len(data)} pasos.")
                self.log_console("INFO", f"Cargada rutina con {len(data)} pasos.")
            else:
                QMessageBox.critical(self.view, "Error", "Archivo inválido o corrupto.")

    def start_execution(self):
        if not self.loaded_routine:
            QMessageBox.warning(self.view, "Error", "No hay rutina cargada.")
            return
        
        if not self.model.is_connected():
            QMessageBox.warning(self.view, "Error", "Conecta el robot primero.")
            return

        self.is_executing = True
        self.view.txt_run_log.clear() 
        self.view.txt_run_log.append("<b>--- INICIANDO EJECUCIÓN ---</b>")

        # Si estaba pausado, continuamos; si no, desde cero
        # (Aquí simplificamos: siempre desde cero si le das a Play salvo pausa)
        if self.execution_index >= len(self.loaded_routine):
            self.execution_index = 0
            
        self.run_timer.start(1500) # Enviar un comando cada 1500ms (1.5s)
        self.execute_next_step() # Ejecutar el primero inmediatamente

    def pause_execution(self):
        self.is_executing = False
        self.run_timer.stop()
        self.view.txt_run_log.append("--- PAUSADO ---")

    def stop_execution(self):
        self.is_executing = False
        self.run_timer.stop()
        self.execution_index = 0
        self.view.progress_bar.setValue(0)
        self.view.txt_run_log.append("--- DETENIDO ---")

        # Solo enviamos el comando de seguridad si el hardware está presente
        if self.model.is_connected():
            self.send_command(":-S")
        else:
            self.log_console("INFO", "Ejecución de software detenida (Hardware desconectado).")

    def execute_next_step(self):
        if not self.is_executing: return

        if self.execution_index < len(self.loaded_routine):
            step = self.loaded_routine[self.execution_index]
            
            # Construir comando según tipo
            cmd = ""
            desc = ""
            
            if step['type'] == 'MOV':
                # Nota: Asumimos velocidad por defecto del firmware
                cmd = f":#X{step['x']}Y{step['y']}Z{step['z']}"
                desc = f"Moviendo a X{step['x']} Y{step['y']} Z{step['z']}"
                # Actualizar Shadow Registers para que LCDs se muevan
                self.current_pos['x'] = step['x']
                self.current_pos['y'] = step['y']
                self.current_pos['z'] = step['z']
                
                # Manejo de Garra en el mismo paso si aplica
                if 'g' in step:
                    gripper_cmd = "C" if step['g'] == 'C' else "A"
                    cmd += f"|{gripper_cmd}" # Concatenar comando garra si tu firmware lo soporta así
                    # OJO: Si tu firmware no soporta X..|C juntos, habría que dividirlo.
                    # Por ahora asumimos que tu lógica de Robot_ModoEjecucion maneja ambos.
            
            self.send_command(cmd)
            self.view.txt_run_log.append(f"Paso {self.execution_index + 1}: {desc}")
            self.update_lcds()
            
            # Actualizar progreso
            self.execution_index += 1
            prog = int((self.execution_index / len(self.loaded_routine)) * 100)
            self.view.progress_bar.setValue(prog)
            
        else:
            # Fin de rutina
            self.stop_execution()
            self.trigger_finish_signal()
            self.view.txt_run_log.append("--- RUTINA COMPLETADA ---")
            self.view.progress_bar.setValue(100)
            QMessageBox.information(self.view, "Fin", "Ejecución finalizada con éxito.")

    def preview_loaded_routine(self):
        if not self.loaded_routine:
            QMessageBox.warning(self.view, "Aviso", "Primero carga una rutina.")
            return

        # Limpiamos el log para mostrar solo la rutina
        self.view.txt_run_log.clear()
        self.view.txt_run_log.append("<b>--- CONTENIDO DE LA RUTINA ---</b>")
        
        # Iteramos y mostramos en color diferente (ej: Cyan)
        for i, step in enumerate(self.loaded_routine):
            # Formateamos el texto amigable
            linea = f"Paso {i+1}: X{step.get('x')} | Y{step.get('y')} | Z{step.get('z')}"
            if 'g' in step:
                garra = "CERRAR" if step['g'] == 'C' else "ABRIR"
                linea += f" | Garra: {garra}"
            
            # Insertar HTML con color
            self.view.txt_run_log.append(f'<span style="color:#00bcd4;">{linea}</span>')
            
        self.view.txt_run_log.append("---------------------------------")

    def clear_all_table(self):
        # Verificar si hay algo que borrar
        if self.view.table_points.rowCount() == 0:
            return

        # Pop-up de confirmación
        reply = QMessageBox.question(
            self.view, 
            'Confirmar Limpieza', 
            "¿Estás seguro de que quieres borrar TODOS los puntos de la lista?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.view.table_points.setRowCount(0)
            self.log_console("INFO", "Tabla de puntos limpiada.")

    def trigger_finish_signal(self):
        # Inicia el parpadeo (5 veces)
        self.blink_count = 0
        self.blink_timer.start(500) # Cambia cada 500ms
        self.log_console("INFO", "Ciclo Finalizado.")

    def handle_finish_blink(self):
        self.blink_count += 1
        
        # Alternar ON/OFF
        if self.blink_count % 2 != 0:
            self.view.lbl_status_finish.setProperty("class", "status_badge_finish_on")
        else:
            self.view.lbl_status_finish.setProperty("class", "status_badge_off")
            
        # Refrescar estilo
        self.view.lbl_status_finish.style().unpolish(self.view.lbl_status_finish)
        self.view.lbl_status_finish.style().polish(self.view.lbl_status_finish)
        
        # Parar después de 6 cambios (3 parpadeos completos)
        if self.blink_count >= 6:
            self.blink_timer.stop()
            self.view.lbl_status_finish.setProperty("class", "status_badge_off") # Apagar al final
            self.view.lbl_status_finish.style().unpolish(self.view.lbl_status_finish)
            self.view.lbl_status_finish.style().polish(self.view.lbl_status_finish)

    def handle_speed_change(self, value):
        # Solo actualiza la etiqueta visualmente mientras arrastras
        self.view.lbl_speed_val.setText(f"{value}%")

    def send_speed_command(self):
        # Se envía solo al soltar el mouse para no saturar el puerto
        val = self.view.slider_speed.value()
        cmd = f":-V{val:03d}" # Ejemplo: :-V050
        self.send_command(cmd)
        self.log_console("INFO", f"Velocidad ajustada a {val}%")


    def start_home_alert(self):
        if not self.alert_timer.isActive():
            self.alert_timer.start(500) # Parpadeo cada 500ms
            self.log_console("ALERTA", "Se requiere Homing inicial.")

    def stop_home_alert(self):
        if self.alert_timer.isActive():
            self.alert_timer.stop()
            # Restaurar estilo normal (Apagado o Verde según lógica externa)
            self.view.lbl_status_home.setProperty("class", "status_badge_off")
            self.view.lbl_status_home.style().unpolish(self.view.lbl_status_home)
            self.view.lbl_status_home.style().polish(self.view.lbl_status_home)

    def handle_home_alert_blink(self):
        self.alert_blink_state = not self.alert_blink_state
        
        # Parpadeo entre ROJO (Atención) y GRIS
        if self.alert_blink_state:
            # Necesitamos definir este estilo en style.css o usar uno temporal
            self.view.lbl_status_home.setStyleSheet("background-color: #d32f2f; color: white; border-radius: 4px; border: 1px solid #ff5252;") 
            self.view.lbl_status_home.setText("REQ. HOMING")
        else:
            self.view.lbl_status_home.setStyleSheet("background-color: #333; color: #555; border-radius: 4px; border: 1px solid #444;")
            self.view.lbl_status_home.setText("HOME")