# 📚 Documentación y Recursos Técnicos - T.A.I.L.S.

Este directorio centraliza la base de conocimientos, la literatura técnica y la investigación que respaldan el desarrollo del brazo robótico T.A.I.L.S.

Tener la documentación organizada es un pilar fundamental en este proyecto, ya que asegura su reproducibilidad, facilita el mantenimiento de la electrónica y el software, y sirve como material de estudio o consulta para futuras implementaciones.

---

## 🗂️ Contenido del Directorio

### 1. 📄 Hojas de Datos (Datasheets)
Recopilación de las especificaciones oficiales de los fabricantes para los componentes críticos del hardware. Es esencial para comprender los límites eléctricos, el mapeo de pines y el comportamiento térmico del circuito.
* **Procesamiento:** Microcontrolador STM32F103C8T6 (Bluepill) y manuales de referencia de la arquitectura ARM Cortex-M3.
* **Drivers y Potencia:** Especificaciones del controlador de motores paso a paso Pololu A4988 y los reguladores de tensión (LM7805, LM317).
* **Acondicionamiento Lógico:** Transistores BJT PNP BC558 y diodos de protección.
* **Actuadores:** Curvas de torque y consumo de los motores utilizados en los ejes X, Y, Z y el actuador final (Garra).

### 2. 📘 Documentación General del Proyecto
Guías operativas y arquitectura del ecosistema T.A.I.L.S.
* **Manual de Usuario de la GUI:** Explicación detallada de la interfaz gráfica, conexión de puertos COM, uso de la pestaña de aprendizaje, y ejecución de rutinas JSON.
* *(Espacio reservado para futuras guías de integración, cuadernillos de actividades, o diagramas de arquitectura de sistemas).*

### 3. 📑 Informe Técnico (Technical Report)
> 🚧 **Estado:** *En fase de redacción.*

El documento central que profundizará en la ingeniería dura detrás de T.A.I.L.S. En próximas actualizaciones, este informe abarcará:
* **Cinemática:** Análisis geométrico y matemático de los 3 Grados de Libertad (Directa e Inversa).
* **Diseño Electrónico:** Justificación de componentes, cálculos de disipación de potencia y análisis de señales.
* **Arquitectura de Software:** Diagramas de flujo del firmware (HAL C++) y del patrón MVC en Python.
* **Aseguramiento de Calidad (QA):** Matrices de prueba, resultados de la automatización de la UI y rendimiento de los Mocks de hardware.

---

## 🔗 Enlaces Rápidos y Archivos Destacados

*(Añadir aquí links directos a los PDFs o archivos Markdown una vez que estén cargados en el repositorio)*

* [Abrir Carpeta de Datasheets](./datasheets/)
* [📄 Leer Manual de Operación (Próximamente)](#)
* [📑 Leer Informe Técnico (Próximamente)](#)

---
*La documentación técnica se actualiza a medida que el proyecto avanza de fase (Hardware -> Firmware -> Software).*