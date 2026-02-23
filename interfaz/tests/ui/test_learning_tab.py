"""
TEST UI LEARNING - Pruebas automatizadas sobre la pestaña de Aprendizaje
"""
import pytest
from PyQt5.QtCore import Qt
from controller.main_controller import MainController

def test_add_point_to_table(qtbot, qapp, tmp_path):
    """
    CP-UI-01: Simular que el usuario mueve el robot y guarda un punto.
    """
    # 1. Levantar la aplicación completa
    controller = MainController()
    qtbot.addWidget(controller.view) # Registramos la ventana para que el bot la vea
    
    # 2. MOCK: Forzar estado "Conectado" para que los botones funcionen
    # Mentimos diciendo que el puerto está abierto
    controller.model.is_connected = lambda: True 
    
    # 3. Preparar escenario: Definir una posición actual simulada
    controller.current_pos = {'x': 100, 'y': 50, 'z': 25}
    controller.gripper_state = 'C'
    
    # 4. ACCIÓN: Hacer clic en el botón "Guardar Punto"
    # Usamos qtbot para simular el clic izquierdo del mouse
    qtbot.mouseClick(controller.view.btn_add_point, Qt.LeftButton)
    
    # 5. VERIFICACIÓN: ¿Apareció la fila en la tabla?
    tabla = controller.view.table_points
    assert tabla.rowCount() == 1, "La tabla debería tener 1 fila."
    
    # Verificar contenido de las celdas
    item_x = tabla.item(0, 0).text() # Fila 0, Columna 0 (X)
    item_g = tabla.item(0, 3).text() # Fila 0, Columna 3 (Garra)
    
    assert item_x == "100"
    assert item_g == "C"

def test_clear_table_logic(qtbot):
    """
    CP-UI-02: Verificar botón de limpiar tabla
    """
    controller = MainController()
    qtbot.addWidget(controller.view)
    
    # Agregamos 3 filas manualmente (setup)
    controller.view.table_points.setRowCount(3)
    assert controller.view.table_points.rowCount() == 3
    
    # Como el botón "Limpiar Todo" lanza un Popup de confirmación, 
    # mockeamos la respuesta del cuadro de diálogo para que diga "YES" automáticamente
    from PyQt5.QtWidgets import QMessageBox
    # Inyectamos una función que reemplace al QMessageBox.question original
    QMessageBox.question = lambda *args: QMessageBox.Yes
    
    # Click en limpiar
    controller.model.is_connected = lambda: True
    qtbot.mouseClick(controller.view.btn_clear_all, Qt.LeftButton)
    
    # Assert
    assert controller.view.table_points.rowCount() == 0