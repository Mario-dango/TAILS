"""
TEST MODEL - Pruebas unitarias para la capa de datos y hardware
"""
import pytest
import os
from model.model import Model

def test_save_and_load_routine(tmp_path):
    """
    Verifica que el Modelo pueda guardar una rutina en JSON en el disco duro 
    y que al leerla de vuelta, los datos se mantengan intactos.
    """
    # 1. PREPARACIÓN (Arrange): Instanciamos la clase que vamos a probar
    modelo = Model()
    
    # Creamos una lista de diccionarios que simula ser una rutina generada por la interfaz
    rutina_falsa = [
        {"type": "MOV", "x": 90, "y": 45, "z": 0, "g": "A"},
        {"type": "MOV", "x": 180, "y": 90, "z": 50, "g": "C"}
    ]
    
    # 'tmp_path' es una magia de pytest. Crea una carpeta temporal real en Windows
    # solo para esta prueba, y la borra automáticamente al terminar. Así no ensuciamos tu PC.
    archivo_prueba = tmp_path / "rutina_test.json"
    
    # 2. ACCIÓN (Act): Ejecutamos los métodos reales del modelo
    # Intentamos guardar la lista falsa en el archivo temporal
    resultado_guardado = modelo.save_routine_to_file(archivo_prueba, rutina_falsa)
    
    # Intentamos leer ese mismo archivo recién creado
    rutina_cargada = modelo.load_routine_from_file(archivo_prueba)
    
    # 3. VERIFICACIÓN (Assert): Comprobamos que el resultado sea el esperado
    # ¿El método devolvió True indicando que no hubo errores de escritura?
    assert resultado_guardado is True, "El método debería retornar True al guardar con éxito."
    
    # ¿El archivo físico realmente existe en la ruta de Windows?
    assert os.path.exists(archivo_prueba), "El archivo físico debe existir en el disco."
    
    # ¿El archivo cargado devolvió datos válidos?
    assert rutina_cargada is not None, "La rutina cargada no debería ser None."
    
    # ¿Recuperamos los 2 pasos exactamente?
    assert len(rutina_cargada) == 2, "La rutina cargada debe tener exactamente 2 pasos."
    
    # Verificamos valores puntuales para asegurar que la serialización JSON funcionó
    assert rutina_cargada[0]['x'] == 90, "El valor X del primer paso se corrompió."
    assert rutina_cargada[1]['g'] == "C", "El valor de la garra del segundo paso se corrompió."

def test_serial_initial_state():
    """
    Verifica que por seguridad, el robot arranque siempre desconectado.
    """
    # 1. Preparación
    modelo = Model()
    
    # 2. Verificación directa (No hay acción previa)
    # Comprobamos que la bandera booleana sea False
    assert modelo.is_connected() is False, "El robot no debe estar conectado al inicio."
    
    # Comprobamos que el objeto PySerial esté vacío (None) para no bloquear puertos
    assert modelo.serial_port is None, "El objeto de puerto serial debe ser None al inicio."