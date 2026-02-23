"""
PESTAÑA DE APRENDIZAJE (TEACHING TAB)
Este widget contiene dos secciones principales:
1. Panel de Control Manual (Jogging): Flechas de movimiento, velocidad y control de garra.
2. Lista de Puntos (Rutina): Tabla para guardar coordenadas y botones de gestión de archivo.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
                             QPushButton, QLabel, QSlider, QRadioButton, QButtonGroup, 
                             QTableWidget, QHeaderView)
from PyQt5.QtCore import Qt

class TeachingTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Layout principal horizontal: Izquierda (Jogging) | Derecha (Tabla)
        self.layout = QHBoxLayout(self)

        # ==========================================
        # COLUMNA IZQUIERDA: CONTROLES MANUALES (JOGGING)
        # ==========================================
        col_jog = QVBoxLayout()
        
        # --- A. GRUPO: FLECHAS DE MOVIMIENTO ---
        grp_jog = QGroupBox("Control Manual (Jogging)")
        grid_jog = QGridLayout(grp_jog)
        
        # Botones de Ejes (X, Y, Z)
        # Nota: Los iconos se asignan en view.py
        self.btn_x_plus = QPushButton("X+")
        self.btn_x_plus.setMinimumHeight(64)
        self.btn_x_plus.setToolTip("Incrementar posición X.")
        
        self.btn_x_minus = QPushButton("X-")
        self.btn_x_minus.setMinimumHeight(64)
        self.btn_x_minus.setToolTip("Reducir posición X.")
        
        self.btn_y_plus = QPushButton("Y+")
        self.btn_y_plus.setMinimumHeight(64)
        self.btn_y_plus.setToolTip("Incrementar posición Y.")
        
        self.btn_y_minus = QPushButton("Y-")
        self.btn_y_minus.setMinimumHeight(64)
        self.btn_y_minus.setToolTip("Reducir posición Y.")
        
        self.btn_z_plus = QPushButton("Z+")
        self.btn_z_plus.setMinimumHeight(64)
        self.btn_z_plus.setToolTip("Incrementar posición Z.")
        
        self.btn_z_minus = QPushButton("Z-")
        self.btn_z_minus.setMinimumHeight(64)
        self.btn_z_minus.setToolTip("Reducir posición Z.")
        
        # Botones Especiales de Centrado (Home Parcial)
        self.btn_home_xy = QPushButton("Hxy")
        self.btn_home_xy.setMinimumHeight(64)
        self.btn_home_xy.setToolTip("Mandar a home los motores X e Y.")
        # Estilo específico para diferenciarlo (Cyan)
        self.btn_home_xy.setStyleSheet("background-color: #00bcd4; color: black; font-weight: bold;")
        
        self.btn_home_z = QPushButton("Hz")
        self.btn_home_z.setToolTip("Mandar a home al motor Z.")
        # Estilo específico (Cyan)
        self.btn_home_z.setStyleSheet("background-color: #00bcd4; color: black; font-weight: bold;")

        # Distribución en la Grilla (Fila, Columna)
        # Layout en cruz para X/Y
        grid_jog.addWidget(self.btn_y_plus, 0, 1)
        grid_jog.addWidget(self.btn_x_minus, 1, 0)
        grid_jog.addWidget(self.btn_home_xy, 1, 1) # Centro XY
        grid_jog.addWidget(self.btn_x_plus, 1, 2)
        grid_jog.addWidget(self.btn_y_minus, 2, 1)
        
        # Separador visual y Columna Z
        grid_jog.addWidget(QLabel("   |   "), 1, 3) 
        grid_jog.addWidget(self.btn_z_plus, 0, 4)
        grid_jog.addWidget(self.btn_home_z, 1, 4) # Centro Z
        grid_jog.addWidget(self.btn_z_minus, 2, 4)
        
        # --- B. GRUPO: VELOCIDAD ---
        grp_speed = QGroupBox("Velocidad de Movimiento (%)")
        lay_speed = QHBoxLayout(grp_speed)
        
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setMinimum(10)
        self.slider_speed.setMaximum(100)
        self.slider_speed.setValue(50) # Valor inicial
        self.slider_speed.setTickPosition(QSlider.TicksBelow)
        self.slider_speed.setTickInterval(10)
        
        self.lbl_speed_val = QLabel("50%")
        self.lbl_speed_val.setFixedWidth(35)
        
        lay_speed.addWidget(self.slider_speed)
        lay_speed.addWidget(self.lbl_speed_val)
        
        # Agregamos primero la velocidad y luego la grilla de flechas
        col_jog.addWidget(grp_speed)
        col_jog.addWidget(grp_jog)
        
        # --- C. GRUPO: INCREMENTO (PASOS) ---
        grp_step = QGroupBox("Incremento (Grados)")
        lay_step = QHBoxLayout(grp_step)
        
        self.radio_1deg = QRadioButton("1°")
        self.radio_10deg = QRadioButton("10°")
        self.radio_50deg = QRadioButton("50°")
        self.radio_10deg.setChecked(True) # Default
        
        # Grupo lógico de botones (para saber cuál está activo)
        self.step_group = QButtonGroup()
        self.step_group.addButton(self.radio_1deg, 1)
        self.step_group.addButton(self.radio_10deg, 10)
        self.step_group.addButton(self.radio_50deg, 50)
        
        lay_step.addWidget(self.radio_1deg)
        lay_step.addWidget(self.radio_10deg)
        lay_step.addWidget(self.radio_50deg)
        col_jog.addWidget(grp_step)
        
        # --- D. GRUPO: GARRA MANUAL ---
        grp_man_grip = QGroupBox("Garra")
        lay_man_grip = QHBoxLayout(grp_man_grip)
        
        self.btn_open_grip = QPushButton("Abrir")
        self.btn_open_grip.setToolTip("Abrir garra según ángulo seteado.")
        
        self.btn_close_grip = QPushButton("Cerrar")
        self.btn_close_grip.setToolTip("Cerrar garra según ángulo seteado.")
        
        lay_man_grip.addWidget(self.btn_open_grip)
        lay_man_grip.addWidget(self.btn_close_grip)
        col_jog.addWidget(grp_man_grip)
        
        col_jog.addStretch() # Empujar todo arriba
        
        # ==========================================
        # COLUMNA DERECHA: LISTA DE PUNTOS (RUTINA)
        # ==========================================
        col_list = QVBoxLayout()
        
        # Título
        col_list.addWidget(QLabel("Rutina Actual:"))
        
        # Tabla
        self.table_points = QTableWidget()
        self.table_points.setColumnCount(4)
        self.table_points.setHorizontalHeaderLabels(["X", "Y", "Z", "G"])
        # Hacer que las columnas se estiren para ocupar todo el ancho
        self.table_points.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        col_list.addWidget(self.table_points)
        
        # Botonera de Gestión de Lista
        lay_btns_list = QHBoxLayout()
        
        self.btn_add_point = QPushButton("Guardar Punto Actual")
        self.btn_add_point.setToolTip("Agregar punto actual a la lista de posiciones.")

        self.btn_del_point = QPushButton("Borrar Seleccionado")
        self.btn_del_point.setToolTip("Borrar fila seleccionada.")
        
        self.btn_clear_all = QPushButton("Limpiar Todo")
        self.btn_clear_all.setToolTip("Borrar todas las posiciones de la lista.")
        self.btn_clear_all.setStyleSheet("background-color: #d32f2f; font-weight: bold;") # Rojo alerta
        
        self.btn_save_file = QPushButton("Guardar Rutina JSON")
        self.btn_save_file.setToolTip("Exportar lista a un archivo .json.")
        
        lay_btns_list.addWidget(self.btn_add_point)
        lay_btns_list.addWidget(self.btn_del_point)
        lay_btns_list.addWidget(self.btn_clear_all) 
        lay_btns_list.addWidget(self.btn_save_file)
        
        col_list.addLayout(lay_btns_list)
        
        # ==========================================
        # ENSAMBLAJE FINAL
        # ==========================================
        # Proporción: Jogging (1 parte) vs Lista (2 partes)
        self.layout.addLayout(col_jog, 1)
        self.layout.addLayout(col_list, 2)