# ⚙️ Módulo Modelo - Proyecto T.A.I.L.S.

Este directorio contiene la Capa de Datos y Hardware del patrón MVC. 

El Modelo es completamente "ciego" respecto a la interfaz gráfica. No sabe que existen botones, ventanas o colores. Su única responsabilidad es manejar los datos puros y la conexión física.

## 📄 Archivos

### `model.py`
Contiene la clase `Model`, la cual provee los siguientes servicios al Controlador:

1. **Gestión de Hardware (PySerial):**
   * Escaneo de puertos COM disponibles en el sistema operativo.
   * Apertura, cierre y mantenimiento de la conexión serial (por defecto a 115200 baudios).
   * Envío seguro de tramas de texto codificadas en UTF-8 hacia el microcontrolador.

2. **Gestión de Archivos (JSON):**
   * Guardado (`save_routine_to_file`): Serializa diccionarios de Python a formato `.json` estructurado para exportar las rutinas de movimiento.
   * Carga (`load_routine_from_file`): Deserializa archivos `.json` del disco duro y los convierte en listas de Python listas para ser inyectadas en el metrónomo de ejecución.