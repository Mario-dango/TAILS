"""
TEST UI LEARNING - Pruebas visuales automatizadas sobre la pestaña de Aprendizaje
"""
import pytest
from PyQt5.QtCore import Qt
from controller.main_controller import MainController
from controller.learning_manager import COL_NUM, COL_NAME, COL_X, COL_G, COL_T

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
    
    # 7. VERIFICACIÓN (Asserts): El programa comprueba que el clic funcionó.
    # Las columnas son ["#", "NOMBRE", "X", "Y", "Z", "GARRA", "VEL %"]: la 0 es el
    # número de paso, la 1 el nombre opcional, y los datos del movimiento arrancan
    # en la 2 (ver COL_* en controller/learning_manager.py).
    tabla = controller.view.table_points
    assert tabla.rowCount() == 1, "La tabla debería tener 1 fila."
    assert tabla.item(0, COL_NUM).text() == "1", "La numeración de la fila no coincide."
    assert tabla.item(0, COL_X).text() == "100", "El valor X en la tabla no coincide."
    assert tabla.item(0, COL_G).text() == "C", "El estado de la garra en la tabla no coincide."
    assert tabla.item(0, COL_NAME).text() == "", "El nombre del punto nace vacío (es opcional)."

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

def _capturar(controller, qtbot, x, y, z, nombre=""):
    """Agrega un punto a la tabla como lo haría el operador con 'Capturar punto'."""
    controller.current_pos = {'x': x, 'y': y, 'z': z}
    qtbot.mouseClick(controller.view.btn_add_point, Qt.LeftButton)
    if nombre:
        fila = controller.view.table_points.rowCount() - 1
        controller.view.table_points.item(fila, COL_NAME).setText(nombre)


def test_reordenar_puntos_de_la_rutina(qtbot):
    """El orden de la tabla ES el orden de ejecución: tiene que poder cambiarse.

    Antes la única forma de corregir un punto capturado fuera de lugar era
    borrarlo y volver a llevar el brazo físicamente hasta esa posición.
    """
    controller = MainController()
    qtbot.addWidget(controller.view)
    controller.view.tabs.setCurrentIndex(1)
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)

    _capturar(controller, qtbot, 10, 1, 1, nombre="primero")
    _capturar(controller, qtbot, 20, 2, 2, nombre="segundo")
    _capturar(controller, qtbot, 30, 3, 3, nombre="tercero")

    tabla = controller.view.table_points
    assert tabla.rowCount() == 3

    # Bajamos el primer punto un lugar
    tabla.selectRow(0)
    qtbot.mouseClick(controller.view.btn_move_down, Qt.LeftButton)

    assert tabla.item(0, COL_NAME).text() == "segundo"
    assert tabla.item(1, COL_NAME).text() == "primero"
    assert tabla.item(0, COL_X).text() == "20"
    assert tabla.item(1, COL_X).text() == "10"
    # La selección viaja con el punto movido, no se queda en la fila 0.
    assert tabla.currentRow() == 1
    # La columna "#" se renumera: es sólo el orden, no un identificador.
    assert [tabla.item(f, COL_NUM).text() for f in range(3)] == ["1", "2", "3"]

    # Y lo volvemos a subir: la rutina queda como estaba
    qtbot.mouseClick(controller.view.btn_move_up, Qt.LeftButton)
    assert tabla.item(0, COL_NAME).text() == "primero"
    assert tabla.currentRow() == 0


def test_los_botones_de_reordenar_se_apagan_en_los_extremos(qtbot):
    """Subir en la primera fila (o bajar en la última) no tiene sentido."""
    controller = MainController()
    qtbot.addWidget(controller.view)
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)

    vista = controller.view
    # Sin puntos no hay nada que mover
    assert not vista.btn_move_up.isEnabled()
    assert not vista.btn_move_down.isEnabled()

    _capturar(controller, qtbot, 10, 1, 1)
    _capturar(controller, qtbot, 20, 2, 2)

    vista.table_points.selectRow(0)
    assert not vista.btn_move_up.isEnabled(), "Primera fila: no se puede subir."
    assert vista.btn_move_down.isEnabled()

    vista.table_points.selectRow(1)
    assert vista.btn_move_up.isEnabled()
    assert not vista.btn_move_down.isEnabled(), "Última fila: no se puede bajar."


def test_borrar_una_fila_reindexa_los_valores_previos(qtbot):
    """El mapa de 'último valor válido' se indexa por número de fila.

    Si no se reconstruye tras un borrado, revertir una edición inválida
    restauraba el dato que antes vivía en OTRA fila.
    """
    controller = MainController()
    qtbot.addWidget(controller.view)
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)

    _capturar(controller, qtbot, 10, 1, 1)
    _capturar(controller, qtbot, 20, 2, 2)

    controller.view.table_points.selectRow(0)
    qtbot.mouseClick(controller.view.btn_del_point, Qt.LeftButton)

    previos = controller.learning_mgr._valores_previos
    assert previos[(0, COL_X)] == "20", (
        "Tras borrar la fila 0, la clave (0, X) debe apuntar al punto que quedó.")
    assert (1, COL_X) not in previos, "No deben quedar claves de filas inexistentes."


def test_la_espera_por_paso_se_guarda_en_el_json(qtbot, monkeypatch):
    """La pausa de cada paso viaja al archivo en la clave 't', en segundos.

    Es el dato que permite que la rutina espere a que la garra termine de cerrar
    o a que la pieza se asiente antes de seguir: si no llega al JSON, la
    ejecución vuelve al ritmo fijo de siempre.
    """
    controller = MainController()
    qtbot.addWidget(controller.view)
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)

    _capturar(controller, qtbot, 10, 20, 30, nombre="tomar")
    _capturar(controller, qtbot, 40, 50, 60)

    tabla = controller.view.table_points
    # El paso nace sin espera y se carga a mano, como lo haría el operador.
    assert tabla.item(0, COL_T).text() == "0.0"
    tabla.item(0, COL_T).setText("2,5")     # con coma: se normaliza a 2.5

    guardado = {}
    monkeypatch.setattr(
        "controller.learning_manager.QFileDialog.getSaveFileName",
        lambda *a, **k: ("rutina_test.json", ""))
    monkeypatch.setattr(
        controller.model, "save_routine_to_file",
        lambda ruta, datos: guardado.update(ruta=ruta, datos=datos) or True)

    qtbot.mouseClick(controller.view.btn_save_file, Qt.LeftButton)

    pasos = guardado["datos"]
    assert pasos[0]["t"] == 2.5, "El primer paso tiene que llevar su espera."
    assert "t" not in pasos[1], (
        "Sin espera no se escribe la clave: un 't': 0 en cada paso sólo "
        "ensucia el archivo.")


def test_una_espera_fuera_de_rango_se_revierte(qtbot, monkeypatch):
    """La celda de espera tiene tope (ESPERA_MAXIMA_S): más que eso se rechaza."""
    from PyQt5.QtWidgets import QMessageBox
    from view.tab_teaching import ESPERA_MAXIMA_S

    controller = MainController()
    qtbot.addWidget(controller.view)
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)

    avisos = []
    monkeypatch.setattr(QMessageBox, "warning",
                        lambda *a, **k: avisos.append(a) or QMessageBox.Ok)

    _capturar(controller, qtbot, 10, 20, 30)
    tabla = controller.view.table_points

    tabla.item(0, COL_T).setText("1.5")
    assert tabla.item(0, COL_T).text() == "1.5"

    tabla.item(0, COL_T).setText(str(ESPERA_MAXIMA_S + 10))
    assert tabla.item(0, COL_T).text() == "1.5", (
        "Una espera fuera de rango vuelve al último valor válido.")
    assert avisos, "Y se le avisa al operador por qué no se tomó el valor."
