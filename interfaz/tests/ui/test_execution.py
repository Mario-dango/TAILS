"""
TEST UI EXECUTION - Pruebas del ciclo de reproducción de rutinas
"""
import pytest
from PyQt5.QtCore import Qt
from controller.main_controller import MainController

def test_load_and_play_routine(qtbot):
    """
    CP-UI-03: Cargar rutina manualmente y dar Play
    """
    controller = MainController()
    qtbot.addWidget(controller.view)
    controller.model.is_connected = lambda: True
    
    # 1. Inyectamos una rutina "a la fuerza" en la memoria
    # (Para no depender del diálogo de abrir archivo de Windows)
    rutina_test = [
        {'type': 'MOV', 'x': 10, 'y': 10, 'z': 10},
        {'type': 'MOV', 'x': 20, 'y': 20, 'z': 20}
    ]
    controller.execution_mgr.loaded_routine = rutina_test
    
    # 2. Verificar estado inicial
    assert controller.execution_mgr.is_executing is False
    
    # 3. ACCIÓN: Click en PLAY
    qtbot.mouseClick(controller.view.btn_play, Qt.LeftButton)
    
    # 4. VERIFICACIÓN
    assert controller.execution_mgr.is_executing is True
    # Verificamos que el log de ejecución haya escrito algo
    log_text = controller.view.txt_run_log.toPlainText()
    assert "INICIANDO EJECUCIÓN" in log_text

def test_stop_button(qtbot):
    """
    CP-UI-04: El botón Stop debe detener el timer y resetear índices
    """
    controller = MainController()
    qtbot.addWidget(controller.view)
    controller.model.is_connected = lambda: True
    
    # Estado inicial simulado: Corriendo
    controller.execution_mgr.is_executing = True
    controller.execution_mgr.execution_index = 5
    
    # Click Stop
    qtbot.mouseClick(controller.view.btn_stop_run, Qt.LeftButton)
    
    # Asserts
    assert controller.execution_mgr.is_executing is False
    assert controller.execution_mgr.execution_index == 0
    # La barra de progreso debe volver a 0
    assert controller.view.progress_bar.value() == 0