import serial
import serial.tools.list_ports

class Model:
    def __init__(self):
        self.ports = []
        self.serial_port = None

    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        self.ports = [port.device for port in ports]
        return self.ports

    def open_serial_port(self, port):
        try:
            # Agregamos timeout para que no se congele si no hay datos
            self.serial_port = serial.Serial(port, 115200, timeout=0.1)
            return self.serial_port  # <--- ¡ESTO FALTABA! Retornar el objeto
        except serial.SerialException as e:
            print(f"Error al abrir el puerto: {e}")
            self.serial_port = None
            return None

    def send_data(self, port, data):
        if self.serial_port is not None and self.serial_port.is_open:
            try:
                # Agregamos salto de línea (\n) al final para delimitar el comando
                full_command = data + "\n"
                string_byte = full_command.encode('utf-8')
                self.serial_port.write(string_byte)
            except Exception as e:
                print(f"Error enviando datos: {e}")
    
    def receive_data(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                # read_all a veces retorna bytes vacíos, decodificamos con ignorar errores
                data = self.serial_port.read_all()
                if data:
                    return data.decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"Error recibiendo: {e}")
        return ""
    
    def close_port(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None