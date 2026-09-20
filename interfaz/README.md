# 🤖 T.A.I.L.S. - Technical Articulated Intelligent Linkage System

T.A.I.L.S. es un entorno de software y hardware diseñado para el control, calibración y automatización de un brazo robótico articulado mediante comunicación serial (USB CDC) con un microcontrolador **STM32F103C8T6 (BluePill)**.

Este proyecto implementa una Interfaz Gráfica de Usuario (GUI) robusta desarrollada en **Python y PyQt5**, estructurada bajo el patrón de arquitectura de software **MVC (Modelo-Vista-Controlador)**.

## 🗂️ Estructura del Proyecto

El código está estrictamente modularizado para garantizar escalabilidad y fácil mantenimiento:

* 🧠 **/controller**: Contiene la lógica de negocio, temporizadores y la comunicación entre la vista y el modelo. Fraccionado en Managers especializados.
* 🎨 **/view**: Contiene la interfaz gráfica (GUI) fraccionada por paneles y pestañas. Es una capa puramente visual.
* ⚙️ **/model**: Gestiona la conexión de bajo nivel con el hardware (Puertos COM) y el sistema de archivos (JSON).
* 📁 **/rutinas**: Directorio de almacenamiento por defecto para las rutinas de aprendizaje (`.json`).
* 🖼️ **/images**: Contiene los assets visuales (iconos, capturas) para el "Modo Kawaii" y la UI en general.
* 🧪 **/tests**: Suite de pruebas automatizadas (`pytest` + `pytest-qt`), mocks de hardware y plan de pruebas manuales.
* 📄 **`main.py`**: Punto de entrada (Entry Point) de la aplicación.
* 💅 **`style.css`**: Hoja de estilos global (tema oscuro "Instrument Dark").
* 📦 **`requirements.txt`**: Dependencias del proyecto.

## 🚀 Instalación y Ejecución

```bash
pip install -r requirements.txt
```

```bash
python main.py
```

Las rutas de iconos y estilos están ancladas al propio módulo, así que la aplicación también levanta correctamente si se la lanza desde la raíz del repositorio (`python interfaz/main.py`).

**Tipografías (opcional):** el tema usa *IBM Plex Sans* e *IBM Plex Mono*. Si no están instaladas, Qt cae a Segoe UI / Consolas sin ningún otro efecto.

## ⌨️ Atajos de teclado

| Tecla | Acción |
| :--- | :--- |
| `←` `→` | Jogging del eje X |
| `↑` `↓` | Jogging del eje Y |
| `W` `S` | Jogging del eje Z |
| `Esc` | Parada de emergencia |

## 📐 Unidades

La interfaz trabaja **siempre en pasos**, igual que el firmware (`:#X<n>` es una posición absoluta en pasos, y la telemetría llega como `STATUS|X:<pasos>`). No se convierte a grados en ningún punto. La única excepción es la garra, que se configura en grados de servo (`:-A<grados>` / `:-P<grados>`).

Las constantes `RANGO_X / RANGO_Y / RANGO_Z` de [`view/ui_widgets.py`](view/ui_widgets.py) son el **recorrido real de cada eje en pasos** y la única fuente de verdad del proyecto. Definen la escala de los indicadores visuales (vista superior y gauge de Z) y **además limitan el movimiento**: acotan el jogging, la validación de la tabla de rutina y las coordenadas que se envían al ejecutar un JSON.

Son la primera de dos barreras. La segunda vive en el firmware (`MAX_POS_X / _Y / _Z` en `Core/Inc/robot_defines.h`), que recorta el destino y frena el motor por hardware aunque el comando llegue escrito a mano por la terminal. **Los dos juegos de valores tienen que coincidir**: si se cambia el recorrido de un eje, hay que tocar ambos y reflashear la placa.

## ⏱️ Ritmo de ejecución

La interfaz manda un paso cada **1500 ms** (`INTERVALO_BASE_MS` en [`controller/execution_manager.py`](controller/execution_manager.py)): es el tiempo que le da al brazo para completar el movimiento antes de mandar el siguiente.

A ese piso se le **suma la espera propia de cada paso** — la columna `ESPERA s` de la pestaña Aprendizaje, que se guarda en la clave `"t"` del JSON. Sirve para dejar asentar una pieza, darle tiempo a la garra a terminar de cerrar o parar la secuencia mientras el operador acomoda algo. El metrónomo es un `QTimer` de un solo disparo que se reprograma después de cada paso, así que cada pausa puede valer distinto.

## 🧪 Pruebas

```bash
python -m pytest
```

Ver [`tests/README.md`](tests/README.md) para el detalle de la estrategia de QA y [`tests/manual/test_plan.md`](tests/manual/test_plan.md) para los casos de prueba con hardware real.
