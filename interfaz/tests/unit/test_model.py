"""
TEST MODEL - Pruebas unitarias para la capa de datos y hardware
"""
import pytest
import os
from model.model import Model

def test_save_and_load_routine(tmp_path):
    """
    Caso de Prueba: Verificar que el Modelo pueda guardar una rutina en JSON 
    y que al cargarla, los datos sean exactamente los mismos.
    """
    # 1. Preparación (Arrange)
    modelo = Model()
    
    # Creamos una rutina falsa de prueba
    rutina_falsa = [
        {"type": "MOV", "x": 90, "y": 45, "z": 0, "g": "A"},
        {"type": "MOV", "x": 180, "y": 90, "z": 50, "g": "C"}
    ]
    
    # Usamos tmp_path para que cree un archivo en una carpeta temporal segura
    archivo_prueba = tmp_path / "rutina_test.json"
    
    # 2. Acción (Act)
    # Guardamos
    resultado_guardado = modelo.save_routine_to_file(archivo_prueba, rutina_falsa)
    # Volvemos a cargar
    rutina_cargada = modelo.load_routine_from_file(archivo_prueba)
    
    # 3. Verificación (Assert)
    assert resultado_guardado is True, "El método debería retornar True al guardar con éxito."
    assert os.path.exists(archivo_prueba), "El archivo físico debe existir en el disco."
    assert rutina_cargada is not None, "La rutina cargada no debería ser None."
    assert len(rutina_cargada) == 2, "La rutina cargada debe tener exactamente 2 pasos."
    assert rutina_cargada[0]['x'] == 90, "El primer paso debe tener X=90."
    assert rutina_cargada[1]['g'] == "C", "El segundo paso debe tener la garra Cerrada ('C')."

def test_serial_initial_state():
    """
    Caso de Prueba: Verificar que al instanciar el Modelo, 
    la conexión serial esté apagada por defecto por seguridad.
    """
    modelo = Model()
    assert modelo.is_connected() is False, "El robot no debe estar conectado al inicio."
    assert modelo.serial_port is None, "El objeto de puerto serial debe ser None al inicio."