"""
PESTAÑA DE EJECUCIÓN (EXECUTION TAB)
Este widget contiene los controles para automatizar el robot:
Carga de archivos JSON, barra de progreso, controles de reproducción y log detallado.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QTextEdit

class ExecutionTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Layout principal de la pestaña (Vertical)
        self.layout = QVBoxLayout(self)
        
        # ==========================================
        # 1. SECCIÓN: ARCHIVO
        # ==========================================
        lay_file = QHBoxLayout()
        
        self.lbl_file = QLabel("Archivo: Ninguno cargado")
        
        self.btn_load_file = QPushButton("Cargar Rutina")
        self.btn_load_file.setToolTip("Cargar archivo de rutina en formato JSON.")
        
        self.btn_preview = QPushButton("Ver Contenido")
        self.btn_preview.setToolTip("Ver contenido del archivo JSON cargado.")
        # Estilo naranja brillante para destacarlo
        self.btn_preview.setStyleSheet("background-color: #FF9800; color: black; font-weight: bold;") 
        
        lay_file.addWidget(self.lbl_file)
        lay_file.addWidget(self.btn_load_file)
        lay_file.addWidget(self.btn_preview)
        
        self.layout.addLayout(lay_file)
        
        # ==========================================
        # 2. SECCIÓN: PROGRESO
        # ==========================================
        self.progress_bar = QProgressBar()
        # Por defecto empieza en 0
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)
        
        # ==========================================
        # 3. SECCIÓN: CONTROLES DE REPRODUCCIÓN
        # ==========================================
        lay_ctrl = QHBoxLayout()
        
        self.btn_play = QPushButton("PLAY")
        self.btn_play.setToolTip("Ejecutar rutina seleccionada y cargada.")
        self.btn_play.setStyleSheet("background-color: #2e7d32; font-weight: bold; font-size: 14px; min-height: 40px;") # Verde grande
        
        self.btn_pause = QPushButton("PAUSA")
        self.btn_pause.setToolTip("Pausar rutina que se está ejecutando.")
        self.btn_pause.setStyleSheet("font-weight: bold; font-size: 14px; min-height: 40px;")
        
        self.btn_stop_run = QPushButton("DETENER")
        self.btn_stop_run.setToolTip("Detener rutina que se ejecuta actualmente.")
        self.btn_stop_run.setStyleSheet("background-color: #c62828; font-weight: bold; font-size: 14px; min-height: 40px;") # Rojo grande
        
        lay_ctrl.addWidget(self.btn_play)
        lay_ctrl.addWidget(self.btn_pause)
        lay_ctrl.addWidget(self.btn_stop_run)
        
        self.layout.addLayout(lay_ctrl)
        
        # ==========================================
        # 4. SECCIÓN: LOG DE EJECUCIÓN (Terminal)
        # ==========================================
        self.txt_run_log = QTextEdit()
        self.txt_run_log.setReadOnly(True)
        self.txt_run_log.setPlaceholderText("Los detalles de ejecución de la rutina aparecerán aquí...")
        
        self.layout.addWidget(self.txt_run_log)