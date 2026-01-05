from model import Model
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox
from view import View, ViewUpdater

class Controller:
    def __init__(self):
        self.model = Model()
        self.view = View()
        self.view_updater = ViewUpdater(self.view)
        
        # Temporizador
        self.receive_timer = QTimer()
        self.receive_timer.timeout.connect(self.receive_data)
        self.serial_port = None
        
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        self.view.show()
        self.update_available_ports()

    def setup_signals(self):
        # Botones existentes
        self.view.button_send.clicked.connect(self.send_data)
        self.view.button_refresh.clicked.connect(self.update_available_ports)
        
        # NUEVO: Conectar botón Limpiar
        self.view.button_clear.clicked.connect(self.clear_console)
        
        # NUEVO: Enviar al presionar Enter en el campo de texto
        self.view.text_input.returnPressed.connect(self.send_data)

    def update_available_ports(self):
        ports = self.model.get_available_ports()
        self.view_updater.update_ports(ports)

    def send_data(self):
        selected_port = self.view_updater.get_selected_port()
        data = self.view_updater.get_input_data()

        if not selected_port:
            QMessageBox.warning(self.view, "Advertencia", "Por favor, selecciona un puerto COM.")
            return

        # Lógica de conexión (con las correcciones que vimos antes)
        if not self.serial_port or (hasattr(self.serial_port, 'port') and selected_port != self.serial_port.port):
            if self.serial_port:
                self.model.close_port()

            new_port_obj = self.model.open_serial_port(selected_port)
            if new_port_obj is None:
                QMessageBox.critical(self.view, "Error", f"No se pudo abrir el puerto {selected_port}")
                return
            
            self.serial_port = new_port_obj
            if not self.receive_timer.isActive():
                self.receive_timer.start(100)

        self.model.send_data(selected_port, data)
        self.view_updater.append_output_text(f"TX: {data}")
        self.view_updater.clear_input_data()

    def receive_data(self):
        received_data = self.model.receive_data()
        if received_data:
            self.view_updater.append_output_text(f"RX: {received_data}")
            
    # NUEVO: Método para ejecutar la limpieza
    def clear_console(self):
        self.view_updater.clear_output_text()

    def cleanup(self):
        if self.serial_port:
            self.model.close_port()
        self.receive_timer.stop()