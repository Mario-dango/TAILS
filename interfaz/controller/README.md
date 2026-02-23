# 🧠 Módulo Controlador - Proyecto T.A.I.L.S.

Este directorio contiene el "Cerebro" de la interfaz gráfica del **Technical Articulated Intelligent Linkage System (T.A.I.L.S.)**. 

Siguiendo el patrón de arquitectura **MVC (Modelo-Vista-Controlador)**, el Controlador es el intermediario estricto: escucha las interacciones del usuario en la Vista (`view.py`) y utiliza el Modelo (`model.py`) para enviar comandos físicos al microcontrolador (STM32).

Para evitar un "God Object" (un archivo gigante y difícil de mantener), la lógica se ha fraccionado en 5 archivos especializados:

---

## 🏛️ 1. `main_controller.py` (El Orquestador)
**Clase: `MainController`**
Es el punto de entrada lógico. Su misión es inicializar el MVC, guardar la memoria compartida y coordinar a los demás sub-controladores (Managers).
* `__init__()`: Instancia la Vista, el Modelo y los 4 Managers. Crea los registros "sombra" (`current_pos`, `gripper_state`) que recuerdan la posición física del brazo robótico.
* `init_general_ui()`: Conecta acciones globales como el menú de Ayuda o el modo visual Kawaii.
* `handle_finish_blink()` / `handle_home_alert_blink()`: Manejan las animaciones visuales (parpadeo de LEDs) de la interfaz gráfica basadas en QTimers.

---

## 🔌 2. `connection_manager.py` (Gestor de Comunicaciones)
**Clases: `ConnectionManager` y `SerialWorker`**
Especialista en la comunicación USB bidireccional entre la PC y el STM32.
* **`SerialWorker (QThread)`**: Un hilo secundario vital. Escucha el puerto serial infinitamente sin congelar la ventana gráfica. Emite la señal `data_received` cuando llega una trama.
* `toggle_connection()`: Abre o cierra el puerto COM y lanza el hilo `SerialWorker`.
* `send_command(cmd)`: Aduana de salida. Verifica que haya hardware conectado antes de enviar tramas (ej: `:#X100`).
* `process_serial_data(data)`: **El Parser (Traductor)**. Despedaza las tramas entrantes (`STATUS|X:10|Y:20...`), extrae la telemetría y actualiza los indicadores visuales (LEDs de sensores, etiquetas HOME/WAIT).
* `update_ui_connection_state()`: Bloqueo de seguridad. Deshabilita botones en la interfaz si el cable USB se desconecta.

---

## ⚙️ 3. `movement_manager.py` (Gestor de Movimiento)
**Clase: `MovementManager`**
Traduce las interacciones humanas en la pestaña "Aprendizaje" a movimientos cinemáticos.
* `handle_jog(axis, direction)`: Lee las flechas de la interfaz, suma/resta los grados configurados y ordena el movimiento manual (Jogging).
* `handle_home()` / `handle_set_zero()`: Ejecutan los comandos de inicialización (`:-H` y `:-Z`).
* `handle_gripper(action)`: Cambia el estado dinámico de la pinza (Abierta/Cerrada).
* `emergency_stop()`: Botón del pánico (`:-S`).
* `update_lcds()`: Refresca las pantallas numéricas de la UI consultando la memoria global del `MainController`.

---

## 📝 4. `learning_manager.py` (Gestor de Aprendizaje)
**Clase: `LearningManager`**
Maneja la captura de datos y la creación de secuencias lógicas (Rutinas).
* `add_point_to_table()`: Captura las coordenadas exactas de la memoria global al momento del clic y las inyecta en el `QTableWidget`.
* `delete_point_from_table()` / `clear_all_table()`: Manipulación de la interfaz de la tabla para corregir errores.
* `save_routine_json()`: Extrae todas las filas de la tabla visual, las empaqueta en una lista de diccionarios y usa el Modelo para generar un archivo físico `.json`.

---

## 🚀 5. `execution_manager.py` (Gestor de Ejecución)
**Clase: `ExecutionManager`**
Es el motor de automatización. Lee los archivos JSON y los reproduce paso a paso simulando un CNC.
* `load_routine_dialog()` / `preview_loaded_routine()`: Interfaz de carga de archivos de Windows y volcado de previsualización en la consola.
* `start_execution()` / `pause_execution()` / `stop_execution()`: Controlan el estado del ciclo automático.
* `execute_next_step()`: **El Metrónomo**. Función conectada a un `QTimer` que, a intervalos regulares (ej: 1500ms), extrae el siguiente bloque del archivo JSON cargado, arma el comando (ej: `:#X50Y10Z0|C`) y lo envía al robot, actualizando la barra de progreso.