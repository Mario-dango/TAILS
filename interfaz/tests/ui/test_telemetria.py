"""
TEST UI TELEMETRÍA — LEDs de finales de carrera, badges de estado y límites.

Cubre tres defectos reportados sobre hardware real:
 1. Los LEDs virtuales de fin de carrera no se encendían durante el homing.
 2. Los badges WAIT y FINISH no avisaban el fin de un movimiento (quedaban fijos).
 3. El brazo no frenaba en los topes articulares (X=580, Y=130, Z=60).
"""
import pytest
from controller.main_controller import MainController
from controller.connection_manager import RETENCION_LED_MS
from view.ui_widgets import RANGO_X, RANGO_Y, RANGO_Z


@pytest.fixture
def app_conectada(qtbot):
    """Controlador completo con la conexión simulada y el envío interceptado."""
    controller = MainController()
    qtbot.addWidget(controller.view)
    controller.model.is_connected = lambda: True
    controller.connection_mgr.update_ui_connection_state(True)

    controller.enviados = []
    controller.connection_mgr.send_command = controller.enviados.append
    return controller


def _led_encendido(view, eje):
    return getattr(view, "led_%s" % eje).objectName() == "sensor_led_on"


# ─────────────────────── 1. LEDs de finales de carrera ───────────────────────
def test_el_led_del_final_se_enciende_al_tocarlo(app_conectada):
    vista = app_conectada.view
    app_conectada.connection_mgr.process_serial_data(
        "STATUS|X:0|Y:0|Z:0|S:000|C:0|M:0|E:0")
    assert not _led_encendido(vista, 'x')

    app_conectada.connection_mgr.process_serial_data(
        "STATUS|X:1|Y:0|Z:0|S:100|C:0|M:1|E:0")
    assert _led_encendido(vista, 'x')


def test_el_led_queda_retenido_aunque_el_sensor_se_libere(app_conectada, qtbot):
    """Un final se pisa unos milisegundos y la trama siguiente ya lo da libre.

    Sin retención el LED se prendía y apagaba entre dos refrescos y en pantalla
    no se veía nada: ese era el síntoma reportado durante el homing.
    """
    vista = app_conectada.view
    cm = app_conectada.connection_mgr

    cm.process_serial_data("STATUS|X:1|Y:0|Z:0|S:100|C:0|M:1|E:0")
    cm.process_serial_data("STATUS|X:6|Y:0|Z:0|S:000|C:0|M:1|E:0")
    assert _led_encendido(vista, 'x'), "El retén debe sostener el LED encendido."

    # Pasado el retén, y con el sensor ya libre, se apaga solo.
    qtbot.wait(RETENCION_LED_MS + 250)
    assert not _led_encendido(vista, 'x')


def test_los_tres_finales_se_encienden_durante_el_homing(app_conectada):
    """Se encienden a medida que cada eje llega, no recién al terminar."""
    vista = app_conectada.view
    cm = app_conectada.connection_mgr

    cm.process_serial_data("STATUS|Homing...|M:1")        # trama sin campos
    cm.process_serial_data("STATUS|X:400|Y:3|Z:40|S:010|C:0|M:1|E:0")
    assert _led_encendido(vista, 'y') and not _led_encendido(vista, 'z')

    cm.process_serial_data("STATUS|X:400|Y:0|Z:2|S:001|C:0|M:1|E:0")
    cm.process_serial_data("STATUS|X:5|Y:0|Z:0|S:100|C:0|M:1|E:0")
    assert all(_led_encendido(vista, e) for e in "xyz")


def test_la_trama_de_homing_sin_campos_no_rompe_el_parser(app_conectada):
    """'STATUS|Homing...|M:1' no trae X/Y/Z: antes reventaba y se tragaba callado."""
    cm = app_conectada.connection_mgr
    cm.process_serial_data("STATUS|Homing...|M:1")        # no debe lanzar
    # Y una trama posterior bien formada se sigue procesando con normalidad.
    cm.process_serial_data("STATUS|X:7|Y:0|Z:0|S:000|C:0|M:0|E:0")
    assert app_conectada.current_pos['x'] == 7


# ──────────────────────── 2. Destello de WAIT / FINISH ───────────────────────
def test_wait_y_finish_destellan_con_el_movimiento(app_conectada):
    cm = app_conectada.connection_mgr
    app_conectada.was_moving = False

    cm.process_serial_data("STATUS|X:0|Y:0|Z:0|S:000|C:1|M:1|E:0")
    assert app_conectada.wait_timer.isActive(), "WAIT late mientras el brazo se mueve."

    cm.process_serial_data("STATUS|X:9|Y:0|Z:0|S:000|C:1|M:0|E:0")
    assert not app_conectada.wait_timer.isActive()
    assert app_conectada.blink_timer.isActive(), (
        "FINISH destella al terminar CUALQUIER movimiento, no sólo una rutina.")


def test_el_paro_de_emergencia_corta_el_destello_de_wait(app_conectada):
    """Si el paro entra en pleno movimiento, el timer se comía el texto E-STOP."""
    cm = app_conectada.connection_mgr
    app_conectada.was_moving = False
    cm.process_serial_data("STATUS|X:0|Y:0|Z:0|S:000|C:1|M:1|E:0")
    assert app_conectada.wait_timer.isActive()

    cm.process_serial_data("STATUS|X:0|Y:0|Z:0|S:000|C:1|M:1|E:1")
    assert not app_conectada.wait_timer.isActive()
    assert app_conectada.view.lbl_status_wait.text() == "E-STOP"


# ─────────────────────────── 3. Límites articulares ──────────────────────────
@pytest.mark.parametrize("eje, tope", [('x', RANGO_X), ('y', RANGO_Y), ('z', RANGO_Z)])
def test_el_jog_no_pasa_del_tope_articular(app_conectada, eje, tope):
    """El fin de carrera sólo cuida el lado de HOME; el tope lejano es cosa nuestra."""
    app_conectada.view.tab_teach.radio_50deg.setChecked(True)   # 50 pasos
    app_conectada.current_pos = {'x': 0, 'y': 0, 'z': 0}
    app_conectada.current_pos[eje] = tope - 10

    app_conectada.movement_mgr.handle_jog(eje, +1)
    assert app_conectada.current_pos[eje] == tope
    assert app_conectada.enviados[-1] == ":#%s%d" % (eje.upper(), tope)

    # Ya en el tope no se reenvía el mismo destino: no mueve y ensucia la consola.
    antes = len(app_conectada.enviados)
    app_conectada.movement_mgr.handle_jog(eje, +1)
    assert len(app_conectada.enviados) == antes


def test_el_jog_no_pasa_de_cero(app_conectada):
    app_conectada.view.tab_teach.radio_50deg.setChecked(True)
    app_conectada.current_pos = {'x': 20, 'y': 0, 'z': 0}
    app_conectada.movement_mgr.handle_jog('x', -1)
    assert app_conectada.current_pos['x'] == 0


def test_la_ejecucion_recorta_un_json_fuera_de_rango(app_conectada):
    """Una rutina editada a mano no puede mandar al brazo más allá del recorrido."""
    em = app_conectada.execution_mgr
    em.loaded_routine = [{"type": "MOV", "x": 5000, "y": 40, "z": 10, "v": 50}]
    em.is_executing = True
    em.execution_index = 0
    app_conectada.view.tab_run.set_sequence(em.loaded_routine)

    app_conectada.enviados.clear()
    em.execute_next_step()

    assert app_conectada.enviados[-1] == ":#X%dY40Z10V050" % RANGO_X
    # El log tiene que mostrar lo que REALMENTE se ejecutó, no lo que pedía el JSON.
    assert "X%d" % RANGO_X in app_conectada.view.txt_run_log.toPlainText()


# ──────────────────── 4. Nombre del paso en el log (ítem 6) ──────────────────
def test_el_log_de_ejecucion_nombra_el_paso(app_conectada):
    em = app_conectada.execution_mgr
    paso = {"type": "MOV", "x": 120, "y": 40, "z": 10, "g": "C", "v": 60,
            "n": "Tomar pieza"}
    texto = em.describir_paso(2, paso)
    assert "Paso 3" in texto and "Tomar pieza" in texto and "X120" in texto

    sin_nombre = em.describir_paso(2, {k: v for k, v in paso.items() if k != "n"})
    assert "Paso 3" in sin_nombre and "Tomar pieza" not in sin_nombre
