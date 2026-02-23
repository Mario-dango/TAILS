# 🖨️ Diseño 3D y Estructura Mecánica - T.A.I.L.S.

Este directorio contiene los modelos tridimensionales (archivos `.STL` y fuentes CAD) necesarios para la fabricación física del brazo robótico T.A.I.L.S.

La estructura mecánica está pensada para ser fabricada mediante manufactura aditiva (Impresión 3D FDM), garantizando un equilibrio entre ligereza, resistencia estructural y bajo costo de prototipado.

---

## 🛠️ Origen del Diseño y Autoría

El modelado 3D de este proyecto se divide en dos partes fundamentales:

### 1. Estructura Base (Créditos)
La cinemática principal y los eslabones del brazo de 3 Grados de Libertad se basan en un diseño de código abierto.
* **Diseño Original:** *[Nombre del Proyecto Original o "Brazo Robótico genérico"]*
* **Autor Original:** *[Nombre del Autor o "Comunidad Thingiverse/Printables"]*
* **Enlace al diseño original:** *[Link de origen, si lo tienes]*

### 2. Modificaciones y Complementos (Custom Add-ons)
Para adaptar la estructura base a los requerimientos técnicos y electrónicos del proyecto T.A.I.L.S., se diseñaron piezas complementarias específicas desde cero:
* **Soportes para Sensores:** Monturas diseñadas a medida para fijar los finales de carrera (End-stops) de los ejes X, Y y Z.
* **Carcasa / Monturas de PCB:** Separadores y anclajes para fijar de manera segura la placa electrónica principal (Shield STM32) a la base del robot.
* **Engranajes y Transmisiones Personalizadas:** Componentes cinemáticos adaptados para mejorar el torque y la precisión de los servomotores.
* **Adaptaciones del Gripper:** Modificaciones en el actuador final para mejorar el agarre.

---

## 📸 Renders y Ensamblaje

*(Aquí puedes colocar capturas de pantalla de tu software CAD mostrando el brazo ensamblado o los complementos que diseñaste)*
![Render del Ensamblaje CAD](../resources/ensamblaje_3d_placeholder.png)

*(Aquí puedes agregar fotos de las piezas ya impresas y montadas)*
![Piezas Impresas y Montadas](../resources/piezas_impresas_placeholder.png)

---

## ⚙️ Recomendaciones de Impresión (Slicing)

Para garantizar la rigidez del brazo y evitar problemas de tolerancias en los ensambles mecánicos, se sugieren los siguientes parámetros para laminadores como Cura o PrusaSlicer:

* **Material recomendado:** PLA+ o PETG (mayor resistencia mecánica y térmica para los soportes de los motores).
* **Relleno (Infill):** Mínimo 20% - 30%. Se recomienda patrón cúbico o giroide para las piezas sometidas a mayor torque (eslabones base y hombro).
* **Perímetros:** 3 o 4 paredes para mejorar la resistencia a la torsión.
* **Tolerancias y "Pata de Elefante":** Es crítico activar la compensación de contracción (Elephant's foot compensation) en las primeras capas, especialmente para los engranajes o piezas que encastran. Una expansión de capa inicial no corregida impedirá que los ejes giren libremente.
* **Soportes:** Utilizar soportes tipo "Árbol" (Tree Supports) solo en las zonas de voladizo mayores a 50° para facilitar la limpieza posterior y no dañar las superficies de fricción.

---
*Todos los archivos `.STL` listos para imprimir se encuentran en las subcarpetas correspondientes.*