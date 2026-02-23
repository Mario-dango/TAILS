# 📁 Almacenamiento de Rutinas T.A.I.L.S.

Directorio de trabajo (Workspace) por defecto donde el software exporta y carga las secuencias de movimiento automatizadas.

## Formato de Datos
Las rutinas generadas en la pestaña "Aprendizaje" se exportan como archivos de texto plano en formato **JSON**.

### Estructura del Payload
Cada archivo contiene un arreglo de objetos (pasos), donde cada objeto define una acción cinemática absoluta:

```json
[
    {
        "type": "MOV",
        "x": 180,
        "y": 45,
        "z": 90,
        "g": "A"
    }
]