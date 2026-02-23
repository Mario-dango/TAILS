"""
TEST UI EXECUTION - Pruebas visuales de reproducción de rutinas
"""
import pytest
from PyQt5.QtCore import Qt
from controller.main_controller import MainController
from unittest.mock import MagicMock

def test_load_and_play_routine(qtbot):
    """
    Verifica que al dar Play, la UI reaccione y cambie de estado.
    """
    # 1. Configuración inicial
    controller = MainController()
    qtbot.addWidget(controller.view)
    
    # --- EFECTO VISUAL ---
    controller.view.show()
    controller.view.tabs.setCurrentIndex(2) # Cambiamos a la pestaña "Ejecución"
    qtbot.wait(1000)
    
    # 2. Mockeamos la conexión para habilitar los controles
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)
    
    # 3. MOCK DEL HARDWARE: Anulamos la función de enviar datos al COM real.
    # MagicMock() crea un "agujero negro": la función se llama, pero no hace nada ni da error.
    controller.connection_mgr.send_command = MagicMock()
    
    # 4. Inyectamos una rutina artificial en la memoria del gestor
    rutina_test = [
        {'type': 'MOV', 'x': 10, 'y': 10, 'z': 10},
        {'type': 'MOV', 'x': 20, 'y': 20, 'z': 20}
    ]
    controller.execution_mgr.loaded_routine = rutina_test
    
    # 5. Verificamos que al inicio el sistema NO esté ejecutando
    assert controller.execution_mgr.is_executing is False
    
    # 6. ACCIÓN: Clic en el botón verde de PLAY
    qtbot.mouseClick(controller.view.btn_play, Qt.LeftButton)
    qtbot.wait(2000) # Pausa de 2 segundos. ¡Verás cómo aparece "INICIANDO EJECUCIÓN" en la consola!
    
    # 7. VERIFICACIÓN: El sistema interno ahora sabe que está ejecutando
    assert controller.execution_mgr.is_executing is True
    
    # Obtenemos el texto de la terminal de log y buscamos la frase clave
    log_text = controller.view.txt_run_log.toPlainText()
    assert "INICIANDO EJECUCIÓN" in log_text
    
    # 8. LIMPIEZA (Teardown): Apagamos el metrónomo para que no interfiera con la siguiente prueba
    controller.execution_mgr.run_timer.stop()

def test_stop_button(qtbot):
    """
    Verifica que el botón Stop corte la rutina y reinicie la barra de progreso.
    """
    # 1. Configuración inicial
    controller = MainController()
    qtbot.addWidget(controller.view)
    
    # --- EFECTO VISUAL ---
    controller.view.show()
    controller.view.tabs.setCurrentIndex(2)
    
    # 2. Desbloqueo y anulación de puerto serie
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)
    controller.connection_mgr.send_command = MagicMock()
    
    # 3. Forzamos un estado "a mitad de ejecución"
    controller.execution_mgr.is_executing = True
    controller.execution_mgr.execution_index = 5 # Simula que va por el paso 5
    controller.view.progress_bar.setValue(50)    # Simulamos barra al 50%
    qtbot.wait(1500) # Verás la barra a la mitad
    
    # 4. ACCIÓN: Clic en DETENER
    qtbot.mouseClick(controller.view.btn_stop_run, Qt.LeftButton)
    qtbot.wait(1500) # Verás la barra de progreso volver a 0 de golpe!
    
    # 5. VERIFICACIÓN
    assert controller.execution_mgr.is_executing is False
    assert controller.execution_mgr.execution_index == 0
    assert controller.view.progress_bar.value() == 0