"""
TEST DEL RAIL IZQUIERDO — reparto del alto y proporción de los visores.

Motivo: al ocultar la terminal (que es un dock y devuelve ~200px de alto), el
panel izquierdo se estiraba. Los visores no pueden crecer indefinidamente —el
semidisco de la vista superior tiene el radio limitado por el ancho FIJO del
rail—, así que ese espacio terminaba como un bloque de fondo vacío dentro del
recuadro: la vista se veía deformada.

Estas pruebas fijan las dos mitades del arreglo: los visores tienen tope y el
alto que sobra se lo queda el botón de parada de emergencia.
"""
import pytest
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QResizeEvent

from view.left_panel import LeftPanel
from view.ui_widgets import ArmPreview, ZGauge


def _redimensionar(panel, alto):
    """Cambia el alto del rail y entrega el resizeEvent a mano.

    Qt no manda eventos de redimensionado a un widget que nunca se mostró, y
    estas pruebas no abren ventanas: el tamaño real dependería del monitor de
    quien las corra.
    """
    anterior = panel.size()
    panel.resize(336, alto)
    panel.resizeEvent(QResizeEvent(QSize(336, alto), anterior))


@pytest.fixture
def panel(qtbot):
    p = LeftPanel()
    qtbot.addWidget(p)
    return p


def test_los_visores_tienen_tope_y_lo_piden_como_alto_preferido(panel):
    """Sin tope, el marco crece y el dibujo queda flotando en el medio."""
    for visor in (panel.arm_preview, panel.z_gauge):
        assert visor.maximumHeight() == ArmPreview.ALTO_MAXIMO
        assert visor.minimumHeight() == ArmPreview.ALTO_MINIMO
        # El sizeHint es el MÁXIMO: si hay lugar, el visor lo usa; QWidget no
        # define sizeHint y el layout lo mediría por su mínimo.
        assert visor.sizeHint().height() == ArmPreview.ALTO_MAXIMO

    assert isinstance(panel.arm_preview, ArmPreview)
    assert isinstance(panel.z_gauge, ZGauge)


def test_el_stop_se_queda_con_el_alto_que_sobra(panel, qtbot):
    """Con la terminal cerrada sobra alto: se lo lleva la parada de emergencia.

    Se mira el alto FIJADO (setFixedHeight) y no height(): el widget del
    fixture nunca se muestra, así que el layout no llega a aplicar la geometría.
    """
    _redimensionar(panel, 900)
    assert panel.btn_estop.maximumHeight() == LeftPanel.ESTOP_ALTO_MAXIMO, (
        "Con espacio de sobra el STOP crece hasta su tope en vez de dejar un "
        "bloque de fondo vacío entre las tarjetas y el botón.")


def test_con_la_ventana_justa_el_stop_no_le_roba_alto_a_las_tarjetas(panel, qtbot):
    """Primero las tarjetas; el botón se queda sólo con lo que sobra.

    Con el STOP compitiendo por stretch, Qt le daba alto al botón mientras el
    rail mostraba barra de desplazamiento y tapaba las tarjetas de estado.
    """
    _redimensionar(panel, 560)
    assert panel.btn_estop.maximumHeight() == LeftPanel.ESTOP_ALTO_MINIMO

    tarjetas = panel.scroll.widget()
    assert panel.scroll.minimumHeight() >= tarjetas.minimumSizeHint().height(), (
        "El área de tarjetas reserva su mínimo: ahí es donde aparecía la barra "
        "de desplazamiento cuando el botón se quedaba con el alto.")
