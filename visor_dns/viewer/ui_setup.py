# visor_dns/viewer/ui_setup.py
import tkinter as tk
from tkinter import ttk
from utils.colors import darken_color, lighten_color

class UISupport:
    """Configuración de interfaz de usuario"""
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Configurar estilo para una apariencia más moderna
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores profesionales
        bg_color = "#f8f9fa"
        accent_color = "#2c3e50"
        secondary_color = "#3498db"
        success_color = "#27ae60"
        warning_color = "#e74c3c"
        
        # Configurar fondo principal
        self.root.configure(bg=bg_color)

        # Hacer la ventana redimensionable y responsive
        self.root.resizable(True, True)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Definir tamaño inicial de la ventana
        window_width = 750
        window_height = 500

        # Centrar la ventana en la pantalla
        x_offset = (screen_width - window_width) // 2
        y_offset = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_offset}+{y_offset}")

        # Establecer tamaño mínimo de la ventana
        self.root.minsize(750, 500)

        main_frame = ttk.Frame(self.root, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== ENCABEZADO =====
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        # Logo/Título con icono
        title_container = ttk.Frame(header_frame)
        title_container.pack()
        
        # Título principal
        title = ttk.Label(title_container, text="DNS Cache Viewer", font=('Arial', 22, 'bold'), foreground=accent_color)
        title.pack(side=tk.LEFT)
        
        # Subtítulo
        subtitle = ttk.Label(header_frame, text="Análisis y monitorización de la caché DNS", font=('Arial', 10), foreground="#131313")
        subtitle.pack(pady=(5, 0))
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 25))
        
        # ===== CONTENEDOR PRINCIPAL CON DOS COLUMNAS =====
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Columna izquierda - Carga de archivos
        left_frame = ttk.LabelFrame(content_frame, text="CARGAR ARCHIVOS ", padding="20", relief="solid", borderwidth=1)
        left_frame.grid(row=0, column=0, padx=(0, 15), sticky="nsew")
        
        # Columna derecha - Visualización
        right_frame = ttk.LabelFrame(content_frame, text="VISUALIZACIÓN ", padding="20", relief="solid", borderwidth=1)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # ===== PANEL DE CARGA DE ARCHIVOS (IZQUIERDA) =====
        load_title = ttk.Label(left_frame, text="Importar datos de análisis", font=('AArial', 12, 'bold'), foreground=accent_color)
        load_title.pack(anchor="w", pady=(0, 15))
        
        # Botón para cargar estadísticas con icono
        stats_btn_frame = ttk.Frame(left_frame)
        stats_btn_frame.pack(fill=tk.X, pady=8)
        
        ttk.Button(stats_btn_frame, text="Cargar stats_real.csv", command=self.load_estadisticas, style="Accent.TButton").pack(fill=tk.X)
        
        # Botón para cargar archivos de caché con icono
        cache_btn_frame = ttk.Frame(left_frame)
        cache_btn_frame.pack(fill=tk.X, pady=8)
        
        ttk.Button(cache_btn_frame, text="Cargar cache_real.csv", command=self.load_cache_files, style="Accent.TButton").pack(fill=tk.X)
        
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, pady=20)
        
        # ===== PANEL DE ESTADO DE ARCHIVOS =====
        status_title = ttk.Label(left_frame, text="Estado de archivos", font=('AriArial', 11, 'bold'), foreground=accent_color)
        status_title.pack(anchor="w", pady=(0, 10))
        
        # Estado de archivo de estadísticas
        stats_status_frame = ttk.Frame(left_frame)
        stats_status_frame.pack(fill=tk.X, pady=5)
        
        self.stats_status_indicator = ttk.Label(stats_status_frame, text="●", font=('Arial', 14), foreground=warning_color)
        self.stats_status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stats_label = ttk.Label(stats_status_frame, text="stats_real.csv - No cargado", font=('Arial', 9))
        self.stats_label.pack(side=tk.LEFT)
        
        # Estado de archivos de caché
        cache_status_frame = ttk.Frame(left_frame)
        cache_status_frame.pack(fill=tk.X, pady=5)
        
        self.cache_status_indicator = ttk.Label(cache_status_frame, text="●", font=('Arial', 14), foreground=warning_color)
        self.cache_status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cache_label = ttk.Label(cache_status_frame, text="cache_real.csv - No cargado", font=('Arial', 9))
        self.cache_label.pack(side=tk.LEFT)
        

        # ===== PANEL DE VISUALIZACIÓN (DERECHA) =====
        view_title = ttk.Label(right_frame, text="Herramientas de análisis", font=('AriArial', 12, 'bold'), foreground=accent_color)
        view_title.pack(anchor="w", pady=(0, 20))
        
        # Botones de visualización con iconos y efectos hover
        btn_configs = [
            ("Estadísticas DNS", self.show_stats_dashboard, "#3498db"),
            ("Contenido de Caché", self.show_cache_content, "#9b59b6"),
            ("Hits y Misses por Dominio", self.show_hits_misses_per_domain_gui, "#2ecc71"),
        ]
        
        for text, command, color in btn_configs:
            btn_frame = ttk.Frame(right_frame)
            btn_frame.pack(fill=tk.X, pady=8)
            
            # Crear botón con estilo personalizado
            btn = tk.Button(btn_frame, text=text, command=command,
                        font=('Arial', 10),
                        bg=color,
                        fg="white",
                        bd=0,
                        padx=20,
                        pady=10,
                        cursor="hand2",
                        activebackground=darken_color(color, 0.2),
                        activeforeground="white")
            btn.pack(fill=tk.X)
            
            # Configurar hover effect
            btn.bind("<Enter>", lambda e, b=btn, c=color: b.config(bg=lighten_color(c, 0.1)))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))
        

        
        

