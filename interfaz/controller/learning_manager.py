"""
LEARNING MANAGER (Gestor de Aprendizaje)
Se encarga exclusivamente de la pestaña "Aprendizaje": 
leer coordenadas, listarlas en la tabla (QTableWidget) y guardar rutinas en JSON.
"""

from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QFileDialog

class LearningManager:
    def __init__(self, main_controller):
        # Recibe al Jefe para acceder a las variables globales y la interfaz
        self.app = main_controller
        self.view = main_controller.view
        self.model = main_controller.model

        self.init_connections()

    def init_connections(self):
        """Conecta los botones de la lista de puntos"""
        self.view.btn_add_point.clicked.connect(self.add_point_to_table)
        self.view.btn_del_point.clicked.connect(self.delete_point_from_table)
        self.view.btn_clear_all.clicked.connect(self.clear_all_table)
        self.view.btn_save_file.clicked.connect(self.save_routine_json)

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
        
        # 2. Crear una nueva fila al final de la tabla
        row_pos = self.view.table_points.rowCount()
        self.view.table_points.insertRow(row_pos)
        
        # 3. Insertar los valores en las celdas (Col 0=X, 1=Y, 2=Z, 3=G)
        self.view.table_points.setItem(row_pos, 0, QTableWidgetItem(str(x)))
        self.view.table_points.setItem(row_pos, 1, QTableWidgetItem(str(y)))
        self.view.table_points.setItem(row_pos, 2, QTableWidgetItem(str(z)))
        self.view.table_points.setItem(row_pos, 3, QTableWidgetItem(g))
        
        self.log("INFO", f"Punto agregado: X{x} Y{y} Z{z} {g}")

    def delete_point_from_table(self):
        """Elimina la fila que el usuario tenga seleccionada con el mouse"""
        current_row = self.view.table_points.currentRow()
        if current_row >= 0:
            self.view.table_points.removeRow(current_row)

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
            p = {
                "type": "MOV",
                "x": int(self.view.table_points.item(i, 0).text()),
                "y": int(self.view.table_points.item(i, 1).text()),
                "z": int(self.view.table_points.item(i, 2).text()),
                "g": self.view.table_points.item(i, 3).text()
            }
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