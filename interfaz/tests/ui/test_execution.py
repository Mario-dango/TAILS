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

def test_la_espera_del_paso_alarga_el_metronomo(qtbot):
    """Cada paso puede pedir su propia pausa: el timer se reprograma con ella.

    El metrónomo era un QTimer repetitivo de 1500 ms fijos, así que no había
    forma de que un paso esperara más que otro. Ahora es de un solo disparo y se
    agenda con INTERVALO_BASE_MS + la espera del paso recién enviado.
    """
    from controller.execution_manager import INTERVALO_BASE_MS

    controller = MainController()
    qtbot.addWidget(controller.view)
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)
    controller.connection_mgr.send_command = MagicMock()

    gestor = controller.execution_mgr
    gestor.loaded_routine = [
        {'type': 'MOV', 'x': 10, 'y': 10, 'z': 10, 't': 2},   # 2 s de espera
        {'type': 'MOV', 'x': 20, 'y': 20, 'z': 20},           # sin clave 't'
    ]
    gestor.is_executing = True

    gestor.execute_next_step()
    assert gestor.run_timer.isSingleShot(), (
        "El metrónomo se reprograma paso a paso: no puede ser repetitivo.")
    assert gestor.run_timer.interval() == INTERVALO_BASE_MS + 2000

    gestor.execute_next_step()
    assert gestor.run_timer.interval() == INTERVALO_BASE_MS, (
        "Una rutina vieja (sin 't') conserva el ritmo de siempre.")

    gestor.run_timer.stop()


def test_la_espera_aparece_en_la_descripcion_del_paso(qtbot):
    """El log y el panel Secuencia tienen que mostrar la pausa cargada."""
    controller = MainController()
    qtbot.addWidget(controller.view)
    gestor = controller.execution_mgr

    paso = {'type': 'MOV', 'x': 1, 'y': 2, 'z': 3, 'v': 50, 't': 1.5}
    assert "espera 1.5 s" in gestor.describir_paso(0, paso)
    assert "espera" not in gestor.describir_paso(0, {'type': 'MOV', 'x': 1,
                                                    'y': 2, 'z': 3})

    controller.view.tab_run.set_sequence([paso])
    assert "+1.5s" in controller.view.tab_run.list_steps.item(0).text()
