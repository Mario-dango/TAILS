# 🎨 Módulo Vista - Proyecto T.A.I.L.S.

Este directorio contiene la **Interfaz Gráfica de Usuario (GUI)** del sistema T.A.I.L.S., construida con **PyQt5**.

Siguiendo el patrón **MVC**, esta capa es "tonta": no contiene lógica de negocio, no controla el robot y no toma decisiones. Su única responsabilidad es dibujar los botones, paneles y gráficos en la pantalla, y exponer estos elementos para que el **Controlador** pueda conectarles funciones.

Desde la **v2 ("Instrument Dark")** la interfaz se reparte en **10 archivos**: la barra superior, el banner de alarma y los widgets auxiliares se separaron del panel izquierdo para que el estado del robot se lea sin buscarlo.

> 📐 **Unidades:** la interfaz trabaja **siempre en pasos**, igual que el firmware
> (`:#X<n>` y la telemetría `STATUS|X:<pasos>`). No hay conversión a grados en ningún
> punto. La única excepción es la garra, que sí se configura en grados de servo
> (`:-A<grados>` / `:-P<grados>`).

---

## 🖼️ 1. `view.py` (La Fachada Principal)
**Clase: `View(QMainWindow)`**
Es la ventana principal y el contenedor de todo. Actúa como una **Fachada** (Facade Pattern) que simplifica el acceso a los componentes internos.
* **Estructura:** app bar → banner de alarma → cuerpo (rail izquierdo | pestañas) → dock de consola.
* `setup_ui_structure()`: Instancia los sub-paneles y los organiza en el layout principal.
* `expose_widgets_to_controller()`: **Método Crítico**. Crea referencias directas ("atajos") en la clase `View` hacia los botones que están escondidos dentro de las pestañas. Esto permite que el Controlador acceda a `self.view.btn_play` sin saber que ese botón vive realmente en `self.view.tab_run.btn_play`.
* `assign_all_icons()`: Centraliza la carga de recursos gráficos. Los iconos se asignan **con un tamaño por contexto (18–38px)**, no con el 64px global de la v1 que inflaba toda la interfaz.
* `set_btn_icon(item, nombre, size, fallback=None)`: Registra el icono para el Modo Kawaii. El `fallback` permite dejar cableado un icono que todavía no se dibujó (hoy: `kawaii.png` cae a `showHide.png`).
* `toggle_kawaii_mode(state)`: Activa o desactiva la visualización de iconos. Se puede disparar desde el menú Ayuda o desde el botón del app bar; ambos controles se espejan entre sí.
* `setup_shortcuts()`: Atajos de teclado para jogging.
* **Rutas ancladas al módulo:** `ICON_DIR` y `STYLE_PATH` se calculan a partir de `__file__`, así la app levanta igual lanzada desde `interfaz/` o desde la raíz del repositorio.

---

## 🔝 2. `top_bar.py` (Barra Superior) — *nuevo en v2*
**Clase: `TopBar(QFrame)`**
App bar de 54px. La conexión serial dejó de vivir escondida en el panel izquierdo.
* **Marca:** logo y subtítulo del proyecto.
* **Conexión:** combo de puertos COM, refrescar y conectar.
* **Badge de enlace:** `EN LÍNEA` / `SIN ENLACE`, vía `set_link(bool)`.
* **Telemetría condensada:** X/Y/Z siempre visibles, vía `set_position(x, y, z)`.
* **Accesos:** toggle de Modo Kawaii y botón de manual.

---

## 🚨 3. `alarm_banner.py` (Banner de Alarma) — *nuevo en v2*
**Clase: `AlarmBanner(QFrame)`**
Franja roja bajo el app bar para condiciones de bloqueo (parada de emergencia). Antes esa información era una línea más de la consola.
* `show_alarm(titulo, cuerpo)` / `hide_alarm()`.
* Incluye su propio botón **Rearmar (:-R)**, conectado al mismo slot que el del panel izquierdo.

---

## 🧩 4. `ui_widgets.py` (Widgets Auxiliares) — *nuevo en v2*
Piezas visuales reutilizables, dibujadas con `QPainter`. Ninguna depende del controlador.
* `SectionCard`: tarjeta con encabezado en versalitas (reemplaza al `QGroupBox` de título flotante, que comía ~20px por grupo).
* `ArmPreview`: vista superior polar del brazo, en pasos. El semidisco se **centra** en el alto disponible y el visor tiene tope (`ALTO_MAXIMO`): su radio lo limita el ancho fijo del rail, así que sin tope el dibujo quedaba chico dentro de un marco enorme al cerrar la terminal.
* `ZGauge`: barra vertical con la altura del eje Z, en pasos. Comparte mínimo y tope con `ArmPreview` para que los dos visores queden parejos.

> Los rótulos de los dos visores se dibujan a mano: la banda de cada uno sale de la
> **métrica de la fuente** (no de un alto fijo) y la fuente se achica sola si el texto no
> entra. Con los rectángulos fijos de antes, las coordenadas se recortaban en cuanto la
> pantalla tenía escala mayor al 100 %.
* `GripRange`: recorrido de la garra entre el ángulo cerrado y el abierto (**en grados**, que es como trabaja el servo).
* `Kbd`: etiqueta tipo tecla para los atajos de jogging.

> Las constantes `RANGO_X / RANGO_Y / RANGO_Z` de este módulo son el **recorrido real de
> cada eje, en pasos**, y la única fuente de verdad del proyecto: dan la escala de los
> indicadores visuales y **acotan el movimiento** (jogging, validación de la tabla y
> coordenadas enviadas al ejecutar una rutina). Deben coincidir con `MAX_POS_X / _Y / _Z`
> de `Core/Inc/robot_defines.h`, que es la barrera equivalente en el firmware.

---

## 🔌 5. `left_panel.py` (Panel de Estado)
**Clase: `LeftPanel(QWidget)`**
Barra lateral izquierda con el estado crítico del hardware en tiempo real.
* **Posición:** `AxisReadout` por eje — número monoespaciado grande con barra de color, en pasos. Expone `.display(v)`, así que es un reemplazo directo del `QLCDNumber` de la v1 (que se veía vacío e ilegible).
* **Vista del brazo:** `ArmPreview` + `ZGauge`, refrescados con `update_preview(x, y, z)`.
* **Finales de carrera y Sistema:** comparten una fila para eliminar el hueco vertical muerto. Los LEDs se colorean vía `objectName` (`sensor_led_on/off`) y los badges vía la property `class`.
* **STOP Emergencia:** anclado abajo, siempre visible. Debajo, el botón **Rearmar**.
* **Reparto del alto:** las tarjetas viven en un `QScrollArea` y el STOP queda afuera. `_repartir_alto_libre()` le da al botón el alto que sobra **después** de las tarjetas (hasta `ESTOP_ALTO_MAXIMO`): al cerrar la terminal el rail gana ~200px y, como los visores tienen tope, ese espacio iba a parar a un bloque de fondo vacío. Se calcula a mano en vez de con un stretch porque el orden de prioridad importa: primero las tarjetas, el resto para el STOP.

---

## 💻 6. `console_panel.py` (Terminal Inferior)
**Clase: `ConsolePanel(QWidget)`**
Dock con cabecera propia: toggle, contador de líneas y estado del puerto.
* `txt_console`: historial de comunicación. Ya no es verde `#0f0` sobre negro: el texto es gris claro legible y **el color queda para la severidad** del mensaje.
* `append_line(tag, mensaje)`: formatea con timestamp y etiqueta coloreada. `TAG_COLORS` cubre `INFO / TX / RX / OK / WARN / ERR / ERROR / ALERTA`.
* `clear_console()`: limpia el texto **y** resetea el contador de la cabecera.
* `set_port(texto)`: muestra el puerto abierto y su configuración.
* `input_console`: línea de entrada para comandos manuales (ej: `:#X100`).

---

## 🎯 7. `tab_calibration.py` (Pestaña Calibración)
**Clase: `CalibrationTab(QWidget)`**
Controles para la puesta a punto y referenciado del robot.
* **Inicialización:** `HOME ALL` (búsqueda física de ceros) y `Set Zero Here` (offset lógico).
* **Garra:** campos para definir los ángulos de apertura y cierre del servo, con un `GripRange` que muestra el recorrido resultante.
* **Enable:** checkbox para habilitar/deshabilitar la etapa de potencia.

---

## 🕹️ 8. `tab_teaching.py` (Pestaña Aprendizaje)
**Clase: `TeachingTab(QWidget)`**
Interfaz dividida para el control manual y la grabación de puntos.
* **Columna Izquierda (Jogging):**
  * Cruz X/Y y columna Z en bloques separados por un divisor real, con el atajo de teclado impreso en cada botón.
  * Slider de velocidad (10-100%) y selector de incremento.
* **Columna Derecha (Rutina):**
  * `QTableWidget` de **8 columnas: `["#", "NOMBRE", "X", "Y", "Z", "GARRA", "VEL %", "ESPERA s"]`**, con filas alternadas y ancho fijo para las columnas de índice y espera.
  * **ESPERA s** es la pausa (en segundos, 0–60) que el robot mantiene al terminar ese paso, antes de que la interfaz mande el siguiente. Se edita con un `QDoubleSpinBox` y viaja al JSON en la clave `"t"`.
  * ⚠️ Los índices de esas columnas están nombrados en `controller/learning_manager.py` (`COL_NUM`, `COL_X`, …). Si se cambia el orden acá, hay que actualizarlos allá — `tests/ui/test_view_facade.py` verifica que coincidan.
  * Botones CRUD: Capturar punto, Borrar seleccionado, Limpiar todo y Guardar JSON.

---

## ▶️ 9. `tab_execution.py` (Pestaña Ejecución)
**Clase: `ExecutionTab(QWidget)`**
Interfaz de reproducción automática de rutinas.
* **Carga de Archivos:** abrir el explorador y cargar/previsualizar rutinas JSON.
* **Progreso:** `QProgressBar` + `lbl_progress_pct` y `lbl_step` ("paso 3 de 12").
* **Secuencia:** `set_sequence(puntos)` lista los pasos y `highlight_step(i)` resalta el que se está ejecutando.
* **Controles:** botones grandes de PLAY, PAUSA y DETENER.
* **Log de Ejecución:** detalle paso a paso de la rutina activa (distinto de la consola técnica inferior).

---

## 🧪 10. `diagnostics_panel.py` (Panel de Test / Diagnóstico)
**Clase: `DiagnosticsPanel(QDialog)`**
Ventana emergente accesible desde el menú **Herramientas**. Permite prender/apagar cada LED y mover cada motor de forma independiente y relativa (comandos `:*`), más abrir/cerrar la garra y togglear el torque. Incluye una guía rápida; los resultados se ven en la consola inferior. Es autocontenida: recibe la función `send_cmd` y cablea sus propios botones.

> Se llamaba `test_panel.py` / `TestPanel`. Se renombró porque `pytest` importaba el archivo como si fuera un módulo de pruebas y emitía un `PytestCollectionWarning` en cada corrida.

---

## ⌨️ Atajos de teclado

| Tecla | Acción |
| :--- | :--- |
| `←` `→` | Eje X |
| `↑` `↓` | Eje Y |
| `W` `S` | Eje Z |
| `Esc` | Parada de emergencia |

Se disparan como clicks en los botones correspondientes, así que no requieren nada del controlador.

---

## 🔤 Tipografías

El tema pide **IBM Plex Sans** e **IBM Plex Mono** (gratuitas, licencia OFL). Si no están instaladas, Qt cae a Segoe UI / Consolas y todo sigue funcionando: solo cambia el tipo.
