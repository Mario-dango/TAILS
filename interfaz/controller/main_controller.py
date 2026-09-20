"""
CONTROLADOR PRINCIPAL (El Orquestador)
Este archivo inicializa la aplicación y delega las tareas específicas 
a sus 4 sub-controladores (Managers).
"""

import os
from PyQt5.QtCore import QTimer, Qt
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
        self.estop_active = False # Espejo del bloqueo E-STOP del robot (campo E: de la telemetría)

        # 3. --- GESTIÓN DE RUTAS BASE ---
        base_path = os.getcwd()
        self.routines_path = os.path.join(base_path, "rutinas")
        if not os.path.exists(self.routines_path):
            try:
                os.makedirs(self.routines_path)
            except OSError as e:
                print(f"Error creando carpeta rutinas: {e}")

        # 4. --- TIMERS GLOBALES DE INTERFAZ ---
        # TODOS van parentados a la vista: así Qt los destruye junto con la
        # ventana. Sin padre seguían latiendo tras cerrarla y repintaban labels
        # ya liberados ("wrapped C/C++ object of type QLabel has been deleted").
        #
        # Timer para efecto blink del badge FINISH
        self.blink_timer = QTimer(self.view)
        self.blink_timer.timeout.connect(self.handle_finish_blink)
        self.blink_count = 0

        # Destello del badge WAIT mientras el brazo se mueve. Antes quedaba fijo
        # y no había forma de distinguir "moviéndose" de "quedó colgado": ahora
        # late mientras dura la tarea y se apaga al terminarla.
        self.wait_timer = QTimer(self.view)
        self.wait_timer.timeout.connect(self.handle_wait_blink)
        self.wait_blink_state = False

        # Timer para parpadeo de alerta (HOME necesario)
        self.alert_timer = QTimer(self.view)
        self.alert_timer.timeout.connect(self.handle_home_alert_blink)
        self.alert_blink_state = False
        self.homing_failed = False # True si el firmware reportó un error de homing
        self.finish_active = False # Badge FINISH: espejo del LED físico del robot
        self.was_moving = False    # Estado previo de movimiento (para el flanco)

        # 5. --- INICIALIZACIÓN DE MANAGERS ---
        # Aquí le pasamos 'self' (este controlador entero) a cada manager.
        # Así, los managers podrán acceder a app.view, app.model y app.current_pos.
        
        self.connection_mgr = ConnectionManager(self)
        self.movement_mgr = MovementManager(self)
        self.learning_mgr = LearningManager(self)
        self.execution_mgr = ExecutionManager(self)

        # 6. Conexiones generales (Ayuda y UI) que no pertenecen a ningún manager en particular
        self.init_general_ui()

        # Al cerrar la ventana frenamos TODO lo que late. Un parpadeo de badge o
        # el metrónomo de ejecución que sigan corriendo mientras Qt destruye los
        # widgets terminan escribiendo sobre objetos ya liberados.
        self.view.cerrando.connect(self.detener_timers)
        
        # Mostramos la ventana al terminar de configurar todo
        self.view.show()

    def init_general_ui(self):
        """Conecta los botones de la barra de menú superior"""
        self.view.action_manual.triggered.connect(self.show_manual)
        self.view.action_about.triggered.connect(self.show_about)
        self.view.action_kawaii.toggled.connect(self.view.toggle_kawaii_mode)

        # Botón de ayuda del app bar: mismo manual que el del menú
        self.view.top_bar.btn_help.clicked.connect(self.show_manual)

        # El banner de alarma tiene su propio "Rearmar": comparte el slot del
        # botón del panel izquierdo (movement_manager.rearm).
        self.view.alarm.btn_rearm.clicked.connect(self.movement_mgr.rearm)

        # Ayuda de comandos del firmware (2 capas, se ve por consola)
        self.view.action_cmd_list.triggered.connect(self.show_command_list)
        self.view.action_cmd_example.triggered.connect(self.show_command_example)

        # Panel de Test / Diagnóstico
        self.view.action_test_panel.triggered.connect(self.open_test_panel)
        self._test_panel = None

    # --- AYUDA DE COMANDOS (pide al firmware que imprima por consola) ---
    def show_command_list(self):
        """CAPA 1: pide al STM32 la lista completa de comandos (:-?)."""
        self.connection_mgr.log_console("INFO", "Solicitando lista de comandos al STM32 (:-?)…")
        self.connection_mgr.send_command(":-?")

    def show_command_example(self):
        """CAPA 2: elige un comando y pide su ejemplo (:-?<Letra>)."""
        from PyQt5.QtWidgets import QInputDialog
        items = [
            "H — Homing", "Z — Set Zero", "A — Apertura garra", "P — Cierre garra",
            "E — Enable motores", "V — Velocidad global", "S — Stop (E-STOP)",
            "R — Rearmar", "I — Handshake", "# — Mover (ejecución)",
            "M — Test motor", "L — Test LED", "G — Test garra",
        ]
        eleccion, ok = QInputDialog.getItem(
            self.view, "Ejemplo de comando",
            "Elegí el comando para ver un ejemplo en la consola:", items, 0, False)
        if ok and eleccion:
            letra = eleccion.split(" ")[0]  # el primer token es la letra/símbolo
            self.connection_mgr.log_console("INFO", f"Solicitando ejemplo de '{letra}' (:-?{letra})…")
            self.connection_mgr.send_command(f":-?{letra}")

    # --- PANEL DE TEST / DIAGNÓSTICO ---
    def open_test_panel(self):
        """Abre (o trae al frente) la ventana de test de hardware."""
        from view.diagnostics_panel import DiagnosticsPanel
        if self._test_panel is None:
            self._test_panel = DiagnosticsPanel(self.connection_mgr.send_command, parent=self.view)
        self._test_panel.show()
        self._test_panel.raise_()
        self._test_panel.activateWindow()

    # --- APAGADO ORDENADO ---
    def detener_timers(self):
        """Frena todos los temporizadores de la aplicación.

        Se llama al cerrar la ventana. Cada timer está parentado a la vista, así
        que Qt igual los destruiría, pero un evento de timeout ya encolado puede
        ejecutarse con los widgets a medio destruir.
        """
        for timer in (self.blink_timer, self.wait_timer, self.alert_timer):
            timer.stop()
        if hasattr(self, 'execution_mgr'):
            self.execution_mgr.run_timer.stop()
            self.execution_mgr.is_executing = False
        if hasattr(self, 'connection_mgr'):
            self.connection_mgr.detener_retenes()

    # --- SINCRONIZACIÓN DE PARO DE EMERGENCIA (robot -> interfaz) ---
    def handle_estop_engaged(self):
        """El robot entró en PARO (botón físico o :-S). Frenamos la secuencia de la
        interfaz aunque el paro no haya salido de ella, y resaltamos 'Rearmar'."""
        # 1. Frenar la ejecución automática si estaba corriendo
        if hasattr(self, 'execution_mgr'):
            self.execution_mgr.halt_by_estop()
        # 2. Avisar por consola
        if hasattr(self, 'connection_mgr'):
            self.connection_mgr.log_console("ALERTA", "PARO DE EMERGENCIA ACTIVO. Secuencia detenida. Enviá :-R (Rearmar) para continuar.")
        # 3. Franja roja bajo el app bar: el paro deja de ser una línea más de consola
        self.view.alarm.show_alarm(
            "Parada de emergencia activa",
            "Los motores están bloqueados. Verificá el área y rearmá para continuar.")
        # 4. Resaltar el botón Rearmar del panel izquierdo
        self.view.btn_rearm.setProperty("variant", "danger")
        self.view.btn_rearm.setText("¡REARMAR! (:-R)")
        self.view.btn_rearm.style().unpolish(self.view.btn_rearm)
        self.view.btn_rearm.style().polish(self.view.btn_rearm)
        # 5. Marcar el badge WAIT como bloqueo. Cortamos primero su destello: si
        # el paro entra en pleno movimiento, el timer seguiría repintando el badge
        # y se comería el estado de bloqueo.
        self.stop_wait_blink(apagar=False)
        self._pintar_badge(self.view.lbl_status_wait, "status_badge_off")
        self.view.lbl_status_wait.setText("E-STOP")

    def handle_estop_cleared(self):
        """El robot salió del PARO (tras :-R). Restauramos la interfaz."""
        if hasattr(self, 'connection_mgr'):
            self.connection_mgr.log_console("INFO", "Paro liberado. Recordá recalibrar (Home) antes de operar.")
        self.view.alarm.hide_alarm()
        self.view.btn_rearm.setProperty("variant", "")
        self.view.btn_rearm.setText("Rearmar (:-R)")
        self.view.btn_rearm.style().unpolish(self.view.btn_rearm)
        self.view.btn_rearm.style().polish(self.view.btn_rearm)
        self.stop_wait_blink()
        self.view.lbl_status_wait.setText("WAIT / BUSY")

    # --- FUNCIONES DE ALERTAS VISUALES GLOBALES ---
    def set_finish_state(self, encendido):
        """Prende o apaga el badge FINISH del panel de estado.

        Espeja el LED fisico del robot: se enciende cuando el brazo termina de
        moverse (fin de home, de un jog o de una rutina) y se apaga al arrancar
        el movimiento siguiente. Antes solo parpadeaba al completar una rutina y
        el parpadeo terminaba apagado, asi que en la practica no se encendia nunca.
        """
        if self.blink_timer.isActive():
            if encendido:
                return      # ya está destellando hacia "encendido": no lo pisamos
            # Arrancó una tarea nueva: cortamos la ráfaga anterior, porque si no
            # el badge se quedaba en "terminado" durante el movimiento siguiente.
            self.blink_timer.stop()
        self.finish_active = encendido
        self._paint_finish("status_badge_finish_on" if encendido
                           else "status_badge_off")

    def _paint_finish(self, clase):
        lbl = self.view.lbl_status_finish
        lbl.setProperty("class", clase)
        lbl.style().unpolish(lbl)
        lbl.style().polish(lbl)

    def _pintar_badge(self, lbl, clase):
        """Repinta un badge de estado. La clase sale de style.css, no inline."""
        lbl.setProperty("class", clase)
        lbl.style().unpolish(lbl)
        lbl.style().polish(lbl)

    def flash_finish(self, veces=6, ms=250):
        """Ráfaga de destellos del badge FINISH, terminando ENCENDIDO.

        Se dispara al terminar CUALQUIER movimiento (un jog de la pestaña
        Aprendizaje, un home o una rutina completa), no sólo al final de una
        rutina como hacía la versión anterior: el operador necesita ver que la
        acción terminó sin tener que mirar el LED físico del robot.
        """
        self.blink_count = 0
        self._blink_total = veces
        self.blink_timer.start(ms)

    def handle_finish_blink(self):
        """Parpadeo de enfasis al completar una tarea."""
        self.blink_count += 1
        self._paint_finish("status_badge_finish_on" if self.blink_count % 2
                           else "status_badge_off")

        if self.blink_count >= getattr(self, "_blink_total", 6):
            self.blink_timer.stop()
            # Termina ENCENDIDO: la tarea quedo completada. Antes terminaba en
            # "off" y el badge se apagaba apenas dejaba de parpadear.
            self.finish_active = True
            self._paint_finish("status_badge_finish_on")

    # --- DESTELLO DE 'WAIT / BUSY' MIENTRAS EL BRAZO SE MUEVE ---
    def start_wait_blink(self):
        """Arranca el latido del badge WAIT (hay un movimiento en curso)."""
        if not self.wait_timer.isActive():
            self.wait_blink_state = False
            self.wait_timer.start(300)

    def stop_wait_blink(self, apagar=True):
        """Corta el latido de WAIT. Con apagar=False deja el badge como está
        (lo usa el paro de emergencia, que pinta su propio estado)."""
        if self.wait_timer.isActive():
            self.wait_timer.stop()
        self.wait_blink_state = False
        if apagar:
            self._pintar_badge(self.view.lbl_status_wait, "status_badge_off")

    def handle_wait_blink(self):
        self.wait_blink_state = not self.wait_blink_state
        self._pintar_badge(self.view.lbl_status_wait,
                           "status_badge_wait_on" if self.wait_blink_state
                           else "status_badge_off")


    def start_home_alert(self):
        """Arranca el parpadeo del indicador HOME (robot sin calibrar)."""
        if not self.alert_timer.isActive():
            self.alert_timer.start(500)

    def stop_home_alert(self):
        """Detiene el parpadeo del indicador HOME (robot ya calibrado)."""
        if self.alert_timer.isActive():
            self.alert_timer.stop()
        self.alert_blink_state = False
        self.homing_failed = False # Al calibrar bien, se borra el estado de error

    def notify_homing_failed(self, msg):
        """El firmware reportó un error de homing: log en rojo + parpadeo marcado."""
        self.homing_failed = True
        if hasattr(self, 'connection_mgr'):
            self.connection_mgr.log_console("ERROR", f"FALLO DE HOMING → {msg}")
        self.start_home_alert() # Aseguramos que el indicador HOME esté parpadeando

    def notify_homing_ok(self):
        """El firmware reportó homing exitoso."""
        self.homing_failed = False
        if hasattr(self, 'connection_mgr'):
            self.connection_mgr.log_console("INFO", "Homing OK. Robot calibrado.")

    def handle_home_alert_blink(self):
        """Hace parpadear el indicador HOME. Muestra 'HOME FALLÓ' si hubo un error de
        homing, o 'REQ. HOMING' si simplemente falta calibrar."""
        self.alert_blink_state = not self.alert_blink_state
        lbl = self.view.lbl_status_home
        lbl.setText("HOME FALLO" if self.homing_failed else "REQ. HOMING")
        # Alternamos entre las clases del tema en vez de pisar con stylesheets inline,
        # así el parpadeo respeta la paleta del rediseño.
        lbl.setProperty("class", "status_badge_wait_on" if self.alert_blink_state
                        else "status_badge_off")
        lbl.style().unpolish(lbl)
        lbl.style().polish(lbl)

    # --- FUNCIONES DE LA BARRA DE AYUDA ---
    def show_manual(self):
        instrucciones = (
            "<b>Manual de Usuario — T.A.I.L.S.</b><br><br>"

            "<b>Conexión:</b> Elegí el puerto COM y presioná <b>Conectar</b>. Al conectar se "
            "envía el handshake (<code>:-I</code>) y el robot informa por consola el estado del "
            "LCD (dirección I2C detectada o si no responde).<br><br>"

            "<b>1. Calibración:</b> Hacé <b>Home</b> (<code>:-H</code>) antes de operar. "
            "Si el homing falla, el indicador <b>HOME</b> parpadea mostrando "
            "<b>HOME FALLÓ</b> y la consola detalla el motivo (qué eje y por qué). "
            "También podés fijar el cero actual con <b>Set Zero</b> (<code>:-Z</code>).<br>"

            "<b>2. Aprendizaje:</b> Movés el brazo con las flechas (jogging), ajustás velocidad "
            "e incremento, y con <b>Guardar Punto</b> armás la secuencia. Exportás a JSON.<br>"

            "<b>3. Ejecución:</b> Cargás la rutina JSON y presionás <b>Play</b>.<br><br>"

            "<b>Paro de Emergencia:</b> El botón <b>STOP EMERGENCIA</b> (o el pulsador físico) "
            "frena el robot y <u>engancha un bloqueo</u>. La interfaz lo detecta por telemetría: "
            "<b>detiene la secuencia automáticamente</b> y resalta el botón <b>¡REARMAR!</b>. "
            "Para salir del bloqueo, presioná <b>Rearmar</b> (<code>:-R</code>) y volvé a hacer Home.<br><br>"

            "<b>Herramientas → Panel de Test / Diagnóstico:</b> ventana para probar el hardware "
            "pieza por pieza: prender/apagar cada LED y mover cada motor de forma independiente. "
            "Ideal para verificar conexiones sin cargar una rutina.<br><br>"

            "<b>Ayuda → Comandos del STM32:</b> imprime en la consola la lista de comandos que "
            "interpreta el firmware. <b>Ayuda → Ejemplo de un comando…</b> muestra un ejemplo "
            "concreto del comando que elijas.<br><br>"

            "<i>Nota: si el indicador de sistema dice 'REQ. HOMING' o 'HOME FALLÓ', andá a la "
            "pestaña de Calibración y hacé Home.</i>"
        )
        QMessageBox.information(self.view, "Manual de Usuario", instrucciones)

    def show_about(self):
        about_text = (
            "<h2>T.A.I.L.S.</h2>"
            "<p><b>Technical Articulated Intelligent Linkage System</b></p>"
            "<p>Interfaz de control robótico — versión 2.0 «Instrument Dark».</p>"

            "<p><b>Repositorio</b><br>"
            "<a href='https://github.com/Mario-dango/TAILS'>"
            "github.com/Mario-dango/TAILS</a></p>"

            "<p><b>Autores</b><br>"
            "Mario Papetti &nbsp;— &nbsp;"
            "<a href='mailto:mp.robots@gmail.com'>mp.robots@gmail.com</a><br>"
            "Francisco Cano &nbsp;— &nbsp;"
            "<a href='mailto:francano773@gmail.com'>francano773@gmail.com</a></p>"

            "<p><i>Universidad Nacional de Cuyo</i></p>"
        )
        dlg = QMessageBox(self.view)
        dlg.setWindowTitle("Acerca de")
        dlg.setIconPixmap(self.view.windowIcon().pixmap(64, 64))
        dlg.setText(about_text)
        # Sin esto los enlaces se ven como texto plano y no se pueden abrir.
        dlg.setTextFormat(Qt.RichText)
        dlg.setTextInteractionFlags(Qt.TextBrowserInteraction)
        dlg.exec_()