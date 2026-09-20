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

# La vista recuerda el tamaño de la ventana y la posición del dock de terminal
# en QSettings. Sin aislar eso, las pruebas pisarían la configuración real del
# operador y —peor— arrastrarían estado entre corridas: un test que deja la
# terminal escondida hacía fallar al siguiente.
@pytest.fixture(autouse=True, scope="session")
def _ajustes_aislados():
    from PyQt5.QtCore import QSettings
    from view.view import View

    original = View.SETTINGS_APP
    View.SETTINGS_APP = "interfaz-tests"
    QSettings(View.SETTINGS_ORG, View.SETTINGS_APP).clear()
    yield
    QSettings(View.SETTINGS_ORG, View.SETTINGS_APP).clear()
    View.SETTINGS_APP = original
