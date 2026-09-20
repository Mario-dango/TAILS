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
        "g": "A",
        "v": 60,
        "t": 1.5,
        "n": "Tomar pieza"
    }
]
```

| Clave | Obligatoria | Significado |
| :--- | :--- | :--- |
| `type` | sí | Tipo de paso. Hoy sólo `"MOV"` (movimiento absoluto). |
| `x` `y` `z` | sí | Destino de cada eje, **en pasos**. Se recortan al recorrido real al ejecutar. |
| `g` | no | Garra: `"A"` abrir, `"C"` cerrar. Sin la clave, la garra no se toca. |
| `v` | no | Velocidad del segmento en % (10–100). Por defecto 50. |
| `t` | no | **Espera posterior al paso, en segundos** (0–60). Por defecto 0. |
| `n` | no | Nombre del punto, para identificarlo en el log y en el panel Secuencia. |

Las claves opcionales que faltan no rompen nada: una rutina guardada antes de que existieran `v`, `t` o `n` se ejecuta con los valores por defecto, o sea con el comportamiento de siempre.
