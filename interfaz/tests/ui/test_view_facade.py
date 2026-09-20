"""
TEST DE FACHADA — Contrato entre la Vista y el Controlador.

Motivo: al instalar el rediseño v2 ("Instrument Dark"), el view.py del bundle venía
escrito contra una versión anterior del proyecto y no construía el menú Herramientas
ni la ayuda de comandos. Como el controlador conecta esas acciones en su __init__,
la aplicación moría con AttributeError antes de mostrar la ventana.

Estas pruebas fijan ese contrato: si un rediseño futuro vuelve a dejar afuera un
widget que el controlador espera, falla acá y no en el arranque del usuario.
"""
import pytest
from view.view import View


# Widgets que expose_widgets_to_controller() debe publicar sí o sí, porque
# controller/*.py los usa por nombre.
WIDGETS_REQUERIDOS = [
    # Menús
    "action_manual", "action_about", "action_kawaii",
    "action_test_panel", "action_cmd_list", "action_cmd_example",
    # Conexión (viven en el app bar desde la v2)
    "btn_refresh", "combo_ports", "btn_connect",
    # Panel izquierdo
    "lcd_x", "lcd_y", "lcd_z", "led_x", "led_y", "led_z",
    "lbl_status_home", "lbl_status_wait", "lbl_status_finish",
    "btn_estop", "btn_rearm",
    # Consola
    "txt_console", "input_console", "btn_send_console", "btn_clear_console",
    # Calibración
    "btn_home", "btn_setzero", "input_angle_open", "btn_set_open",
    "input_angle_close", "btn_set_close", "chk_enable",
    # Aprendizaje
    "btn_x_plus", "btn_x_minus", "btn_y_plus", "btn_y_minus",
    "btn_z_plus", "btn_z_minus", "btn_home_xy", "btn_home_z",
    "slider_speed", "lbl_speed_val", "step_group",
    "btn_open_grip", "btn_close_grip", "table_points",
    "btn_add_point", "btn_del_point", "btn_clear_all", "btn_save_file",
    "btn_move_up", "btn_move_down",
    # Ejecución
    "lbl_file", "btn_load_file", "btn_preview", "progress_bar",
    "btn_play", "btn_pause", "btn_stop_run", "btn_repeat", "txt_run_log",
    # Piezas nuevas de la v2 que el controlador ya usa
    "top_bar", "alarm", "panel_left", "console_container", "tab_run", "tab_teach",
    "console_dock",
]


@pytest.fixture
def view(qtbot):
    v = View()
    qtbot.addWidget(v)
    return v


@pytest.mark.parametrize("nombre", WIDGETS_REQUERIDOS)
def test_la_vista_expone_el_widget(view, nombre):
    assert hasattr(view, nombre), (
        f"View no expone '{nombre}'. El paquete /controller lo usa por nombre: "
        f"si se renombró o se perdió en un rediseño, hay que reponerlo en "
        f"expose_widgets_to_controller() o en setup_menu_bar()."
    )


def test_la_tabla_de_puntos_tiene_las_columnas_esperadas(view):
    """Los índices COL_* de learning_manager dependen de este orden exacto."""
    from controller.learning_manager import (COL_NUM, COL_NAME, COL_X, COL_Y,
                                             COL_Z, COL_G, COL_V, COL_T)

    tabla = view.table_points
    assert tabla.columnCount() == 8
    encabezados = [tabla.horizontalHeaderItem(i).text()
                   for i in range(tabla.columnCount())]
    assert encabezados == ["#", "NOMBRE", "X", "Y", "Z", "GARRA", "VEL %",
                           "ESPERA s"]
    assert (COL_NUM, COL_NAME, COL_X, COL_Y, COL_Z,
            COL_G, COL_V, COL_T) == (0, 1, 2, 3, 4, 5, 6, 7)


def test_los_rangos_de_celda_salen_del_recorrido_real(view):
    """La validación de la tabla y el visualizador comparten los mismos rangos."""
    from view.tab_teaching import RANGOS_CELDA, COL_X, COL_Y, COL_Z, COL_V
    from view.ui_widgets import RANGO_X, RANGO_Y, RANGO_Z

    assert RANGOS_CELDA[COL_X][1:] == (0, RANGO_X)
    assert RANGOS_CELDA[COL_Y][1:] == (0, RANGO_Y)
    assert RANGOS_CELDA[COL_Z][1:] == (0, RANGO_Z)
    assert RANGOS_CELDA[COL_V][1:] == (10, 100)


def test_la_espera_por_paso_se_edita_con_decimales(view):
    """La espera se carga en segundos: 0.5 s tiene que ser un valor posible."""
    from PyQt5.QtWidgets import QDoubleSpinBox
    from view.tab_teaching import COL_T, RANGOS_DECIMALES, ESPERA_MAXIMA_S

    assert RANGOS_DECIMALES[COL_T][1:] == (0.0, ESPERA_MAXIMA_S)

    tabla = view.table_points
    tabla.setRowCount(1)
    editor = tabla.itemDelegate().createEditor(
        tabla, None, tabla.model().index(0, COL_T))
    assert isinstance(editor, QDoubleSpinBox), (
        "La espera necesita decimales: con un QSpinBox entero no se puede "
        "cargar medio segundo.")
    assert editor.maximum() == ESPERA_MAXIMA_S


def test_los_dos_controles_de_kawaii_quedan_sincronizados(view):
    """El toggle vive en el menú Ayuda y en el app bar: no deben desfasarse."""
    inicial = view.action_kawaii.isChecked()

    view.top_bar.btn_kawaii.setChecked(not inicial)
    assert view.action_kawaii.isChecked() == (not inicial)

    view.action_kawaii.setChecked(inicial)
    assert view.top_bar.btn_kawaii.isChecked() == inicial


def test_la_terminal_se_muestra_y_oculta_desde_el_app_bar(view):
    """La terminal es un dock: el botón del app bar y el dock no deben desfasarse.

    Se mira isVisibleTo(): la ventana del fixture nunca se muestra, y en ese
    caso todos sus hijos reportan isVisible()==False e isHidden()==True estén
    ocultos o no.
    """
    assert view.console_dock.isVisibleTo(view), "La terminal arranca a la vista."

    view.toggle_console(False)
    assert not view.console_dock.isVisibleTo(view)
    assert not view.top_bar.btn_console.isChecked()

    view.toggle_console(True)
    assert view.console_dock.isVisibleTo(view)
    assert view.top_bar.btn_console.isChecked()


def test_los_botones_de_jogging_apilan_icono_y_etiqueta(view):
    """QPushButton sólo dibuja el icono AL LADO del texto: por eso son QToolButton.

    Si un rediseño los vuelve a convertir en QPushButton, el icono y el rótulo
    se pelean el ancho del botón y los dos salen recortados.
    """
    from PyQt5.QtWidgets import QToolButton
    from PyQt5.QtCore import Qt

    for nombre in ("btn_x_plus", "btn_x_minus", "btn_y_plus", "btn_y_minus",
                   "btn_z_plus", "btn_z_minus", "btn_home_xy", "btn_home_z"):
        btn = getattr(view, nombre)
        assert isinstance(btn, QToolButton), f"{nombre} debe ser QToolButton."
        assert btn.toolButtonStyle() == Qt.ToolButtonTextUnderIcon, (
            f"{nombre} debe dibujar la etiqueta DEBAJO del icono.")
