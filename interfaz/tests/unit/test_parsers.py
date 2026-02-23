"""
TEST PARSERS - Pruebas de la lógica de decodificación de tramas (Strings)
"""
import pytest
from unittest.mock import MagicMock
from controller.connection_manager import ConnectionManager

@pytest.fixture
def mock_app():
    """
    Fixture: Crea un 'MainController' falso (Mock).
    En pruebas unitarias estrictas, no queremos abrir ventanas gráficas.
    Usamos MagicMock para crear objetos vacíos que el ConnectionManager pueda 
    modificar sin que Python tire error de 'objeto no encontrado'.
    """
    app_mock = MagicMock()
    
    # Fingimos que todos estos componentes de la interfaz existen
    app_mock.view.lcd_x = MagicMock()
    app_mock.view.lcd_y = MagicMock()
    app_mock.view.lcd_z = MagicMock()
    app_mock.view.lbl_status_home = MagicMock()
    app_mock.view.lbl_status_wait = MagicMock()
    app_mock.view.led_x = MagicMock()
    app_mock.view.led_y = MagicMock()
    app_mock.view.led_z = MagicMock()
    app_mock.view.btn_home = MagicMock()
    
    # Creamos la memoria global inicial
    app_mock.current_pos = {'x': 0, 'y': 0, 'z': 0}
    
    return app_mock

def test_process_valid_status_string(mock_app):
    """
    Verifica que si el STM32 manda una trama válida, el parser separe bien
    los números y mande a actualizar la pantalla.
    """
    # 1. PREPARACIÓN: Instanciamos el manager entregándole nuestro jefe falso
    manager = ConnectionManager(mock_app)
    
    # Simulamos el String exacto que escupiría el cable USB
    trama = "STATUS|X:150|Y:20|Z:10|S:000|C:1|M:0"
    
    # 2. ACCIÓN: Forzamos al manager a procesar este string
    manager.process_serial_data(trama)
    
    # 3. VERIFICACIÓN
    # Comprobamos que el parser haya extraído el 150, 20 y 10 y los haya guardado
    assert mock_app.current_pos['x'] == 150, "El parser falló en extraer la X."
    assert mock_app.current_pos['y'] == 20, "El parser falló en extraer la Y."
    assert mock_app.current_pos['z'] == 10, "El parser falló en extraer la Z."
    
    # Comprobamos que el manager le haya dado la orden a la pantalla (LCD) de mostrar el 150.
    # assert_called_with es una magia de MagicMock para saber si una función fue invocada.
    mock_app.view.lcd_x.display.assert_called_with(150)

def test_process_corrupted_string(mock_app):
    """
    Prueba de Resiliencia: Si el cable hace falso contacto y llega basura,
    el software debe ignorarla, no cerrarse inesperadamente (Crash).
    """
    # 1. Preparación
    manager = ConnectionManager(mock_app)
    
    # Un string que no cumple el formato esperado
    trama_basura = "ASDF|X:??|@#$%" 
    
    # 2. Acción y Verificación combinadas
    try:
        # Si el bloque try/except dentro de process_serial_data funciona bien,
        # esto no debería hacer nada.
        manager.process_serial_data(trama_basura)
    except Exception:
        # Si llega hasta aquí, significa que la excepción "rompió" el método
        # y llegó hasta la prueba, por lo que fallamos el test manualmente.
        pytest.fail("El parser no manejó correctamente la trama corrupta y lanzó una excepción.")