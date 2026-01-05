from PyQt5.QtWidgets import (QMainWindow, QLabel, QComboBox, QLineEdit, 
                             QPushButton, QTextEdit, QWidget, QGridLayout)

class View(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Comunicación Serial")
        self.resize(450, 350) 

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QGridLayout()
        central_widget.setLayout(layout)

        # --- Widgets ---
        self.label_select_port = QLabel("Seleccionar puerto COM:", self)
        self.combo_ports = QComboBox(self)

        self.label_send_data = QLabel("Enviar datos al dispositivo:", self)
        self.text_input = QLineEdit(self)

        self.button_send = QPushButton("Enviar", self)
        self.button_refresh = QPushButton("Refrescar", self)
        
        # NUEVO: Botón para limpiar
        self.button_clear = QPushButton("Limpiar", self)

        self.label_sent_received = QLabel("Datos enviados y recibidos:", self)
        
        self.text_output = QTextEdit(self)
        self.text_output.setReadOnly(True)

        # --- Layout (Filas, Columnas) ---
        layout.addWidget(self.label_select_port, 0, 0)
        layout.addWidget(self.combo_ports, 0, 1)

        layout.addWidget(self.label_send_data, 1, 0)
        layout.addWidget(self.text_input, 1, 1)

        layout.addWidget(self.button_send, 2, 0)
        layout.addWidget(self.button_refresh, 2, 1)

        # Fila 3: Label a la izquierda, Botón Limpiar a la derecha
        layout.addWidget(self.label_sent_received, 3, 0)
        layout.addWidget(self.button_clear, 3, 1) # <--- Aquí ubicamos el botón nuevo

        layout.addWidget(self.text_output, 4, 0, 1, 2)
                
        self.set_stylesheet()

    def set_stylesheet(self):
        try:
            with open("style.css", "r") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            print("Archivo style.css no encontrado")


class ViewUpdater:
    def __init__(self, view):
        self.view = view

    def update_ports(self, ports):
        self.view.combo_ports.clear()
        self.view.combo_ports.addItems(ports)

    def get_selected_port(self):
        return self.view.combo_ports.currentText()

    def get_input_data(self):
        return self.view.text_input.text()

    def clear_input_data(self):
        self.view.text_input.clear()

    def append_output_text(self, text):
        self.view.text_output.append(text)
        
    # NUEVO: Método para limpiar la consola
    def clear_output_text(self):
        self.view.text_output.clear()