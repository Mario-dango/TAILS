"""
TEST PARSERS - Pruebas de la lógica de decodificación de tramas (Strings)
"""
import pytest
from unittest.mock import MagicMock
from controller.connection_manager import ConnectionManager

@pytest.fixture
def mock_app():
    """Crea un controlador falso (Mock) para aislar el ConnectionManager"""
    app_mock = MagicMock()
    # Simulamos que la View y sus elementos existen
    app_mock.view.lcd_x = MagicMock()
    app_mock.view.lcd_y = MagicMock()
    app_mock.view.lcd_z = MagicMock()
    app_mock.view.lbl_status_home = MagicMock()
    app_mock.view.lbl_status_wait = MagicMock()
    app_mock.view.led_x = MagicMock()
    app_mock.view.led_y = MagicMock()
    app_mock.view.led_z = MagicMock()
    app_mock.view.btn_home = MagicMock()
    
    # Datos globales iniciales
    app_mock.current_pos = {'x': 0, 'y': 0, 'z': 0}
    return app_mock

def test_process_valid_status_string(mock_app):
    """
    CP-01: Verificar que una trama STATUS estándar actualice la memoria global
    """
    # Instanciamos el manager pasándole el jefe falso
    manager = ConnectionManager(mock_app)
    
    # Trama simulada que llegaría del STM32
    # X=150, Y=20, Z=10, Sensores=000, Calibrado=1, Moviendo=0
    trama = "STATUS|X:150|Y:20|Z:10|S:000|C:1|M:0"
    
    # Ejecutamos la función a probar
    manager.process_serial_data(trama)
    
    # Verificaciones (Asserts)
    # 1. ¿Se actualizó la memoria global del jefe?
    assert mock_app.current_pos['x'] == 150
    assert mock_app.current_pos['y'] == 20
    assert mock_app.current_pos['z'] == 10
    
    # 2. ¿Se mandó a actualizar el LCD visual?
    mock_app.view.lcd_x.display.assert_called_with(150)

def test_process_corrupted_string(mock_app):
    """
    CP-02: Verificar que si llega basura, el programa no crashee
    """
    manager = ConnectionManager(mock_app)
    trama_basura = "ASDF|X:??|@#$%" # Trama corrupta
    
    try:
        manager.process_serial_data(trama_basura)
    except Exception:
        pytest.fail("El parser no debería lanzar excepción con tramas corruptas")