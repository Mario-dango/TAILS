"""
CONFTEST - Configuración global para Pytest
"""
import pytest
from PyQt5.QtWidgets import QApplication
import sys

# Fixture global que asegura que exista una instancia de QApplication
# antes de correr cualquier prueba que involucre la UI.
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Aquí podríamos poner código de limpieza (teardown) si fuera necesario