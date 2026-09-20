"""
LEARNING MANAGER (Gestor de Aprendizaje)
Se encarga exclusivamente de la pestaña "Aprendizaje": 
leer coordenadas, listarlas en la tabla (QTableWidget) y guardar rutinas en JSON.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QFileDialog

# Índices de columna de table_points, reexportados desde la vista para que haya
# una sola definición del orden. La tabla es
# ["#", "NOMBRE", "X", "Y", "Z", "GARRA", "VEL %", "ESPERA s"]: "#" es el número
# de paso (solo visual), "NOMBRE" es opcional, los datos del movimiento arrancan
# en X y "ESPERA s" es la pausa posterior al paso, en segundos.
#
# Están nombrados a propósito: la v1 usaba literales 0..4 y cada vez que se agregó
# una columna los accesos quedaron corridos, cruzando los campos de las rutinas.
from view.tab_teaching import (COL_NUM, COL_NAME, COL_X, COL_Y, COL_Z, COL_G,
                               COL_V, COL_T, RANGOS_CELDA, RANGOS_DECIMALES,
                               ESPERA_DECIMALES)


def formatear_espera(segundos):
    """Texto de una espera en segundos, con los decimales que usa la tabla."""
    return "%.*f" % (ESPERA_DECIMALES, float(segundos))


class LearningManager:
    def __init__(self, main_controller):
        # Recibe al Jefe para acceder a las variables globales y la interfaz
        self.app = main_controller
        self.view = main_controller.view
        self.model = main_controller.model

        # Se pone en True mientras el programa repuebla la tabla, para que el
        # guardián de validación no se dispare con nuestras propias escrituras.
        self._repoblando = False
        # Último valor válido por celda {(fila, col): texto}, para poder revertir
        # una edición inválida sin perder lo que había antes.
        self._valores_previos = {}

        self.init_connections()

    def init_connections(self):
        """Conecta los botones de la lista de puntos"""
        self.view.table_points.itemChanged.connect(self.validate_cell)
        self.view.btn_add_point.clicked.connect(self.add_point_to_table)
        self.view.btn_del_point.clicked.connect(self.delete_point_from_table)
        self.view.btn_clear_all.clicked.connect(self.clear_all_table)
        self.view.btn_save_file.clicked.connect(self.save_routine_json)

        # Reordenamiento de la rutina: el orden de la tabla ES el orden de
        # ejecución, y hasta ahora un punto capturado fuera de lugar obligaba a
        # borrarlo y volver a llevar el brazo hasta esa posición.
        self.view.btn_move_up.clicked.connect(self.move_point_up)
        self.view.btn_move_down.clicked.connect(self.move_point_down)
        self.view.table_points.itemSelectionChanged.connect(self.refresh_move_buttons)
        self.refresh_move_buttons()

    def log(self, prefix, msg):
        """Atajo para loguear en la consola inferior a través del jefe"""
        if hasattr(self.app, 'connection_mgr'):
            self.app.connection_mgr.log_console(prefix, msg)

    # --- LÓGICA DE LA TABLA ---
    def add_point_to_table(self):
        """Captura la posición actual y la agrega como una nueva fila en la tabla"""
        # Validación: Solo guardamos puntos si sabemos que el hardware está conectado
        if not self.model.is_connected():
            QMessageBox.warning(self.view, "Error de Conexión", 
            "Debe conectar el robot para capturar una posición válida.")
            return
     
        # 1. Obtener datos actuales desde la memoria global del Jefe
        x = self.app.current_pos['x']
        y = self.app.current_pos['y']
        z = self.app.current_pos['z']
        g = self.app.gripper_state
        # Velocidad del segmento: por defecto la que se está usando (slider). Editable en la tabla.
        v = self.view.slider_speed.value()
        # Espera posterior al paso, en segundos. Nace en 0 (encadenar sin pausa)
        # y se edita en la tabla: es el tiempo que el brazo se queda quieto antes
        # de que la interfaz mande el paso siguiente.
        t = 0.0

        # 2. Crear una nueva fila al final de la tabla
        row_pos = self.view.table_points.rowCount()
        self.view.table_points.insertRow(row_pos)

        # 3. Insertar los valores en las celdas. El nombre nace vacío: es
        #    opcional y lo completa el usuario para dar contexto al punto.
        self._repoblando = True
        self.view.table_points.setItem(row_pos, COL_NAME, QTableWidgetItem(""))
        self.view.table_points.setItem(row_pos, COL_X, QTableWidgetItem(str(x)))
        self.view.table_points.setItem(row_pos, COL_Y, QTableWidgetItem(str(y)))
        self.view.table_points.setItem(row_pos, COL_Z, QTableWidgetItem(str(z)))
        self.view.table_points.setItem(row_pos, COL_G, QTableWidgetItem(g))
        self.view.table_points.setItem(row_pos, COL_V, QTableWidgetItem(str(v)))
        self.view.table_points.setItem(
            row_pos, COL_T, QTableWidgetItem(formatear_espera(t)))
        self._repoblando = False
        for col, val in ((COL_NAME, ""), (COL_X, x), (COL_Y, y), (COL_Z, z),
                         (COL_G, g), (COL_V, v), (COL_T, formatear_espera(t))):
            self._valores_previos[(row_pos, col)] = str(val)
        self.renumber_rows()
        self.refresh_move_buttons()

        self.log("INFO", f"Punto agregado: X{x} Y{y} Z{z} {g} V{v}%")

    def renumber_rows(self):
        """Reescribe la columna '#' y el contador de la cabecera.

        La columna 0 es puramente visual: se recalcula tras cada alta o baja para
        que no queden huecos en la numeración.
        """
        tabla = self.view.table_points
        self._repoblando = True
        for fila in range(tabla.rowCount()):
            item = QTableWidgetItem(str(fila + 1))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            tabla.setItem(fila, COL_NUM, item)
        self._repoblando = False

        if hasattr(self.view.tab_teach, 'lbl_count'):
            self.view.tab_teach.lbl_count.setText("%d puntos" % tabla.rowCount())

    def validate_cell(self, item):
        """Rechaza valores no numéricos o fuera de rango (recorrido, velocidad, espera).

        El PointDelegate ya impide tipear basura desde el editor; esto cubre el
        pegado y cualquier escritura que no pase por él: revierte la celda al
        último valor bueno y explica por qué el valor no es válido.
        """
        if self._repoblando:
            return
        col = item.column()
        clave = (item.row(), col)

        # La espera es la única celda con decimales: se valida aparte y se
        # normaliza al formato de la tabla (0.0) para que el JSON no herede un
        # "1,5" con coma ni un "2" pelado según cómo se haya tipeado.
        if col in RANGOS_DECIMALES:
            etiqueta, minimo, maximo = RANGOS_DECIMALES[col]
            texto = (item.text() or "").strip().replace(",", ".")
            try:
                valor = float(texto)
            except ValueError:
                self._revert_cell(item, "«%s» no es un número." % item.text(),
                                  etiqueta, minimo, maximo, "segundos")
                return
            if not (minimo <= valor <= maximo):
                self._revert_cell(item, "Se recibió «%s»." % texto,
                                  etiqueta, minimo, maximo, "segundos")
                return
            normalizado = formatear_espera(valor)
            if item.text() != normalizado:
                self._repoblando = True
                item.setText(normalizado)
                self._repoblando = False
            self._valores_previos[clave] = normalizado
            return

        if col not in RANGOS_CELDA:
            self._valores_previos[clave] = item.text()
            return          # "#", NOMBRE y GARRA no tienen rango numérico

        etiqueta, minimo, maximo = RANGOS_CELDA[col]
        texto = (item.text() or "").strip()
        unidad = "%" if col == COL_V else "pasos"

        try:
            valor = int(texto)
        except ValueError:
            self._revert_cell(item, "«%s» no es un número entero." % texto,
                              etiqueta, minimo, maximo, unidad)
            return

        if not (minimo <= valor <= maximo):
            self._revert_cell(item, "Se recibió «%d»." % valor,
                              etiqueta, minimo, maximo, unidad)
            return

        self._valores_previos[clave] = str(valor)

    def _revert_cell(self, item, detalle, etiqueta, minimo, maximo, unidad):
        """Restaura el último valor válido de la celda y avisa por qué."""
        anterior = self._valores_previos.get((item.row(), item.column()),
                                             str(minimo))
        # %g: los rangos enteros se siguen leyendo "0 y 580" y el de la espera,
        # con extremos float, no sale como "0.0 y 60.0".
        rango = "%g y %g" % (minimo, maximo)
        self._repoblando = True
        item.setText(anterior)
        self._repoblando = False
        QMessageBox.warning(
            self.view, "Valor fuera de rango",
            "\n".join([
                # Sólo la inicial: capitalize() convertiría "eje Z" en "Eje z".
                "%s admite valores entre %s %s."
                % (etiqueta[:1].upper() + etiqueta[1:], rango, unidad),
                detalle,
                "",
                "Se restauró el valor anterior (%s)." % anterior,
            ]))

    # --- REORDENAMIENTO DE LA RUTINA ---
    def move_point_up(self):
        self._mover_fila(-1)

    def move_point_down(self):
        self._mover_fila(+1)

    def _mover_fila(self, delta):
        """Intercambia la fila seleccionada con su vecina y sigue la selección.

        Se intercambia el CONTENIDO de las celdas en vez de usar
        insertRow/removeRow: así el QTableWidgetItem del delegate no se recrea y
        la fila mantiene sus banderas (la columna '#' no editable, por ejemplo).
        """
        tabla = self.view.table_points
        fila = tabla.currentRow()
        destino = fila + delta
        if fila < 0 or not (0 <= destino < tabla.rowCount()):
            return

        # El guardián de validación se dispara con itemChanged: mientras movemos
        # somos nosotros los que escribimos, así que lo silenciamos.
        self._repoblando = True
        for col in range(tabla.columnCount()):
            if col == COL_NUM:
                continue        # es sólo el número de orden: lo reescribe renumber_rows
            a = tabla.item(fila, col)
            b = tabla.item(destino, col)
            texto_a = a.text() if a else ""
            texto_b = b.text() if b else ""
            if a is None:
                a = QTableWidgetItem("")
                tabla.setItem(fila, col, a)
            if b is None:
                b = QTableWidgetItem("")
                tabla.setItem(destino, col, b)
            a.setText(texto_b)
            b.setText(texto_a)
        self._repoblando = False

        tabla.selectRow(destino)        # la selección viaja con el punto
        self.renumber_rows()
        self._reindexar_valores_previos()
        self.refresh_move_buttons()

    def refresh_move_buttons(self):
        """Deshabilita Subir/Bajar en los extremos y sin selección."""
        tabla = self.view.table_points
        fila = tabla.currentRow()
        hay_seleccion = fila >= 0 and tabla.rowCount() > 1
        self.view.btn_move_up.setEnabled(hay_seleccion and fila > 0)
        self.view.btn_move_down.setEnabled(
            hay_seleccion and fila < tabla.rowCount() - 1)

    def _reindexar_valores_previos(self):
        """Reconstruye el mapa {(fila, col): texto} desde la tabla real.

        Está indexado por número de fila, así que cualquier alta, baja o
        reordenamiento lo desfasa. Antes no se reconstruía tras un borrado y el
        'revertir al último valor válido' podía restaurar el dato de otra fila.
        """
        tabla = self.view.table_points
        self._valores_previos = {}
        for fila in range(tabla.rowCount()):
            for col in range(tabla.columnCount()):
                item = tabla.item(fila, col)
                if item is not None:
                    self._valores_previos[(fila, col)] = item.text()

    def delete_point_from_table(self):
        """Elimina la fila que el usuario tenga seleccionada con el mouse"""
        current_row = self.view.table_points.currentRow()
        if current_row >= 0:
            self.view.table_points.removeRow(current_row)
            self.renumber_rows()
            self._reindexar_valores_previos()
            self.refresh_move_buttons()

    def clear_all_table(self):
        """Vacía toda la tabla previa confirmación de seguridad"""
        # Verificar si hay algo que borrar para no lanzar popups innecesarios
        if self.view.table_points.rowCount() == 0:
            return

        # Pop-up de confirmación (Seguridad UX)
        reply = QMessageBox.question(
            self.view, 
            'Confirmar Limpieza', 
            "¿Estás seguro de que quieres borrar TODOS los puntos de la lista?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.view.table_points.setRowCount(0)
            self.renumber_rows()
            self._reindexar_valores_previos()
            self.refresh_move_buttons()
            self.log("INFO", "Tabla de puntos limpiada.")

    # --- EXPORTAR ARCHIVO ---
    def save_routine_json(self):
        """Lee la tabla, la convierte a un formato de lista y la guarda en .json"""
        if not self.model.is_connected():
            self.log("ERROR", "No se puede guardar la rutina: Conexión inactiva.")
            QMessageBox.critical(self.view, "Error", "Debe estar conectado para exportar una rutina válida.")
            return

        rows = self.view.table_points.rowCount()
        if rows == 0:
            QMessageBox.warning(self.view, "Aviso", "La lista está vacía.")
            return

        # 1. Empaquetar datos de la tabla visual a una estructura Python
        routine = []
        for i in range(rows):
            # Velocidad del segmento (%). Se valida/limita a 10..100; si la celda
            # quedó vacía o inválida, usamos 50 como valor seguro por defecto.
            try:
                v = int(self.view.table_points.item(i, COL_V).text())
            except (AttributeError, ValueError):
                v = 50
            v = max(10, min(100, v))

            # Espera posterior al paso, en segundos. Igual que la velocidad, si
            # la celda quedó vacía o ilegible se asume 0 (sin pausa).
            try:
                t = float(self.view.table_points.item(i, COL_T).text()
                          .replace(",", "."))
            except (AttributeError, ValueError):
                t = 0.0
            t = max(0.0, min(RANGOS_DECIMALES[COL_T][2], t))

            p = {
                "type": "MOV",
                "x": int(self.view.table_points.item(i, COL_X).text()),
                "y": int(self.view.table_points.item(i, COL_Y).text()),
                "z": int(self.view.table_points.item(i, COL_Z).text()),
                "g": self.view.table_points.item(i, COL_G).text(),
                "v": v
            }

            # La espera sólo se escribe si el operador la cargó: un "t": 0 en
            # cada paso ensuciaría el JSON, y al ejecutar la ausencia de la clave
            # ya significa "sin pausa".
            if t > 0:
                p["t"] = round(t, ESPERA_DECIMALES)

            # Nombre del punto: opcional. Sólo se escribe la clave "n" si el
            # usuario puso algo, para no ensuciar el JSON con cadenas vacías.
            celda_nombre = self.view.table_points.item(i, COL_NAME)
            nombre = celda_nombre.text().strip() if celda_nombre else ""
            if nombre:
                p["n"] = nombre

            routine.append(p)
            
        # 2. ABRIR DIÁLOGO DE SISTEMA PARA GUARDAR
        options = QFileDialog.Options()
        # Usamos self.app.routines_path para que siempre abra en la carpeta correcta
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, 
            "Guardar Rutina", 
            self.app.routines_path, 
            "Archivos JSON (*.json);;Todos (*)", 
            options=options
        )
        
        # 3. Guardar usando el Modelo
        if file_path:
            # Aseguramos que termine en .json aunque el usuario olvide escribirlo
            if not file_path.endswith('.json'):
                file_path += '.json'
                
            if self.model.save_routine_to_file(file_path, routine):
                self.log("INFO", f"Rutina guardada en: {file_path}")
            else:
                self.log("ERROR", "No se pudo guardar el archivo.")