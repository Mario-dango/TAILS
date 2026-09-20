"""
VISTA PRINCIPAL v2
-------------------
Cambios respecto de la v1:
 · Estructura: app bar (marca + conexión + telemetría) → banner de alarma →
   cuerpo (rail izquierdo | pestañas) → dock de consola.
 · Los iconos "kawaii" pasan del 64px global de la v1 a un tamaño por contexto
   (26-55px): el registro guarda el tamaño de cada botón.
 · Atajos de teclado para jogging (← → ↑ ↓ W S) y Esc para parada de emergencia.
 · Mantiene la fachada expose_widgets_to_controller() con los mismos nombres,
   así el paquete /controller sigue funcionando sin cambios.
"""

import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QShortcut, QLineEdit, QTextEdit,
                             QAbstractSpinBox, QScrollArea, QFrame, QApplication,
                             QDockWidget)
from PyQt5.QtCore import Qt, QSize, QSettings, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence

from view.top_bar import TopBar
from view.alarm_banner import AlarmBanner
from view.left_panel import LeftPanel
from view.console_panel import ConsolePanel
from view.tab_calibration import CalibrationTab
from view.tab_teaching import TeachingTab
from view.tab_execution import ExecutionTab

# Anclamos las rutas al propio módulo (no al directorio de trabajo): así la app
# levanta igual lanzada desde interfaz/ o desde la raíz del repositorio.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(_BASE_DIR, "images", "icons")
STYLE_PATH = os.path.join(_BASE_DIR, "style.css")


class View(QMainWindow):
    # Aviso de que la ventana se está cerrando. El controlador lo usa para frenar
    # sus temporizadores (parpadeos de badges, metrónomo de ejecución, retenes de
    # los LEDs) ANTES de que Qt destruya los widgets. Sin esto, un parpadeo en
    # curso al cerrar seguía disparando contra widgets ya liberados.
    cerrando = pyqtSignal()

    # Dónde se guardan el tamaño de la ventana y la posición de la terminal.
    # Son atributos de clase para que la suite de pruebas pueda apuntarlos a un
    # espacio aparte y no pisar la configuración real del operador.
    SETTINGS_ORG = "TAILS"
    SETTINGS_APP = "interfaz"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("T.A.I.L.S. — Technical Articulated Intelligent Linkage System")
        # Con la escala actual el rail de estado necesita ~575px de alto; sumando
        # app bar, consola y márgenes, la ventana precisa ~920px para mostrarlo
        # entero. Fijamos ese mínimo para que NUNCA aparezca barra de desplazamiento.
        # +20px respecto de la v2 inicial: la terminal pasó a ser un dock (suma
        # su barra de título) y los visores del rail crecieron. Con estos
        # mínimos el panel izquierdo sigue entrando entero, que es la condición
        # para que el botón de STOP esté SIEMPRE a la vista.
        self.resize(1500, 980)
        self.setMinimumSize(1280, 940)

        self.is_kawaii = True
        self.icon_registry = {}

        ruta_icono = os.path.join(ICON_DIR, "TAILS_icono.png")
        if os.path.exists(ruta_icono):
            self.setWindowIcon(QIcon(ruta_icono))

        self._settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

        self.setup_menu_bar()
        self.setup_ui_structure()
        self.expose_widgets_to_controller()
        self.assign_all_icons()
        self.setup_shortcuts()
        self.set_stylesheet()
        self._restore_layout()

    # ══════════════════ ESTRUCTURA ══════════════════
    def setup_ui_structure(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 1. app bar
        self.top_bar = TopBar()
        root.addWidget(self.top_bar)

        # 2. banner de alarma (oculto hasta que haga falta)
        self.alarm = AlarmBanner()
        root.addWidget(self.alarm)

        # 3. cuerpo
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(10, 10, 10, 10)
        body_lay.setSpacing(10)

        # El rail de estado maneja su propio desplazamiento: adentro del área
        # desplazable van sólo las tarjetas informativas, mientras que el STOP de
        # emergencia queda anclado abajo (ver LeftPanel). Así el botón está
        # siempre a la vista sin depender de que la ventana tenga cierto alto.
        self.panel_left = LeftPanel()
        # Alias de compatibilidad: antes el scroll lo creaba la vista.
        self.panel_left_scroll = self.panel_left.scroll
        body_lay.addWidget(self.panel_left)

        self.tabs = QTabWidget()
        self.tab_calib = CalibrationTab()
        self.tab_teach = TeachingTab()
        self.tab_run = ExecutionTab()
        self.tabs.addTab(self.tab_calib, "01   CALIBRACIÓN")
        self.tabs.addTab(self.tab_teach, "02   APRENDIZAJE")
        self.tabs.addTab(self.tab_run, "03   EJECUCIÓN")
        self.tabs.setCurrentIndex(1)
        self.tabs.setDocumentMode(True)
        body_lay.addWidget(self.tabs, 1)

        root.addWidget(body, 1)

        # 4. TERMINAL DE COMANDOS (QDockWidget)
        # Antes era el último widget del layout raíz: entraba con su alto natural
        # y no había forma de estirarla ni de sacarla de la ventana. Como dock se
        # puede arrastrar, redimensionar, dejar flotando en otro monitor y cerrar.
        self.console_container = ConsolePanel()
        self.console_dock = QDockWidget("Terminal de comandos", self)
        self.console_dock.setObjectName("console_dock")   # lo necesita saveState()
        self.console_dock.setWidget(self.console_container)
        self.console_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.console_dock.setFeatures(QDockWidget.DockWidgetMovable |
                                      QDockWidget.DockWidgetFloatable |
                                      QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.console_dock)
        # show() explícito: addDockWidget no marca el dock como visible mientras
        # la ventana no se haya mostrado, y sin esto el estado inicial de la
        # terminal quedaba indefinido hasta el primer show() de la ventana.
        self.console_dock.show()
        self.resizeDocks([self.console_dock], [200], Qt.Vertical)

        # compatibilidad: la v1 tenía un botón suelto para la consola
        self.btn_toggle_console = self.top_bar.btn_console

    # ══════════════════ FACHADA ══════════════════
    def expose_widgets_to_controller(self):
        # App bar (antes estaban en el panel izquierdo)
        self.btn_refresh = self.top_bar.btn_refresh
        self.combo_ports = self.top_bar.combo_ports
        self.btn_connect = self.top_bar.btn_connect

        # Panel izquierdo
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
        self.btn_rearm = self.panel_left.btn_rearm

        # Consola
        self.txt_console = self.console_container.txt_console
        self.input_console = self.console_container.input_console
        self.btn_send_console = self.console_container.btn_send
        self.btn_clear_console = self.console_container.btn_clear

        # Calibración
        self.btn_home = self.tab_calib.btn_home
        self.btn_setzero = self.tab_calib.btn_setzero
        self.input_angle_open = self.tab_calib.input_angle_open
        self.btn_set_open = self.tab_calib.btn_set_open
        self.input_angle_close = self.tab_calib.input_angle_close
        self.btn_set_close = self.tab_calib.btn_set_close
        self.chk_enable = self.tab_calib.chk_enable

        # Aprendizaje
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
        self.btn_move_up = self.tab_teach.btn_move_up
        self.btn_move_down = self.tab_teach.btn_move_down

        # Ejecución
        self.lbl_file = self.tab_run.lbl_file
        self.btn_load_file = self.tab_run.btn_load_file
        self.btn_preview = self.tab_run.btn_preview
        self.progress_bar = self.tab_run.progress_bar
        self.btn_play = self.tab_run.btn_play
        self.btn_pause = self.tab_run.btn_pause
        self.btn_stop_run = self.tab_run.btn_stop_run
        self.btn_repeat = self.tab_run.btn_repeat
        self.txt_run_log = self.tab_run.txt_run_log

    # ══════════════════ ICONOS ══════════════════
    def assign_all_icons(self):
        """Tamaño de icono por contexto.

        REGLA: el icono ronda el 60 % del alto útil del botón y, cuando el texto
        va AL LADO, nunca pasa de la mitad del ancho. La tanda anterior subió
        todo un 45 % de golpe y varios botones quedaron con el icono peleando el
        lugar con el rótulo (el caso más visible era el jogging, que además
        pretendía apilarlos con un QPushButton, que no sabe hacerlo).
        """
        # App bar / chrome
        self._set_pixmap(self.top_bar.lbl_logo, "TAILS_icono.png", 44)
        self._set_pixmap(self.alarm.lbl_icon, "alert.png", 32)
        self._set_pixmap(self.tab_run.lbl_file_icon, "load.png", 49)

        self.set_btn_icon(self.top_bar.btn_refresh, "refresh.png", 28)
        self.set_btn_icon(self.top_bar.btn_connect, "plug.png", 29)
        # kawaii.png todavía no está dibujado: hasta que exista se usa showHide.png
        self.set_btn_icon(self.top_bar.btn_kawaii, "kawaii.png", 29, fallback="showHide.png")
        self.set_btn_icon(self.top_bar.btn_help, "help.png", 29)
        self.set_btn_icon(self.top_bar.btn_console, "showHide.png", 29)
        self.set_btn_icon(self.console_container.btn_toggle, "showHide.png", 22)
        self.set_btn_icon(self.action_manual, "help.png", 26)
        self.set_btn_icon(self.action_about, "TAILS_icono.png", 26)

        # Panel izquierdo — el STOP es alto (68px) pero su texto va a la
        # izquierda, así que un icono de 55px lo empujaba contra el borde.
        self.set_btn_icon(self.btn_estop, "alert.png", 40)
        self.set_btn_icon(self.btn_rearm, "rearmar.png", 29)
        self.set_btn_icon(self.alarm.btn_rearm, "rearmar.png", 26)

        # Consola
        self.set_btn_icon(self.btn_send_console, "send.png", 32)
        self.set_btn_icon(self.btn_clear_console, "erase.png", 32)

        # Calibración
        self.set_btn_icon(self.btn_home, "home.png", 44)
        self.set_btn_icon(self.btn_setzero, "zero.png", 44)
        self.set_btn_icon(self.btn_set_open, "open.png", 29)
        self.set_btn_icon(self.btn_set_close, "close.png", 29)

        # Aprendizaje — los botones de jogging son el corazón de la pantalla
        # Son QToolButton con el texto DEBAJO del icono: el icono tiene que
        # dejarle sitio al rótulo dentro de los 88px de alto del botón.
        for btn, name in ((self.btn_x_plus, "x+.png"), (self.btn_x_minus, "x-.png"),
                          (self.btn_y_plus, "y+.png"), (self.btn_y_minus, "y-.png"),
                          (self.btn_z_plus, "z+.png"), (self.btn_z_minus, "z-.png"),
                          (self.btn_home_xy, "homexy.png"), (self.btn_home_z, "homez.png")):
            self.set_btn_icon(btn, name, 34)

        self.set_btn_icon(self.btn_open_grip, "open.png", 28)
        self.set_btn_icon(self.btn_close_grip, "close.png", 28)
        self.set_btn_icon(self.btn_add_point, "add.png", 26)
        self.set_btn_icon(self.btn_del_point, "clear.png", 26)
        self.set_btn_icon(self.btn_clear_all, "clean.png", 26)
        self.set_btn_icon(self.btn_save_file, "save.png", 26)

        # Ejecución
        self.set_btn_icon(self.btn_load_file, "load.png", 32)
        self.set_btn_icon(self.btn_preview, "read.png", 32)
        self.set_btn_icon(self.btn_play, "play.png", 34)
        self.set_btn_icon(self.btn_pause, "pause.png", 34)
        self.set_btn_icon(self.btn_stop_run, "stop.png", 34)
        self.set_btn_icon(self.btn_repeat, "refresh.png", 34)

    def _set_pixmap(self, label, icon_name, size):
        path = os.path.join(ICON_DIR, icon_name)
        if os.path.exists(path):
            label.setPixmap(QPixmap(path).scaled(
                size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _resolve_icon(self, icon_name, fallback=None):
        """Devuelve la ruta del icono, o la del fallback si el primero no existe aún.

        Sirve para dejar cableados iconos que todavía no se dibujaron (kawaii.png):
        el botón muestra el sustituto en vez de quedar vacío y ensuciar la consola.
        """
        path = os.path.join(ICON_DIR, icon_name)
        if os.path.exists(path):
            return path
        if fallback:
            alt = os.path.join(ICON_DIR, fallback)
            if os.path.exists(alt):
                return alt
        return None

    def set_btn_icon(self, item, icon_name, size=24, fallback=None):
        self.icon_registry[item] = {"name": icon_name, "size": size, "fallback": fallback}
        if self.is_kawaii:
            path = self._resolve_icon(icon_name, fallback)
            if path:
                item.setIcon(QIcon(path))
                if hasattr(item, "setIconSize"):
                    item.setIconSize(QSize(size, size))
            else:
                print("Advertencia: no se encontró el icono %s" % icon_name)

    def toggle_kawaii_mode(self, state):
        self.is_kawaii = state
        for item, cfg in self.icon_registry.items():
            if state:
                path = self._resolve_icon(cfg["name"], cfg.get("fallback"))
                if path:
                    item.setIcon(QIcon(path))
                    if hasattr(item, "setIconSize"):
                        item.setIconSize(QSize(cfg["size"], cfg["size"]))
            else:
                item.setIcon(QIcon())

    # ══════════════════ MENÚ / ATAJOS ══════════════════
    def setup_menu_bar(self):
        menu_bar = self.menuBar()

        # --- MENÚ HERRAMIENTAS: panel de test/diagnóstico ---
        tools_menu = menu_bar.addMenu("Herramientas")
        self.action_test_panel = tools_menu.addAction("Panel de Test / Diagnóstico")

        # --- MENÚ AYUDA ---
        help_menu = menu_bar.addMenu("Ayuda")
        self.action_manual = help_menu.addAction("Manual de Usuario")

        # Ayuda de comandos del firmware, en 2 capas (se ven por consola)
        help_menu.addSeparator()
        self.action_cmd_list = help_menu.addAction("Comandos del STM32 (lista en consola)")
        self.action_cmd_example = help_menu.addAction("Ejemplo de un comando… (consola)")

        help_menu.addSeparator()
        self.action_kawaii = help_menu.addAction("Modo Kawaii (Iconos)")
        self.action_kawaii.setCheckable(True)
        self.action_kawaii.setChecked(True)

        help_menu.addSeparator()
        self.action_about = help_menu.addAction("Acerca de T.A.I.L.S.")

    def setup_shortcuts(self):
        """Jogging con teclado — pedido para operar con una mano en el brazo."""
        self.sc_estop = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.sc_x_plus = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.sc_x_minus = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.sc_y_plus = QShortcut(QKeySequence(Qt.Key_Up), self)
        self.sc_y_minus = QShortcut(QKeySequence(Qt.Key_Down), self)
        self.sc_z_plus = QShortcut(QKeySequence(Qt.Key_W), self)
        self.sc_z_minus = QShortcut(QKeySequence(Qt.Key_S), self)

        # Conexiones locales: disparan el mismo click que el botón,
        # así el controlador no necesita saber de los atajos.
        self.sc_x_plus.activated.connect(self.btn_x_plus.click)
        self.sc_x_minus.activated.connect(self.btn_x_minus.click)
        self.sc_y_plus.activated.connect(self.btn_y_plus.click)
        self.sc_y_minus.activated.connect(self.btn_y_minus.click)
        self.sc_z_plus.activated.connect(self.btn_z_plus.click)
        self.sc_z_minus.activated.connect(self.btn_z_minus.click)

        # Esc queda siempre activo: la parada de emergencia tiene que funcionar
        # incluso con el cursor dentro de la consola.
        self.sc_estop.activated.connect(self.btn_estop.click)

        # Los seis atajos de jogging se DESHABILITAN mientras el foco está en una
        # caja de texto. Tiene que ser desactivarlos, no ignorarlos desde el slot:
        # un QShortcut activo CONSUME la tecla, así que un slot que no hace nada
        # igual impide que la flecha llegue al QLineEdit (y el historial de la
        # consola quedaba muerto). Deshabilitado, Qt entrega la tecla al widget
        # con foco con normalidad.
        self._jog_shortcuts = (self.sc_x_plus, self.sc_x_minus,
                               self.sc_y_plus, self.sc_y_minus,
                               self.sc_z_plus, self.sc_z_minus)
        app = QApplication.instance()
        if app is not None:
            app.focusChanged.connect(self._on_focus_changed)

        # El Modo Kawaii se puede togglear desde el botón del app bar o desde el menú
        # Ayuda. Espejamos uno en el otro para que no queden en estados distintos; el
        # repintado real lo dispara action_kawaii.toggled (lo conecta el controlador).
        self.top_bar.btn_kawaii.toggled.connect(self._mirror_kawaii_to_action)
        self.action_kawaii.toggled.connect(self._mirror_kawaii_to_button)

        # Terminal: el botón del app bar manda sobre el dock y el dock informa de
        # vuelta (por si se cierra con su propia ✕).
        self.top_bar.btn_console.toggled.connect(self.toggle_console)
        self.console_dock.visibilityChanged.connect(self._sync_console_button)

    def _on_focus_changed(self, viejo, nuevo):
        """Silencia los atajos de jogging mientras se escribe en un campo de texto.

        Sin esto, ← → ↑ ↓ movían el robot al navegar el historial de la consola, y
        W/S ni siquiera se podían tipear (escribir ':-S' a mano disparaba Z−).
        """
        escribiendo = isinstance(nuevo, (QLineEdit, QTextEdit, QAbstractSpinBox))
        for sc in getattr(self, "_jog_shortcuts", ()):
            sc.setEnabled(not escribiendo)

    def _mirror_kawaii_to_action(self, state):
        if self.action_kawaii.isChecked() != state:
            self.action_kawaii.setChecked(state)

    def _mirror_kawaii_to_button(self, state):
        if self.top_bar.btn_kawaii.isChecked() != state:
            self.top_bar.btn_kawaii.setChecked(state)

    # ══════════════════ TERMINAL (DOCK) ══════════════════
    def toggle_console(self, visible=None):
        """Muestra u oculta el dock de la terminal.

        Sin argumento alterna. El botón del app bar es checkable, así que Qt le
        pasa su estado directamente.
        """
        # isVisibleTo(self) y no isVisible()/isHidden(): mientras la ventana no
        # se mostró, TODOS sus hijos reportan isVisible()==False e
        # isHidden()==True, esté la terminal escondida o no. isVisibleTo()
        # responde la pregunta que de verdad importa: ¿se vería si la ventana
        # estuviera en pantalla?
        if visible is None:
            visible = not self.console_dock.isVisibleTo(self)
        visible = bool(visible)
        self.console_dock.setVisible(visible)
        # No alcanza con esperar a visibilityChanged: Qt sólo lo emite en
        # transiciones de visibilidad REAL, y si la ventana todavía no se mostró
        # el botón se quedaba marcado con la terminal ya escondida.
        self._sync_console_button(visible)

    def _sync_console_button(self, visible):
        """Refleja en el botón el estado real del dock.

        Hace falta porque el dock también se puede cerrar con su propia ✕, y en
        ese caso el botón quedaba marcado con la terminal ya escondida.
        """
        btn = self.top_bar.btn_console
        if btn.isChecked() != visible:
            btn.blockSignals(True)
            btn.setChecked(visible)
            btn.blockSignals(False)

    # ══════════════════ PERSISTENCIA DE LA VENTANA ══════════════════
    def _restore_layout(self):
        """Recupera el tamaño de la ventana y la posición del dock de terminal."""
        geo = self._settings.value("geometry")
        estado = self._settings.value("windowState")
        if geo is not None:
            self.restoreGeometry(geo)
        if estado is not None:
            self.restoreState(estado)
        self._sync_console_button(self.console_dock.isVisibleTo(self))

    def closeEvent(self, event):
        self.cerrando.emit()
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    # ══════════════════ ESTILOS ══════════════════
    def set_stylesheet(self):
        try:
            with open(STYLE_PATH, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Archivo style.css no encontrado en %s" % STYLE_PATH)
