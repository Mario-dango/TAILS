"""
CONNECTION MANAGER (Gestor de Comunicaciones)
Se encarga exclusivamente de abrir/cerrar el puerto serie, enviar comandos
y procesar (parsear) la información que llega del microcontrolador STM32.
"""

import time
from functools import partial
from PyQt5.QtCore import QThread, QTimer, pyqtSignal

# Tiempo mínimo que un LED de fin de carrera queda encendido, en ms. Un final se
# pisa durante unos pocos milisegundos (sobre todo en el homing, donde el motor
# rebota y retrocede enseguida): sin este retén la trama con S:1 llega, se pinta
# y se despinta entre dos refrescos, y en pantalla no se ve nada.
RETENCION_LED_MS = 700

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

        # Retén de los LEDs de finales de carrera: {eje: QTimer}. Mientras el
        # timer del eje esté activo el LED no se apaga, aunque lleguen tramas
        # con el sensor ya liberado.
        self._led_hold = {}
        # Última lectura CRUDA de cada final (lo que dice la telemetría, sin retén).
        self._sensores = {'x': False, 'y': False, 'z': False}

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
        # clear_console() además resetea el contador de líneas de la cabecera;
        # txt_console.clear() a secas lo dejaba desfasado.
        self.view.btn_clear_console.clicked.connect(self.view.console_container.clear_console)

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
            # set_link() ya se encarga del texto del botón y del badge del app bar.
            self.view.top_bar.set_link(False)
            self.view.btn_connect.setChecked(False)
            self.view.combo_ports.setEnabled(True)
            self.view.console_container.set_port("sin puerto abierto")
            self.update_ui_connection_state(False) # BLOQUEAR INTERFAZ
            self.log_console("INFO", "Desconectado.")
        else:
            port = self.view.combo_ports.currentText()
            if not port: return
            if self.model.connect_port(port):
                self.view.top_bar.set_link(True)
                self.view.btn_connect.setChecked(True)
                self.view.combo_ports.setEnabled(False)
                self.view.console_container.set_port(f"{port} · 115200 · 8N1")
                self.update_ui_connection_state(True) # DESBLOQUEAR INTERFAZ
                self.log_console("INFO", f"Conectado a {port}")
                
                # Inicia el hilo que escucha el puerto
                self.worker = SerialWorker(self.model.serial_port)
                self.worker.data_received.connect(self.process_serial_data)
                self.worker.start()

                # Handshake: avisa al firmware que se estableció la comunicación.
                # El STM32 responde y muestra el aviso en su LCD (~2.5 s).
                self.send_command(":-I")

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
            # Queda en el historial aunque el envío falle: si el robot no estaba
            # conectado, poder recuperarlo con ↑ y reintentar es justo lo que se quiere.
            self.view.console_container.push_history(cmd)
            self.view.input_console.clear()

    def log_console(self, prefix, message):
        """Imprime un mensaje en la terminal inferior con su severidad.

        Delega en ConsolePanel.append_line(), que agrega timestamp, colorea la
        etiqueta según la severidad y lleva el contador de líneas de la cabecera.
        """
        self.view.console_container.append_line(prefix, message)

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
        self.view.btn_repeat.setEnabled(is_connected)
        
        if not is_connected:
            self.view.lbl_file.setText("Archivo: Requiere Conexión")

    # --- LÓGICA DE RECEPCIÓN (EL PARSER) ---
    def process_serial_data(self, data):
        """Traduce la cadena STATUS|X:100... que manda el STM32 y actualiza la pantalla"""
        if not data.startswith("STATUS"):
            self.log_console("RX", data)
            # Feedback visual del resultado del homing (además del texto en consola)
            low = data.lower()
            if "homing error" in low or "abortado" in low:
                self.app.notify_homing_failed(data)
            elif "homing ok" in low:
                self.app.notify_homing_ok()

        if data.startswith("STATUS|"):
            try:
                parts = data.split('|')

                # El firmware también emite STATUS|Homing...|M:1 (robot_logic.c),
                # que no tiene los campos posicionales. Antes reventaba el parseo y
                # el except lo tragaba en silencio; ahora lo salteamos explícitamente.
                if len(parts) < 5:
                    return

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

                # 3b. PARO DE EMERGENCIA (campo E:). Lo buscamos por nombre para ser
                # compatible con firmware viejo que no lo enviaba (queda en False).
                is_estop = False
                for p in parts[5:]:
                    if p.startswith('E:'):
                        is_estop = (p.split(':')[1] == '1')

                # Detectamos el FLANCO: si el robot entró (o salió) del bloqueo por
                # paro —tanto por el botón físico como por :-S—, avisamos al Jefe para
                # que frene la secuencia de ejecución por su cuenta.
                prev_estop = getattr(self.app, 'estop_active', False)
                if is_estop != prev_estop:
                    self.app.estop_active = is_estop
                    if is_estop:
                        self.app.handle_estop_engaged()
                    else:
                        self.app.handle_estop_cleared()
                
                # --- ACTUALIZAR LA INTERFAZ ---
                
                # Actualizamos la memoria global del Jefe
                self.app.current_pos = {'x': x, 'y': y, 'z': z}

                # Lecturas de posición (en pasos)
                self.view.lcd_x.display(x)
                self.view.lcd_y.display(y)
                self.view.lcd_z.display(z)

                # Telemetría condensada del app bar + vista superior y gauge Z
                self.view.top_bar.set_position(x, y, z)
                self.view.panel_left.update_preview(x, y, z)

                # LEDs de Finales de Carrera
                self.update_sensor_leds(s_x, s_y, s_z)

                # Badges WAIT y FINISH por FLANCO del estado de movimiento, igual
                # que los LEDs físicos del robot. Los dos DESTELLAN: WAIT late
                # mientras dura la tarea y FINISH hace una ráfaga al terminarla,
                # así el fin de un jog en la pestaña Aprendizaje se ve sin tener
                # que mirar la placa. Antes ambos quedaban fijos y el único
                # parpadeo era el del final de una rutina completa.
                if is_moving != self.app.was_moving:
                    self.app.was_moving = is_moving
                    if is_moving:
                        # Arrancó una tarea: lo anterior deja de estar "terminado".
                        self.app.set_finish_state(False)
                        self.app.start_wait_blink()
                    else:
                        self.app.stop_wait_blink()
                        self.app.flash_finish()

                # Lógica de Etiqueta HOME
                if is_calibrated:
                    self.app.stop_home_alert() # Le pide al jefe que apague la alarma
                    self.view.lbl_status_home.setStyleSheet("") 
                    self.view.lbl_status_home.setProperty("class", "status_badge_home_on")
                    self.view.lbl_status_home.setText("HOME OK")
                    self.set_home_button_state(True)
                else:
                    self.app.start_home_alert() # Le pide al jefe que prenda la alarma
                    self.set_home_button_state(False)
                
                self.view.lbl_status_home.style().unpolish(self.view.lbl_status_home)
                self.view.lbl_status_home.style().polish(self.view.lbl_status_home)

            except Exception as e:
                # Trama cortada o corrupta. Se avisa por consola en vez de
                # descartarla en silencio: un 'except: pass' escondió durante
                # mucho tiempo que ciertas tramas del firmware ni se parseaban.
                self.log_console("WARN", "Trama ilegible (%s): %s" % (e, data))

    def set_home_button_state(self, calibrado):
        """Marca el botón de Home como logrado o pendiente.

        Usa la variante 'success' del tema en lugar de un verde inline, para que el
        color salga de style.css como el resto de la interfaz.
        """
        btn = self.view.btn_home
        btn.setProperty("variant", "success" if calibrado else "home")
        btn.setText("HOME OK (:-H)" if calibrado else "HOME ALL (:-H)")
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def update_sensor_leds(self, x_active, y_active, z_active):
        """Prende o apaga los LEDs de finales de carrera.

        Usa los objectName del tema (sensor_led_on/off) en vez de un stylesheet
        inline: así los colores salen de style.css y siguen la paleta del rediseño.

        El encendido tiene RETENCIÓN: un final se pisa por unos milisegundos y el
        firmware ya manda la trama siguiente con el sensor liberado, así que sin
        retén el LED se prendía y apagaba dentro del mismo refresco y en la
        práctica no se veía nunca (el caso típico es el homing).
        """
        for eje, led, activo in (('x', self.view.led_x, x_active),
                                 ('y', self.view.led_y, y_active),
                                 ('z', self.view.led_z, z_active)):
            self._sensores[eje] = activo
            if activo:
                self._arrancar_reten(eje)
                self._pintar_led(led, True)
            elif eje not in self._led_hold:
                # Sin retén pendiente: el apagado se aplica de inmediato.
                self._pintar_led(led, False)

    def _pintar_led(self, led, encendido):
        nombre = "sensor_led_on" if encendido else "sensor_led_off"
        if led.objectName() == nombre:
            return                      # ya está así: evitamos repolish inútiles
        led.setObjectName(nombre)
        led.style().unpolish(led)
        led.style().polish(led)

    def _arrancar_reten(self, eje):
        """Mantiene encendido el LED del eje durante RETENCION_LED_MS."""
        timer = self._led_hold.get(eje)
        if timer is None:
            # Parentado a la vista: muere con la ventana en vez de quedar
            # latiendo contra un QLabel ya liberado.
            timer = QTimer(self.view)
            timer.setSingleShot(True)
            # partial y no un lambda con argumento por defecto: PyQt5 inspecciona
            # la aridad del slot y con el lambda llegaba a invocarlo sin el
            # argumento ("TypeError: missing 1 required positional argument").
            timer.timeout.connect(partial(self._vencer_reten, eje))
            self._led_hold[eje] = timer
        timer.start(RETENCION_LED_MS)   # reiniciar extiende el retén

    def detener_retenes(self):
        """Frena los retenes de los LEDs (al cerrar la aplicación)."""
        for timer in self._led_hold.values():
            timer.stop()
        self._led_hold.clear()

    def _vencer_reten(self, eje):
        """Venció el retén: apagamos sólo si el sensor ya no está pisado.

        Si sigue pisado dejamos el LED encendido; la próxima trama (o el latido
        de 2 s del firmware) renovará el retén.
        """
        self._led_hold.pop(eje, None)
        if self._sensores.get(eje):
            self._arrancar_reten(eje)
            return
        self._pintar_led(getattr(self.view, "led_%s" % eje), False)