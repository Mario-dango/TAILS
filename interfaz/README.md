# 🤖 T.A.I.L.S. - Technical Articulated Intelligent Linkage System

T.A.I.L.S. es un entorno de software y hardware diseñado para el control cinemático, calibración y automatización de un brazo robótico articulado mediante comunicación serial con un microcontrolador (STM32 / ESP).

Este proyecto implementa una Interfaz Gráfica de Usuario (GUI) robusta desarrollada en **Python y PyQt5**, estructurada bajo el patrón de arquitectura de software **MVC (Modelo-Vista-Controlador)**.

## 🗂️ Estructura del Proyecto

El código está estrictamente modularizado para garantizar escalabilidad y fácil mantenimiento:

* 🧠 **/controller**: Contiene la lógica de negocio, temporizadores y la comunicación entre la vista y el modelo. Fraccionado en Managers especializados.
* 🎨 **/view**: Contiene la interfaz gráfica (GUI) fraccionada por paneles y pestañas. Es una capa puramente visual.
* ⚙️ **/model**: Gestiona la conexión de bajo nivel con el hardware (Puertos COM) y el sistema de archivos (JSON).
* 📁 **/rutinas**: Directorio de almacenamiento por defecto para las rutinas de aprendizaje (`.json`).
* 🖼️ **/resources**: Contiene los assets visuales (iconos, imágenes) para el "Modo Kawaii" y la UI en general.
* 📄 **`main.py`**: Punto de entrada (Entry Point) de la aplicación.
* 💅 **`style.css`**: Hoja de estilos global (Dark Theme).

## 🚀 Ejecución
Para iniciar el entorno de control, simplemente ejecuta el archivo principal desde la terminal:
```bash
python main.py