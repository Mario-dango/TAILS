import serial
import serial.tools.list_ports
import json

class Model:
    def __init__(self):
        self.serial_port = None
        self.baud_rate = 115200

    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def connect_port(self, port_name):
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                
            self.serial_port = serial.Serial(port_name, self.baud_rate, timeout=1.0)
            return True
        except serial.SerialException as e:
            print(f"Error abriendo puerto: {e}")
            return False

    def disconnect_port(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None

    def is_connected(self):
        return self.serial_port is not None and self.serial_port.is_open

    def send_data(self, data):
        if self.is_connected():
            try:
                # Aseguramos salto de línea y encoding
                if not data.endswith('\n'):
                    data += '\n'
                self.serial_port.write(data.encode('utf-8'))
                return True
            except Exception as e:
                print(f"Error enviando: {e}")
        return False

    # --- GESTIÓN DE ARCHIVOS (JSON) ---
    def save_routine_to_file(self, filename, routine_data):
        try:
            with open(filename, 'w') as f:
                json.dump(routine_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error guardando archivo: {e}")
            return False

    def load_routine_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando archivo: {e}")
            return None