# Imágenes del informe

Colocar cada imagen en esta carpeta con **exactamente** el nombre indicado (extensión .png, .jpg, .jpeg o .pdf).
Al recompilar, el recuadro gris "IMAGEN PENDIENTE" se reemplaza solo por la imagen.

Opcional: `logo_fing.png` (logo de la facultad en la portada).

| Nombre de archivo | Sección | Qué imagen va (origen sugerido en el repo) |
|---|---|---|
| `portada_robot` | portada | foto frontal del robot (formato .jpg/.png) |
| `mk2_original` | 01_introduccion | render o foto del diseño original (carpeta `diseño 3D/jackyltle_Structure/images`) |
| `robot_general` | 01_introduccion | foto del robot completo, p. ej. `Documentación/Fotos/extra/TAILS.jpg` |
| `diagrama_bloques` | 02_esquema_tecnologico | `Documentación/Diagrama de Bloques.png` (renombrar a `diagrama_bloques.png`). Nota: el bloque "Regulador DC→DC" corresponde a reguladores lineales |
| `pinout_stm32` | 03_detalle_modulos | `Documentación/conf_pines_stm32f103c8t6.png` |
| `motores` | 03_detalle_modulos | fotos de `Documentación/Fotos/motores` |
| `a4988` | 03_detalle_modulos | `Documentación/datasheets/A4988-Stepper-Motor-Driver-Pinout.jpg` |
| `sch_finales_carrera` | 03_detalle_modulos | `PCB/resources/sch07.png` (o `sch01.png` con los tres ejes) |
| `soportes_sensores` | 03_detalle_modulos | render de `soporteSensor1/2.SLDPRT` o foto de los soportes montados |
| `sch_alimentacion` | 03_detalle_modulos | `PCB/resources/sch04.png` |
| `pcb_3d` | 03_detalle_modulos | `PCB/resources/model.png` |
| `cubemx_clock` | 05_programacion | captura de la pestaña Clock Configuration de `RobotArm.ioc` |
| `gui_calibracion` | 05_programacion | `interfaz/images/Calibración/calibration.png` |
| `gui_aprendizaje` | 05_programacion | `interfaz/images/Aprendizaje/learn.png` |
| `gui_ejecucion` | 05_programacion | `interfaz/images/Ejecución/execution.png` |
| `montaje_protoboard` | 06_montaje_ensayos | foto de la etapa de protoboard (`Documentación/Fotos`, 2023) |
| `ensayo_rutina` | 06_montaje_ensayos | secuencia de fotos del robot ejecutando `rut1.json` o captura de la consola |
| `pcb_montada` | 06_montaje_ensayos | foto de la PCB montada (`Documentación/Fotos/extra`) |
| `montaje_mecanico` | 06_montaje_ensayos | foto del montaje mecánico con finales de carrera |
| `resultado_final` | 07_resultados | foto del robot final tomando una pieza |
| `sch_completo` | F_pcb_bom | `PCB/resources/schematic.png` (idealmente exportado a PDF desde KiCad para conservar la resolución) |
| `pcb_layout` | F_pcb_bom | `PCB/resources/layout.png` y `lay02.png` |
| `bom` | F_pcb_bom | `PCB/resources/boom.png`, o reemplazar por una tabla |
| `sch_stm32` | F_pcb_bom | `PCB/resources/sch03.png` |
| `sch_drivers` | F_pcb_bom | `PCB/resources/sch05.png` o `sch08.png` |
| `sch_leds` | F_pcb_bom | `PCB/resources/sch06.png` |
| `sch_servo_estop` | F_pcb_bom | `PCB/resources/sch09.png` / `sch02.png` |
