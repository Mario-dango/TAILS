import sys
from PyQt5.QtWidgets import QApplication
from controller import Controller

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Instanciamos el controlador, que a su vez crea el Modelo y la Vista
    controller = Controller()
    
    sys.exit(app.exec_())