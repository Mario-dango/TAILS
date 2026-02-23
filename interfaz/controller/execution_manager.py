"""
EXECUTION MANAGER (Gestor de Ejecución)
Se encarga de la pestaña "Ejecución": cargar rutinas guardadas, previsualizarlas,
y controlar el ciclo de reproducción (Play, Pausa, Stop) mediante un temporizador.
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox, QFileDialog

class ExecutionManager:
    def __init__(self, main_controller):
        # Recibe al Jefe para acceder a las variables globales y la interfaz
        self.app = main_controller
        self.view = main_controller.view
        self.model = main_controller.model

        # Variables exclusivas de la ejecución
        self.loaded_routine = []
        self.execution_index = 0
        self.is_executing = False
        
        # El Metrónomo: Timer que dicta cada cuánto tiempo se envía el siguiente paso
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.execute_next_step)

        self.init_connections()

    def init_connections(self):
        """Conecta los botones de control de reproducción"""
        self.view.btn_load_file.clicked.connect(self.load_routine_dialog)
        self.view.btn_play.clicked.connect(self.start_execution)
        self.view.btn_pause.clicked.connect(self.pause_execution)
        self.view.btn_stop_run.clicked.connect(self.stop_execution)
        self.view.btn_preview.clicked.connect(self.preview_loaded_routine)

    # --- FUNCIONES HELPER ---
    def send_cmd(self, cmd):
        """Atajo para enviar comandos usando el ConnectionManager del jefe"""
        if hasattr(self.app, 'connection_mgr'):
            self.app.connection_mgr.send_command(cmd)

    def log(self, prefix, msg):
        """Atajo para loguear en la consola inferior"""
        if hasattr(self.app, 'connection_mgr'):
            self.app.connection_mgr.log_console(prefix, msg)

    # --- GESTIÓN DE ARCHIVOS ---
    def load_routine_dialog(self):
        """Abre el explorador para buscar un JSON y lo carga en memoria"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self.view, 
            "Cargar Rutina", 
            self.app.routines_path, # Abre por defecto en la carpeta de rutinas
            "Archivos JSON (*.json)", 
            options=options
        )
        
        if file_path:
            # Pedimos al modelo que lea el archivo físico
            data = self.model.load_routine_from_file(file_path)
            
            if data is not None:
                self.loaded_routine = data
                # Extraemos solo el nombre del archivo para mostrarlo (ej: rutina1.json)
                nombre_archivo = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                self.view.lbl_file.setText(f"Archivo: {nombre_archivo}")
                self.view.progress_bar.setValue(0)
                self.view.txt_run_log.append(f"Rutina cargada: {len(data)} pasos.")
                self.log("INFO", f"Cargada rutina con {len(data)} pasos.")
            else:
                QMessageBox.critical(self.view, "Error", "Archivo inválido o corrupto.")

    def preview_loaded_routine(self):
        """Muestra en la consola de texto los pasos cargados sin ejecutar nada"""
        if not self.loaded_routine:
            QMessageBox.warning(self.view, "Aviso", "Primero carga una rutina.")
            return

        self.view.txt_run_log.clear()
        self.view.txt_run_log.append("<b>--- CONTENIDO DE LA RUTINA ---</b>")
        
        for i, step in enumerate(self.loaded_routine):
            linea = f"Paso {i+1}: X{step.get('x')} | Y{step.get('y')} | Z{step.get('z')}"
            if 'g' in step:
                garra = "CERRAR" if step['g'] == 'C' else "ABRIR"
                linea += f" | Garra: {garra}"
            
            self.view.txt_run_log.append(f'<span style="color:#00bcd4;">{linea}</span>')
            
        self.view.txt_run_log.append("---------------------------------")

    # --- LÓGICA DE REPRODUCCIÓN (PLAY / PAUSA / STOP) ---
    def start_execution(self):
        """Inicia o reanuda la secuencia de movimientos"""
        if not self.loaded_routine:
            QMessageBox.warning(self.view, "Error", "No hay rutina cargada.")
            return
        
        if not self.model.is_connected():
            QMessageBox.warning(self.view, "Error", "Conecta el robot primero.")
            return

        self.is_executing = True
        
        # Si empezamos de cero, limpiamos el log visual
        if self.execution_index == 0:
            self.view.txt_run_log.clear() 
            self.view.txt_run_log.append("<b>--- INICIANDO EJECUCIÓN ---</b>")
        else:
            self.view.txt_run_log.append("<b>--- REANUDANDO EJECUCIÓN ---</b>")

        # Inicia el metrónomo (1500 ms = 1.5 segundos entre comandos)
        self.run_timer.start(1500) 
        self.execute_next_step() # Ejecutamos el primer paso inmediatamente

    def pause_execution(self):
        """Pausa el temporizador, manteniendo el índice donde se quedó"""
        self.is_executing = False
        self.run_timer.stop()
        self.view.txt_run_log.append("--- PAUSADO ---")

    def stop_execution(self):
        """Detiene todo, reinicia el progreso y envía un comando Stop al robot"""
        self.is_executing = False
        self.run_timer.stop()
        self.execution_index = 0
        self.view.progress_bar.setValue(0)
        self.view.txt_run_log.append("--- DETENIDO ---")

        if self.model.is_connected():
            self.send_cmd(":-S")
        else:
            self.log("INFO", "Ejecución de software detenida (Hardware desconectado).")

    # --- EL MOTOR DE EJECUCIÓN ---
    def execute_next_step(self):
        """Función llamada automáticamente por el QTimer para avanzar paso a paso"""
        if not self.is_executing: return

        # Si aún quedan pasos en la lista
        if self.execution_index < len(self.loaded_routine):
            step = self.loaded_routine[self.execution_index]
            
            cmd = ""
            desc = ""
            
            if step['type'] == 'MOV':
                # Construimos el comando de posición
                cmd = f":#X{step['x']}Y{step['y']}Z{step['z']}"
                desc = f"Moviendo a X{step['x']} Y{step['y']} Z{step['z']}"
                
                # Actualizamos la memoria global para que los LCDs de la UI se enteren
                self.app.current_pos['x'] = step['x']
                self.app.current_pos['y'] = step['y']
                self.app.current_pos['z'] = step['z']
                
                # Agregamos la instrucción de la garra si existe
                if 'g' in step:
                    gripper_cmd = "C" if step['g'] == 'C' else "A"
                    cmd += f"|{gripper_cmd}" 
            
            self.send_cmd(cmd)
            self.view.txt_run_log.append(f"Paso {self.execution_index + 1}: {desc}")
            
            # Si existiera una función en MainController o MovementManager para actualizar los LCDs visualmente:
            if hasattr(self.app, 'movement_mgr'):
                self.app.movement_mgr.update_lcds()
            
            # Avanzamos al siguiente paso y calculamos el porcentaje de la barra
            self.execution_index += 1
            prog = int((self.execution_index / len(self.loaded_routine)) * 100)
            self.view.progress_bar.setValue(prog)
            
        else:
            # --- FIN DE LA RUTINA ---
            self.stop_execution()
            self.trigger_finish_signal()
            self.view.txt_run_log.append("--- RUTINA COMPLETADA ---")
            self.view.progress_bar.setValue(100) # Forzamos el 100% visual
            QMessageBox.information(self.view, "Fin", "Ejecución finalizada con éxito.")

    def trigger_finish_signal(self):
        """Llama al Jefe para iniciar la animación visual de parpadeo (LED Finish)"""
        self.app.blink_count = 0
        self.app.blink_timer.start(500) 
        self.log("INFO", "Ciclo Finalizado.")