"""
EXECUTION MANAGER (Gestor de Ejecución)
Se encarga de la pestaña "Ejecución": cargar rutinas guardadas, previsualizarlas,
y controlar el ciclo de reproducción (Play, Pausa, Stop) mediante un temporizador.
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox, QFileDialog

# Recorrido real de cada eje, en pasos. Única fuente de verdad del proyecto
# (la misma que valida la tabla de la pestaña Aprendizaje).
from view.ui_widgets import RANGO_X, RANGO_Y, RANGO_Z

TOPES = {'x': RANGO_X, 'y': RANGO_Y, 'z': RANGO_Z}


def acotar_eje(eje, valor):
    """Recorta un valor al recorrido del eje. Devuelve (valor, se_recorto)."""
    try:
        v = int(valor)
    except (TypeError, ValueError):
        return 0, True
    acotado = max(0, min(TOPES[eje], v))
    return acotado, acotado != v

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

        # --- CICLADO DE RUTINA ---
        # cycles_target: cuántas pasadas quedan por hacer (0 = una sola, sin repetir)
        # loop_forever: modo continuo, sólo lo corta el operador
        self.cycles_target = 0
        self.cycles_done = 0
        self.loop_forever = False

        # El Metrónomo: Timer que dicta cada cuánto tiempo se envía el siguiente
        # paso. Parentado a la vista para que muera con la ventana (ver nota en
        # main_controller sobre los timers huérfanos).
        self.run_timer = QTimer(self.view)
        self.run_timer.timeout.connect(self.execute_next_step)

        self.init_connections()

    def init_connections(self):
        """Conecta los botones de control de reproducción"""
        self.view.btn_load_file.clicked.connect(self.load_routine_dialog)
        self.view.btn_play.clicked.connect(self.start_execution)
        self.view.btn_repeat.clicked.connect(self.start_repeat_execution)
        self.view.btn_pause.clicked.connect(self.pause_execution)
        self.view.btn_stop_run.clicked.connect(self.stop_execution)
        self.view.btn_preview.clicked.connect(self.preview_loaded_routine)

    # --- CICLADO ---
    def start_repeat_execution(self):
        """Pregunta cuántos ciclos y arranca la rutina en bucle."""
        from view.repeat_dialog import RepeatDialog

        if not self.loaded_routine:
            QMessageBox.warning(self.view, "Aviso", "Primero cargá una rutina.")
            return

        modo = RepeatDialog.pedir_ciclos(self.view)
        if modo is None:
            return

        self.loop_forever = (modo == RepeatDialog.CONTINUO)
        self.cycles_target = 0 if self.loop_forever else modo
        self.cycles_done = 0

        if self.loop_forever:
            self.log("INFO", "Rutina en MODO CONTINUO. Cortala con DETENER o el paro de emergencia.")
        else:
            self.log("INFO", f"Rutina programada para {modo} ciclos.")
        self.start_execution()

    def reset_cycles(self):
        """Limpia el estado de ciclado (al detener o ante un paro)."""
        self.cycles_target = 0
        self.cycles_done = 0
        self.loop_forever = False

    # --- DESCRIPCIÓN DE UN PASO (una sola definición para los 3 usos) ---
    @staticmethod
    def nombre_de_paso(step):
        """Nombre opcional del punto (clave 'n' del JSON), o cadena vacía."""
        return str(step.get("n", "")).strip()

    def describir_paso(self, indice, step):
        """Texto legible de un paso: 'Paso 3 · «Tomar pieza» — X120 Y40 Z10 @ 50%'.

        El nombre del punto ya existía en el JSON y lo mostraba el panel
        'Secuencia', pero el log de ejecución y el rótulo de progreso lo
        ignoraban: durante una rutina larga no había forma de saber en qué paso
        estaba el robot sin contar filas. Los tres usan ahora esta función para
        que no se vuelvan a desincronizar.
        """
        v = self.velocidad_de_paso(step)
        coords = "X%s Y%s Z%s @ %d%%" % (step.get('x'), step.get('y'),
                                         step.get('z'), v)
        if 'g' in step:
            coords += " · garra %s" % ("CERRAR" if step['g'] == 'C' else "ABRIR")

        nombre = self.nombre_de_paso(step)
        etiqueta = "Paso %d" % (indice + 1)
        if nombre:
            etiqueta += " \u00b7 \u00ab%s\u00bb" % nombre
        return "%s \u2014 %s" % (etiqueta, coords)

    @staticmethod
    def velocidad_de_paso(step):
        """Velocidad del segmento en %, acotada a 10..100 (50 por defecto)."""
        try:
            return max(10, min(100, int(step.get('v', 50))))
        except (TypeError, ValueError):
            return 50

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
                # Panel "Secuencia": lista los pasos para poder seguir la ejecución
                self.view.tab_run.set_sequence(data)
                self.view.tab_run.lbl_points.setText(f"{len(data)} puntos")
                self.view.tab_run.lbl_progress_pct.setText("0%")
                self.view.tab_run.lbl_step.setText("sin ejecutar")
                self.view.txt_run_log.append(f"Rutina cargada: {len(data)} pasos.")
                self.log("INFO", f"Cargada rutina con {len(data)} pasos.")
                self.avisar_pasos_fuera_de_rango(data)
            else:
                QMessageBox.critical(self.view, "Error", "Archivo inválido o corrupto.")

    def avisar_pasos_fuera_de_rango(self, rutina):
        """Revisa la rutina recién cargada contra el recorrido real de cada eje.

        El archivo puede venir editado a mano o de otro robot. Avisamos ACÁ, al
        cargar, en vez de dejar que el operador se entere a mitad de la ejecución:
        los pasos se recortan igual al enviarse, pero eso ya no es una sorpresa.
        """
        malos = []
        for i, step in enumerate(rutina):
            for eje in ('x', 'y', 'z'):
                _, recortado = acotar_eje(eje, step.get(eje, 0))
                if recortado:
                    malos.append(i + 1)
                    break
        if not malos:
            return

        detalle = ", ".join(str(n) for n in malos[:8])
        if len(malos) > 8:
            detalle += ", …"
        self.log("WARN", "La rutina tiene %d paso(s) fuera del recorrido "
                         "(%s). Se recortarán al ejecutarse." % (len(malos), detalle))
        QMessageBox.warning(
            self.view, "Pasos fuera de recorrido",
            "Hay %d paso(s) con coordenadas fuera del recorrido del robot "
            "(X 0-%d, Y 0-%d, Z 0-%d).\n\nPasos: %s\n\n"
            "Se recortarán automáticamente al ejecutar la rutina."
            % (len(malos), RANGO_X, RANGO_Y, RANGO_Z, detalle))

    def preview_loaded_routine(self):
        """Muestra en la consola de texto los pasos cargados sin ejecutar nada"""
        if not self.loaded_routine:
            QMessageBox.warning(self.view, "Aviso", "Primero carga una rutina.")
            return

        self.view.txt_run_log.clear()
        self.view.txt_run_log.append("<b>--- CONTENIDO DE LA RUTINA ---</b>")
        
        for i, step in enumerate(self.loaded_routine):
            linea = self.describir_paso(i, step)
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
        """Detiene la reproducción de la rutina.

        NO envía `:-S`: ese comando engancha el bloqueo de parada de emergencia y
        obligaba a rearmar el robot para volver a dar Play, cuando lo único que se
        quería era cortar la secuencia. Detener es una acción de la interfaz —
        frenar el metrónomo—; la emergencia tiene su propio botón.
        """
        self.is_executing = False
        self.run_timer.stop()
        self.execution_index = 0
        self.reset_cycles()
        self.view.progress_bar.setValue(0)
        self.view.tab_run.lbl_progress_pct.setText("0%")
        self.view.tab_run.lbl_step.setText("detenido")
        self.view.txt_run_log.append("--- DETENIDO ---")
        self.log("INFO", "Ejecución detenida.")

    def halt_by_estop(self):
        """Frena la ejecución porque el robot entró en PARO DE EMERGENCIA (detectado
        por telemetría, ej. botón físico). No reenvía :-S (el robot ya está frenado):
        solo detiene el metrónomo de la interfaz para que no siga mandando pasos."""
        if not self.is_executing:
            return
        self.is_executing = False
        self.run_timer.stop()
        self.execution_index = 0
        # El paro también corta el ciclado: es una de las tres salidas del modo continuo.
        self.reset_cycles()
        self.view.progress_bar.setValue(0)
        self.view.tab_run.lbl_progress_pct.setText("0%")
        self.view.tab_run.lbl_step.setText("detenido por paro de emergencia")
        self.view.txt_run_log.append(
            '<b style="color:#ff3333;">--- DETENIDO POR PARO DE EMERGENCIA ---</b>')

    # --- EL MOTOR DE EJECUCIÓN ---
    def execute_next_step(self):
        """Función llamada automáticamente por el QTimer para avanzar paso a paso"""
        if not self.is_executing: return

        # Si aún quedan pasos en la lista
        if self.execution_index < len(self.loaded_routine):
            step = self.loaded_routine[self.execution_index]
            
            cmd = ""

            # Lo que se loguea tiene que ser lo que REALMENTE se ejecuta: si un
            # paso se recorta por límite, el log muestra el valor recortado.
            paso_real = step

            if step['type'] == 'MOV':
                # Velocidad del segmento (%). Compatibilidad: si el JSON es viejo y
                # no trae 'v', usamos 50 %. La embebemos en el comando (V0nn) para que
                # el firmware la aplique de forma atómica, sin un :-V previo aparte.
                v = self.velocidad_de_paso(step)

                # LÍMITES ARTICULARES: un JSON editado a mano (o traído de otra
                # máquina) podía mandar X5000 y el comando salía tal cual. Se
                # recorta al recorrido real antes de armar el comando.
                x, rx = acotar_eje('x', step['x'])
                y, ry = acotar_eje('y', step['y'])
                z, rz = acotar_eje('z', step['z'])
                if rx or ry or rz:
                    self.log("WARN", "Paso %d fuera de recorrido: se recortó a "
                                     "X%d Y%d Z%d." % (self.execution_index + 1, x, y, z))
                    paso_real = dict(step, x=x, y=y, z=z)

                # Construimos el comando de posición + velocidad del segmento
                cmd = f":#X{x}Y{y}Z{z}V{v:03d}"

                # Actualizamos la memoria global para que los LCDs de la UI se enteren
                self.app.current_pos['x'] = x
                self.app.current_pos['y'] = y
                self.app.current_pos['z'] = z

                # Agregamos la instrucción de la garra si existe
                if 'g' in step:
                    gripper_cmd = "C" if step['g'] == 'C' else "A"
                    cmd += f"|{gripper_cmd}"
            
            self.send_cmd(cmd)
            self.view.txt_run_log.append(
                self.describir_paso(self.execution_index, paso_real))

            # Resaltamos el paso en curso dentro del panel "Secuencia"
            total = len(self.loaded_routine)
            self.view.tab_run.highlight_step(self.execution_index)
            detalle = f"paso {self.execution_index + 1} de {total}"
            # El nombre del punto también acá: el rótulo de progreso decía sólo
            # "paso 3 de 8" y no permitía identificar qué estaba haciendo el brazo.
            nombre = self.nombre_de_paso(step)
            if nombre:
                detalle += f" \u00b7 \u00ab{nombre}\u00bb"
            if self.loop_forever:
                detalle = f"ciclo {self.cycles_done + 1} (continuo) · {detalle}"
            elif self.cycles_target:
                detalle = (f"ciclo {self.cycles_done + 1}/{self.cycles_target}"
                           f" · {detalle}")
            self.view.tab_run.lbl_step.setText(detalle)

            # Si existiera una función en MainController o MovementManager para actualizar los LCDs visualmente:
            if hasattr(self.app, 'movement_mgr'):
                self.app.movement_mgr.update_lcds()

            # Avanzamos al siguiente paso y calculamos el porcentaje de la barra
            self.execution_index += 1
            prog = int((self.execution_index / total) * 100)
            self.view.progress_bar.setValue(prog)
            self.view.tab_run.lbl_progress_pct.setText(f"{prog}%")

        else:
            # --- FIN DE UNA PASADA ---
            self.cycles_done += 1

            quedan_ciclos = (self.loop_forever or
                             self.cycles_done < self.cycles_target)
            if quedan_ciclos:
                # Arranca otra vuelta sin cortar el metrónomo ni avisar por popup:
                # en modo bucle un diálogo por ciclo sería inoperable.
                self.execution_index = 0
                self.view.progress_bar.setValue(0)
                self.view.tab_run.lbl_progress_pct.setText("0%")
                etiqueta = (f"CICLO {self.cycles_done + 1}" if self.loop_forever
                            else f"CICLO {self.cycles_done + 1}/{self.cycles_target}")
                self.view.txt_run_log.append(f"<b>--- {etiqueta} ---</b>")
                return

            # --- FIN DE LA RUTINA ---
            total_ciclos = self.cycles_done
            self.stop_execution()
            self.trigger_finish_signal()
            self.view.txt_run_log.append("--- RUTINA COMPLETADA ---")
            self.view.progress_bar.setValue(100) # Forzamos el 100% visual
            self.view.tab_run.lbl_progress_pct.setText("100%")
            self.view.tab_run.lbl_step.setText("rutina completada")
            resumen = ("Ejecución finalizada con éxito."
                       if total_ciclos <= 1 else
                       f"Ejecución finalizada: {total_ciclos} ciclos completados.")
            QMessageBox.information(self.view, "Fin", resumen)

    def trigger_finish_signal(self):
        """Destello de énfasis del badge FINISH al terminar la rutina.

        Usa el mismo helper que el fin de cualquier movimiento (un jog, un home),
        sólo que más lento y con más repeticiones: un único camino de código para
        el parpadeo, en vez de manipular blink_timer desde acá.
        """
        self.app.flash_finish(veces=6, ms=500)
        self.log("INFO", "Ciclo Finalizado.")