"""
Archivo principal de ejecución (Entry Point) para T.A.I.L.S.
(Technical Articulated Intelligent Linkage System).

Este proyecto sigue estrictamente el patrón de arquitectura de software MVC 
(Modelo-Vista-Controlador) para separar la lógica de la interfaz:

- MODELO (model.py): Capa de Datos y Hardware. 
  Gestiona la comunicación física por puerto Serial (STM32) y la escritura/lectura 
  de rutinas guardadas en archivos .json. No tiene idea de que existe una interfaz.

- VISTA (view.py): Capa de Interfaz Gráfica (GUI). 
  Construye la ventana principal, pestañas, botones, estilos CSS y carga los iconos. 
  Es "tonta", no toma decisiones ni procesa datos; solo dibuja la pantalla.

- CONTROLADOR (controller.py): El "Cerebro" u Orquestador.
  Conecta la Vista con el Modelo. Escucha cuando el usuario presiona un botón en la Vista, 
  y le ordena al Modelo qué hacer (ej. enviar un comando al robot). También actualiza 
  la Vista (ej. LCDs, terminal) basándose en las respuestas del Modelo.
"""

import sys # Proporciona variables y funciones para interactuar con el sistema operativo (ej. argumentos y cierre de procesos)
from PyQt5.QtWidgets import QApplication # Clase fundamental de PyQt5 que gestiona el flujo de control, eventos y configuración de la GUI
from controller.main_controller import MainController # Solo necesitamos importar el Controlador, él se encarga de inicializar el resto del sistema

# Verificamos si este script se está ejecutando directamente como programa principal
if __name__ == "__main__":
    
    # 1. Inicializamos la aplicación gráfica de Qt. 
    # sys.argv pasa los posibles argumentos de la línea de comandos al motor de Qt.
    app = QApplication(sys.argv)
    
    # 2. Instanciamos el Controlador principal.
    # Al momento de crearse, el Controller automáticamente en su __init__:
    #   - Instancia self.model = Model()
    #   - Instancia self.view = View()
    #   - Vincula todas las señales (clics) con sus funciones (slots)
    #   - Llama a self.view.show() para desplegar la ventana en pantalla
    controller = MainController()
    
    # 3. Iniciamos el bucle de eventos principal (Event Loop).
    # app.exec_() bloquea el script aquí, manteniendo la ventana abierta y "escuchando" 
    # continuamente los eventos del usuario (mouse, teclado, etc.).
    # sys.exit() garantiza que cuando app.exec_() termine (porque el usuario cerró la ventana),
    # el proceso de Python se destruya limpiamente en el administrador de tareas de Windows.
    sys.exit(app.exec_())