# Informe T.A.I.L.S. — proyecto LaTeX para Overleaf

## Cómo subirlo
1. Overleaf → **New Project → Upload Project** → elegir `Informe_TAILS_overleaf.zip`.
2. Menu → Compiler: **pdfLaTeX** (el que viene por defecto). Main document: `main.tex`.
3. Compilar. Si falta alguna referencia, recompilar una vez más (BibTeX corre solo).

## Estructura
```
main.tex              documento principal (orden de secciones y anexos)
preambulo.tex         paquetes, estilos, macros (\figura, \fig, \imagen, \TODO)
portada.tex           portada con el formato de la plantilla de la cátedra
secciones/01..08      una sección por cada apartado de la plantilla
anexos/A..F           pinout, protocolo, cálculos, plan de pruebas, código, PCB/BOM
referencias.bib       bibliografía (BibTeX, estilo unsrt)
figuras/              carpeta de imágenes, ver figuras/LEEME.md
```

## Imágenes
Cada imagen tiene reservado un recuadro gris "IMAGEN PENDIENTE" con el nombre de archivo esperado.
Se sube la imagen a `figuras/` con ese nombre (png/jpg/jpeg/pdf) y aparece sola al recompilar.
La lista completa y el origen sugerido de cada imagen están en `figuras/LEEME.md`.

## Pendientes (texto en rojo "[PENDIENTE: ...]")
Buscar `\TODO{` en el proyecto (Ctrl+Shift+F en Overleaf). Quedan por completar:
- Modelo exacto de cada motor y qué motor acciona cada eje (y si Z usa medio paso). Datos
  provisionales ya anotados en el `\TODO` de la tabla de motores (sección 3.2).
- Repetibilidad (método propuesto en 7.3) y alcance / área de trabajo en mm.
- Resultados del plan de pruebas (Anexo D) y resumen de `pytest`.
- Duración de la ISR de TIM2 (opcional, osciloscopio; método descripto en el Anexo C.4).

Resueltos en esta revisión (ya no son `\TODO`):
- R_CS = 0,1 Ω y V_REF por eje (X 610 mV, Y 813 mV, Z 623 mV) → 3.3.
- Relaciones de transmisión (X 5,68; Y 2,47; Z 2,47; pinza 1,60) → 3.10, y rango/resolución articular → 7.3.
- Tiempos de homing medidos (Y 3,53 s, Z 1,19 s, X 10,87 s; total 15,59 s) → 5.6 y 7.3.
- El KIA7805 lleva disipador → Anexo C.1.
- Conectores de finales de carrera J13→X, J14→Y, J15→Z → Anexo A.

## Correcciones al README del repositorio detectadas al redactar
- Pinout real (main.h): STEP X/Y/Z = PA2/PA1/PA0 y DIR X/Y/Z = PA5/PA4/PA3 (el README de `programa/` los tiene invertidos).
- El LM317 se alimenta desde +5 V (no desde VCC). El regulador de 5 V es KIA7805 y el transistor es BC558.
- El unipolar adaptado a bipolar es el NMB 17PM-K049U (1,8°). El PM42L-048 es bipolar de 7,5°.
- La fuente de alimentación es **AT** (no ATX).
- Firmware: el *timeout* de búsqueda del homing se hizo dependiente del eje (16 s en X, 10 s en
  Y/Z), porque X tardaba 10,87 s y expiraba el timeout original de 10 s aun habiendo llegado al
  home (`programa/RobotArm/Core/Src/motor_driver.c`). Requiere recompilar y reflashear.
