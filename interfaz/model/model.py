import serial # Importa la librería pyserial para la comunicación física por puertos COM
import serial.tools.list_ports # Herramienta específica para buscar y listar los puertos disponibles en la PC
import json # Importa la librería para manejar la lectura y escritura de archivos en formato JSON

class Model:
    # El Modelo se encarga EXCLUSIVAMENTE de los datos y la conexión con el hardware (STM32).
    # No sabe nada sobre botones, ventanas o layouts.
    
    def __init__(self):
        self.serial_port = None # Inicialmente no hay ningún puerto conectado (objeto nulo)
        self.baud_rate = 115200 # Velocidad de comunicación en baudios (debe coincidir exactamente con el firmware del STM32)

    def get_available_ports(self):
        # Obtiene una lista de todos los dispositivos conectados a los puertos serie
        ports = serial.tools.list_ports.comports()
        # Retorna solo los nombres de los puertos (ej. 'COM3', 'COM8') extrayendo el atributo 'device' de cada puerto encontrado
        return [port.device for port in ports]

    def connect_port(self, port_name):
        try:
            # Si ya hay un puerto abierto, lo cerramos primero para evitar conflictos o bloqueos
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                
            # Intenta abrir el puerto especificado con la velocidad definida y un tiempo de espera (timeout) de 1 segundo
            self.serial_port = serial.Serial(port_name, self.baud_rate, timeout=1.0)
            return True # Retorna True si la conexión fue exitosa
        except serial.SerialException as e:
            # Si ocurre un error (ej. puerto ocupado por otro programa o placa desconectada), lo imprime en la terminal
            print(f"Error abriendo puerto: {e}")
            return False # Retorna False indicando que falló la conexión

    def disconnect_port(self):
        # Verifica si existe un objeto serial creado y si está actualmente abierto
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close() # Cierra la conexión física con el puerto USB
            self.serial_port = None  # Borra la referencia al objeto para liberar memoria y reiniciar el estado interno

    def is_connected(self):
        # Retorna True solo si el puerto está instanciado (no es None) y la conexión está efectivamente abierta
        return self.serial_port is not None and self.serial_port.is_open

    def send_data(self, data):
        # Primero verifica que estemos conectados antes de intentar enviar cualquier trama
        if self.is_connected():
            try:
                # Asegura que el comando termine con un salto de línea ('\n'). 
                # Esto es vital para que el buffer del STM32 sepa que terminó de recibir la trama.
                if not data.endswith('\n'):
                    data += '\n'
                # Convierte el string de texto de Python a bytes (codificación utf-8) y lo envía por el puerto serie
                self.serial_port.write(data.encode('utf-8'))
                return True # Envío exitoso
            except Exception as e:
                # Captura cualquier error durante la transmisión (ej. si el cable se desconecta justo al enviar)
                print(f"Error enviando: {e}")
        # Si no estaba conectado o hubo un error en el try, retorna False
        return False

    # --- GESTIÓN DE ARCHIVOS (JSON) ---
    def save_routine_to_file(self, filename, routine_data):
        try:
            # Abre (o crea si no existe) el archivo en modo escritura ('w' de write)
            with open(filename, 'w') as f:
                # Convierte la lista/diccionario de Python (routine_data) a formato de texto JSON y lo guarda en el archivo (f).
                # El parámetro indent=4 agrega saltos de línea y espacios para que el archivo sea legible para un humano.
                json.dump(routine_data, f, indent=4)
            return True # Guardado exitoso
        except Exception as e:
            # Si falla (ej. permisos insuficientes de Windows o disco lleno), atrapa el error
            print(f"Error guardando archivo: {e}")
            return False

    def load_routine_from_file(self, filename):
        try:
            # Abre el archivo en modo lectura ('r' de read)
            with open(filename, 'r') as f:
                # Lee el texto JSON del archivo y lo convierte de vuelta a objetos nativos de Python (listas/diccionarios)
                return json.load(f)
        except Exception as e:
            # Si falla (ej. el archivo JSON está mal escrito, corrupto, o fue borrado), atrapa el error
            print(f"Error cargando archivo: {e}")
            return None # Retorna None para avisarle al Controlador que la carga fracasó