"""
TEST UI LEARNING - Pruebas visuales automatizadas sobre la pestaña de Aprendizaje
"""
import pytest
from PyQt5.QtCore import Qt
from controller.main_controller import MainController

def test_add_point_to_table(qtbot, qapp, tmp_path):
    """
    Simula visualmente que el usuario mueve el robot y guarda un punto en la tabla.
    """
    # 1. Instanciamos el Controlador (que a su vez crea el Modelo y la Vista)
    controller = MainController()
    
    # 2. Registramos la ventana en qtbot para que pueda interactuar con ella
    qtbot.addWidget(controller.view)
    
    # --- EFECTO VISUAL (Estilo Selenium) ---
    controller.view.show()          # Forzamos a que la ventana aparezca en pantalla
    controller.view.tabs.setCurrentIndex(1) # Cambiamos a la pestaña "Aprendizaje" (índice 1)
    qtbot.wait(1000)                # Pausa de 1 segundo para que el humano vea la UI inicial
    # ---------------------------------------

    # 3. Forzamos la conexión lógica (Mentimos al sistema)
    # Reemplazamos la función real por una función anónima (lambda) que siempre dice True
    controller.model.is_connected = lambda: True 
    
    # 4. Actualizamos la Interfaz Gráfica para que desbloquee los botones grises
    controller.connection_mgr.update_ui_connection_state(True)
    qtbot.wait(1000)                # Pausa para ver cómo los botones se pintan y habilitan

    # 5. Preparamos el escenario simulando que el robot se movió a estas coordenadas
    controller.current_pos = {'x': 100, 'y': 50, 'z': 25}
    controller.gripper_state = 'C'  # Garra cerrada
    
    # 6. ACCIÓN: El bot hace clic izquierdo en el botón "Guardar Punto"
    qtbot.mouseClick(controller.view.btn_add_point, Qt.LeftButton)
    qtbot.wait(1500)                # Pausa de 1.5s para que veamos cómo aparece la nueva fila en la tabla!
    
    # 7. VERIFICACIÓN (Asserts): El programa comprueba que el clic funcionó
    tabla = controller.view.table_points
    assert tabla.rowCount() == 1, "La tabla debería tener 1 fila."
    assert tabla.item(0, 0).text() == "100", "El valor X en la tabla no coincide."
    assert tabla.item(0, 3).text() == "C", "El estado de la garra en la tabla no coincide."

def test_clear_table_logic(qtbot):
    """
    Verifica visualmente el funcionamiento del botón rojo 'Limpiar Todo'.
    """
    # 1. Preparación básica
    controller = MainController()
    qtbot.addWidget(controller.view)
    
    # --- EFECTO VISUAL ---
    controller.view.show()
    controller.view.tabs.setCurrentIndex(1)
    qtbot.wait(500)
    
    # 2. Agregamos 3 filas "falsas" a la tabla directamente en la UI
    controller.view.table_points.setRowCount(3)
    qtbot.wait(1000) # Pausa para que veas las 3 filas vacías creadas
    
    # 3. MOCK DEL POPUP: Interceptamos la ventana de "¿Estás seguro de borrar?"
    # Si no hacemos esto, el test se quedaría pausado para siempre esperando que un humano haga clic en "Sí".
    from PyQt5.QtWidgets import QMessageBox
    QMessageBox.question = lambda *args: QMessageBox.Yes # Obligamos a que responda "Sí"
    
    # 4. Simulamos conexión y desbloqueamos botones
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)
    
    # 5. ACCIÓN: El bot hace clic en "Limpiar Todo"
    qtbot.mouseClick(controller.view.btn_clear_all, Qt.LeftButton)
    qtbot.wait(1000) # Pausa para ver cómo desaparecen las filas de golpe!
    
    # 6. VERIFICACIÓN
    assert controller.view.table_points.rowCount() == 0, "La tabla debería estar vacía."