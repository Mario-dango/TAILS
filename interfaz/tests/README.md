# 🧪 Módulo QA y Pruebas - Proyecto T.A.I.L.S.

Este directorio contiene toda la infraestructura de **Aseguramiento de Calidad (QA)** del proyecto T.A.I.L.S. 

Dado que probar interfaces gráficas dependientes de hardware físico suele ser un cuello de botella (*Hardware-in-the-Loop bottleneck*), este módulo implementa una estrategia de **Mocking** (simulación). Esto permite aislar la capa de software, garantizando que la lógica del patrón MVC y la UI funcionen perfectamente sin necesidad de tener el brazo robótico conectado por USB.

---

## 🛠️ Stack Tecnológico
La automatización está construida sobre los estándares de la industria para Python:
* **`pytest`**: Motor principal de ejecución de pruebas (Test Runner).
* **`pytest-qt`**: Extensión que permite inyectar eventos (clics de mouse, pulsaciones de teclado) directamente en el *Event Loop* de la memoria de PyQt5, simulando interacción humana real.
* **`unittest.mock` (MagicMock)**: Librería nativa para crear "objetos falsos", permitiendo anular llamadas a puertos COM físicos o fingir respuestas del microcontrolador.

---

## 🗂️ Estructura de Pruebas (Test Pyramid)

La suite de pruebas está dividida según su alcance y objetivo:

### 1. Pruebas Unitarias (`/unit`)
Pruebas ultrarrápidas de lógica pura (Backend). No levantan ventanas gráficas.
* **`test_model.py`**: Valida la capa de datos. Verifica que el motor de guardado y carga de rutinas en formato JSON serialice y deserialice la información sin corromperla.
* **`test_parsers.py`**: Valida la resiliencia del software. Asegura que el decodificador de telemetría extraiga bien las coordenadas de las tramas del STM32 (`STATUS|X:10...`) y, más importante, que el programa no sufra un *Crash* si el cable falla y recibe basura (`ASDF|X:??`).

### 2. Pruebas de Interfaz Automatizadas (`/ui`)
Pruebas visuales y de integración. Instancian la Ventana Principal y simulan a un usuario operando el software.
* **`test_learning_tab.py`**: Verifica que los botones de la pestaña "Aprendizaje" (como Guardar Punto o Limpiar Todo) interactúen correctamente con la tabla de memoria (`QTableWidget`).
* **`test_execution.py`**: Valida el metrónomo automático (`QTimer`). Asegura que al presionar Play, la interfaz pase a estado de ejecución, y que el botón Stop detenga los temporizadores de manera segura para evitar fugas de memoria.

### 3. Emulación de Hardware (`/mocks`)
Herramientas para pruebas **Manuales y Exploratorias**.
* **`mock_stm32.py`**: Un script de Python diseñado para conectarse a un puerto COM virtual. Actúa como un "Espejo Falso" del robot: escucha los comandos G-Code de la interfaz y responde con tramas de telemetría falsas, permitiendo a los desarrolladores probar visualmente los LEDs y LCDs de T.A.I.L.S.

### 4. Documentación QA (`/manual`)
* **`test_plan.md`**: Define la matriz de cobertura y los Casos de Prueba (Smoke Tests) que deben ejecutarse manualmente con el hardware físico real antes de liberar una nueva versión (Release) del software al entorno de producción o taller.

---

## 🚀 Ejecución de Pruebas Automatizadas

Para correr toda la suite de regresión, abre una terminal en la raíz del proyecto (carpeta `interfaz`) y ejecuta:

```bash
python -m pytest