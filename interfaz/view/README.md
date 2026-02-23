# 🎨 Módulo Vista - Proyecto T.A.I.L.S.

Este directorio contiene la **Interfaz Gráfica de Usuario (GUI)** del sistema T.A.I.L.S., construida con **PyQt5**.

Siguiendo el patrón **MVC**, esta capa es "tonta": no contiene lógica de negocio, no controla el robot y no toma decisiones. Su única responsabilidad es dibujar los botones, paneles y gráficos en la pantalla, y exponer estos elementos para que el **Controlador** pueda conectarles funciones.

La interfaz se ha modularizado en **6 archivos** para facilitar el mantenimiento y la edición de diseño:

---

## 🖼️ 1. `view.py` (La Fachada Principal)
**Clase: `View(QMainWindow)`**
Es la ventana principal y el contenedor de todo. Actúa como una **Fachada** (Facade Pattern) que simplifica el acceso a los componentes internos.
* `setup_ui_structure()`: Importa e instancia los 5 sub-paneles y los organiza en el Layout principal (Vertical).
* `expose_widgets_to_controller()`: **Método Crítico**. Crea referencias directas ("atajos") en la clase `View` hacia los botones que están escondidos dentro de las pestañas. Esto permite que el Controlador acceda a `self.view.btn_play` sin saber que ese botón vive realmente en `self.view.tabs.tab_run.btn_play`.
* `assign_all_icons()`: Centraliza la carga de recursos gráficos. Asigna los iconos a todos los botones de todos los sub-paneles.
* `toggle_kawaii_mode(state)`: Activa o desactiva la visualización de iconos, dejando la interfaz en modo solo texto o modo gráfico.

---

## 🔌 2. `left_panel.py` (Panel de Estado)
**Clase: `LeftPanel(QGroupBox)`**
Barra lateral izquierda que muestra el estado crítico del hardware en tiempo real.
* **Sección Conexión:** Combobox de puertos COM y botones de Refrescar/Conectar.
* **Sección Telemetría:** Displays LCD (`QLCDNumber`) para las coordenadas X, Y, Z.
* **Sección Sensores:** Etiquetas circulares (`QLabel`) que simulan LEDs. Se colorean vía CSS (`#sensor_led_on/off`) cuando se activan los finales de carrera.
* **Sección Sistema:** Indicadores de estado global (HOME, WAIT, FINISH) controlados por propiedades dinámicas.
* **STOP Emergencia:** Botón prioritario de parada.

---

## 💻 3. `console_panel.py` (Terminal Inferior)
**Clase: `ConsolePanel(QWidget)`**
Simula una terminal de comandos estilo hacker (texto verde sobre fondo negro).
* `txt_console`: Área de texto de solo lectura donde se imprime el historial de comunicación (TX/RX).
* `input_console`: Línea de entrada para enviar comandos G-Code/Custom manuales al robot (ej: `:#X100`).

---

## 🎯 4. `tab_calibration.py` (Pestaña Calibración)
**Clase: `CalibrationTab(QWidget)`**
Controles para la puesta a punto y referenciado del robot.
* **Grupo Inicialización:** Botones para `HOME ALL` (búsqueda física de ceros) y `Set Zero Here` (offset lógico).
* **Grupo Garra:** Campos de texto (`QLineEdit`) para definir los ángulos PWM de apertura y cierre del servo de la herramienta.
* **Enable:** Checkbox para habilitar/deshabilitar la etapa de potencia de los motores.

---

## 🕹️ 5. `tab_teaching.py` (Pestaña Aprendizaje)
**Clase: `TeachingTab(QWidget)`**
Interfaz dividida para el control manual y la grabación de puntos.
* **Columna Izquierda (Jogging):** * Grilla de botones direccionales (X±, Y±, Z±) y botones de centrado rápido (Hxy, Hz).
  * Slider de velocidad (10-100%).
  * Selector de pasos (Grados de incremento).
* **Columna Derecha (Lista):**
  * `QTableWidget`: Tabla que lista los pasos de la rutina actual (X, Y, Z, Garra).
  * Botones CRUD: Agregar punto actual, Borrar seleccionado, Limpiar todo y Guardar JSON.

---

## ▶️ 6. `tab_execution.py` (Pestaña Ejecución)
**Clase: `ExecutionTab(QWidget)`**
Interfaz de reproducción automática de rutinas (CNC).
* **Carga de Archivos:** Botones para abrir el explorador de archivos y cargar/previsualizar rutinas JSON.
* **Progreso:** Barra de carga (`QProgressBar`) vinculada al avance de la rutina.
* **Controles:** Botones grandes de PLAY, PAUSA y DETENER.
* **Log de Ejecución:** Cuadro de texto grande que detalla el paso a paso de la rutina activa (diferente a la consola técnica inferior).