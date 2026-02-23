"""
MOCK STM32 - Emulador de Hardware para T.A.I.L.S.
Simula el comportamiento del microcontrolador respondiendo a comandos G-Code/Custom
y emitiendo tramas de telemetría (STATUS).
"""

import serial
import time
import threading

class MockSTM32:
    def __init__(self, port='COM9', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.is_running = False
        
        # Estado interno simulado del robot
        self.x = 0
        self.y = 0
        self.z = 0
        self.calibrated = 0 # 0 = Falso, 1 = Verdadero
        self.moving = 0     # 0 = Falso, 1 = Verdadero
        
        # Sensores (Finales de carrera falsos)
        self.sx = 0
        self.sy = 0
        self.sz = 0

    def start(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.is_running = True
            print(f"[MOCK] STM32 Simulado escuchando en {self.port} a {self.baudrate} baudios...")
            
            # Hilo para leer comandos de T.A.I.L.S.
            listen_thread = threading.Thread(target=self.listen_commands)
            listen_thread.daemon = True
            listen_thread.start()
            
            # Bucle principal enviando telemetría
            self.send_telemetry_loop()
            
        except serial.SerialException as e:
            print(f"[ERROR] No se pudo abrir {self.port}. ¿Creaste el par de puertos virtuales?")

    def listen_commands(self):
        while self.is_running:
            if self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8').strip()
                print(f"[RX de TAILS] {line}")
                self.process_command(line)

    def process_command(self, cmd):
        # Simular Homing
        if cmd == ":-H":
            print("[MOCK] Ejecutando Homing... simulando demora de 2 segundos.")
            self.moving = 1
            time.sleep(2) # Simula el tiempo que tarda el robot físico
            self.x, self.y, self.z = 0, 0, 0
            self.calibrated = 1
            self.moving = 0
            print("[MOCK] Homing completado.")
            
        # Simular Movimiento absoluto (Jogging o Rutina)
        elif cmd.startswith(":#X") or cmd.startswith(":#Y") or cmd.startswith(":#Z"):
            print("[MOCK] Moviendo motores...")
            self.moving = 1
            time.sleep(0.5) # Simula el viaje de los motores
            
            # Un parser súper básico para actualizar las variables del mock
            import re
            match_x = re.search(r'X(\d+)', cmd)
            match_y = re.search(r'Y(\d+)', cmd)
            match_z = re.search(r'Z(\d+)', cmd)
            
            if match_x: self.x = int(match_x.group(1))
            if match_y: self.y = int(match_y.group(1))
            if match_z: self.z = int(match_z.group(1))
            
            self.moving = 0

    def send_telemetry_loop(self):
        """Envía el estado del robot 10 veces por segundo"""
        try:
            while self.is_running:
                # Formato: STATUS|X:100|Y:0|Z:50|S:001|C:1|M:0
                status_str = f"STATUS|X:{self.x}|Y:{self.y}|Z:{self.z}|S:{self.sx}{self.sy}{self.sz}|C:{self.calibrated}|M:{self.moving}\n"
                self.serial_conn.write(status_str.encode('utf-8'))
                time.sleep(0.1) # 10Hz
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        print("[MOCK] Apagando simulador...")
        self.is_running = False
        if self.serial_conn:
            self.serial_conn.close()

if __name__ == "__main__":
    # Inicia el mock en el puerto COM9
    mock = MockSTM32(port='COM9')
    mock.start()