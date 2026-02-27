# visor_dns/viewer/stats_view.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from datetime import datetime
import traceback

class StatsView:
    """Mixin para visualización de estadísticas"""
    
    def load_estadisticas(self):
        """Carga el archivo de estadísticas"""
        file = filedialog.askopenfilename(title="Seleccionar stats_real.csv", 
                                        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        
        if file:
            self.estadisticas_file = file
            self.stats_label.config(text=f"stats_real.csv - Cargado", font=('Arial', 9, 'bold'))
            self.stats_status_indicator.config(foreground="#27ae60", text="✓")
            messagebox.showinfo("Éxito", "Archivo de estadísticas cargado correctamente")
    
    def show_stats_dashboard(self):
        """Función original que muestra los gráficos - mantener igual (para compatibilidad)"""
        if not self.estadisticas_file:
            messagebox.showwarning("Advertencia", 
                                "Primero debes cargar el archivo stats_real.csv\n"
                                "Usa el botón 'Cargar archivo stats_real.csv' en la sección de carga de archivos")
            return
        self.show_stats()
    
    def calculate_partial_values(self, df):
        """Calcula los valores parciales (incrementos) a partir de los acumulados"""
        # Hacer una copia del DataFrame
        df_partial = df.copy()
        
        # Lista de columnas acumuladas (excluyendo timestamp, hora)
        stat_columns = ['cache hits', 'cache hits (from query)', 'cache misses', 'cache misses (from query)', 'Incoming Queries A']
        
        # Calcular valores parciales
        for col in stat_columns:
            if col in df.columns:
                # Convertir a numérico
                df_partial[col] = pd.to_numeric(df_partial[col], errors='coerce')
                
                # Crear columna para valores parciales
                partial_col = f"{col} (parcial)"
                
                # El primer valor parcial es igual al acumulado
                partial_values = [df_partial[col].iloc[0]] if len(df_partial) > 0 else []
                
                # Calcular incrementos para las filas siguientes
                for i in range(1, len(df_partial)):
                    partial = df_partial[col].iloc[i] - df_partial[col].iloc[i-1]
                    partial_values.append(partial)
                
                df_partial[partial_col] = partial_values
        
        return df_partial
    
    def show_stats(self):
        """Muestra primero los datos en tabla y luego da opción de ver dashboard o exportar"""
        if not self.estadisticas_file:
            messagebox.showwarning("Advertencia", "Primero carga el archivo stats_real.csv")
            return
        
        try:
            # Leer el archivo CSV CON HEADERS
            try:
                df = pd.read_csv(self.estadisticas_file, dtype=str)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo CSV:\n{str(e)}")
                return
            
            # Asignar nombres de columnas MANUALMENTE
            column_names = ['Timestamp', 'Hora', 'Archivo', 'cache hits', 'cache hits (from query)', 'cache misses', 'cache misses (from query)', 'Incoming Queries A']
            
            # Verificar que tenemos suficientes columnas
            if df.shape[1] < len(column_names):
                messagebox.showerror("Error", 
                    f"El archivo tiene {df.shape[1]} columnas, pero se esperaban {len(column_names)}.\n"
                    f"Formato esperado: {column_names}")
                return
            
            # Asignar nombres a las columnas
            df = df.iloc[:, :len(column_names)]
            df.columns = column_names
            
            # ELIMINAR la columna "Archivo" del DataFrame
            df = df.drop('Archivo', axis=1)
            
            # Calcular valores parciales
            df_with_partials = self.calculate_partial_values(df)
            
            # Reordenar columnas para mostrar primero las parciales, luego acumuladas (sin Archivo)
            ordered_columns = ['Timestamp', 'Hora']
            
            # Añadir columnas en el orden deseado
            metric_pairs = [
                ('cache hits (parcial)', 'cache hits'),
                ('cache hits (from query) (parcial)', 'cache hits (from query)'),
                ('cache misses (parcial)', 'cache misses'),
                ('cache misses (from query) (parcial)', 'cache misses (from query)'),
                ('Incoming Queries A (parcial)', 'Incoming Queries A')
            ]
            
            for partial_col, accum_col in metric_pairs:
                if partial_col in df_with_partials.columns:
                    ordered_columns.append(partial_col)
                if accum_col in df_with_partials.columns:
                    ordered_columns.append(accum_col)
            
            # Filtrar solo las columnas que existen
            display_columns = [col for col in ordered_columns if col in df_with_partials.columns]
            df_display = df_with_partials[display_columns]
            
            print(f"Dataframe cargado: {df_display.shape[0]} filas x {df_display.shape[1]} columnas")
            
            # Crear ventana principal para mostrar tabla
            table_window = tk.Toplevel(self.root)
            table_window.title("Datos de Estadísticas DNS - Con Valores Parciales")
            table_window.geometry("1400x600")  # Ajustado sin la columna Archivo
            
            # Frame principal
            main_frame = ttk.Frame(table_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Título e información
            title_frame = ttk.Frame(main_frame)
            title_frame.pack(fill=tk.X, pady=(0, 10))
            
            ttk.Label(title_frame, text="Datos de Estadísticas DNS (Parciales y Acumulados)", font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
            
            total_rows = len(df_display)
            if total_rows > 0:
                first_time = f"{df_display['Timestamp'].iloc[0]} {df_display['Hora'].iloc[0]}"
                last_time = f"{df_display['Timestamp'].iloc[-1]} {df_display['Hora'].iloc[-1]}"
                time_range = f" | Período: {first_time} a {last_time}"
            else:
                time_range = ""
            
            info_text = f"Archivo: {os.path.basename(self.estadisticas_file)} | Registros: {total_rows}{time_range}"
            ttk.Label(main_frame, text=info_text, font=('Arial', 10)).pack(anchor="w", pady=(0, 10))
            
            # Treeview para mostrar datos
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            tree = ttk.Treeview(tree_frame, columns=df_display.columns.tolist(), show='headings')
            
            # Configurar columnas con anchos ajustados (sin columna Archivo)
            col_widths = {
                'Timestamp': 95, 'Hora': 75,
                'cache hits (parcial)': 110, 'cache hits': 95,
                'cache hits (from query) (parcial)': 140, 'cache hits (from query)': 125,
                'cache misses (parcial)': 110, 'cache misses': 95,
                'cache misses (from query) (parcial)': 160, 'cache misses (from query)': 140,
                'Incoming Queries A (parcial)': 160, 'Incoming Queries A': 140
            }
            
            for col in df_display.columns:
                # Nombres más cortos en los headers
                display_name = col.replace('(parcial)', '(Δ)').replace('(from query)', '(query)')
                tree.heading(col, text=display_name)
                tree.column(col, width=col_widths.get(col, 100), anchor='center')
            
            # Scrollbars
            v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
            tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            
            tree.grid(row=0, column=0, sticky='nsew')
            v_scroll.grid(row=0, column=1, sticky='ns')
            h_scroll.grid(row=1, column=0, sticky='ew')
            
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # Insertar datos
            for idx, row in df_display.iterrows():
                values = [str(row[col]) if pd.notna(row[col]) else '' for col in df_display.columns]
                tree.insert('', tk.END, values=values)
            
            # Frame de botones
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=15)
            
            def show_graphs():
                """Mostrar dashboard de gráficos"""
                self.show_graphs_dashboard(df_with_partials)
            
            def export_data():
                """Exportar datos a CSV"""
                export_file = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    initialfile=f"estadisticas_completas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                if export_file:
                    try:
                        df_with_partials.to_csv(export_file, index=False, encoding='utf-8')
                        messagebox.showinfo("Éxito", f"Datos exportados a:\n{export_file}")
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo exportar:\n{str(e)}")
            
            ttk.Button(button_frame, text="Ver Dashboard de Gráficos", command=show_graphs, width=25).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Exportar a CSV", command=export_data, width=15).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cerrar", command=table_window.destroy, width=10).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar los datos:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_graphs_dashboard(self, df_with_partials):
        """Dashboard de gráficos con solo las métricas solicitadas"""
        
        # Crear ventana del dashboard
        dash_window = tk.Toplevel(self.root)
        dash_window.title("Dashboard de Estadísticas DNS")
        dash_window.geometry("1175x900")
        
        # Lista para almacenar referencias a las figuras y sus metadatos
        self.all_figures = []  # Esto almacenará tuplas (figura, métrica, tipo)
        
        # Frame principal con scroll
        main_container = ttk.Frame(dash_window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior con botón de retroceso y título
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Botón de retroceso
        back_button = tk.Button(top_frame, text="←", font=('Arial', 16, 'bold'), 
                                width=3, height=1, command=dash_window.destroy,
                                relief=tk.RAISED, bd=2)
        back_button.pack(side=tk.LEFT)
        
        # Título del dashboard
        title_label = ttk.Label(top_frame, text="Dashboard de Estadísticas DNS", 
                                font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT, padx=20)
        
        # Botón de guardar todos los gráficos (arriba a la derecha del título)
        def save_all_charts():
            """Guarda los 6 gráficos en una carpeta seleccionada por el usuario"""
            folder_path = filedialog.askdirectory(title="Seleccionar carpeta para guardar gráficos")
            
            if not folder_path:
                return
            
            # Fecha y hora actual para el nombre de los archivos
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            try:
                saved_count = 0
                
                # Guardar todas las figuras almacenadas en self.all_figures
                for fig_info in self.all_figures:
                    fig, metric_title, chart_type = fig_info
                    
                    # Crear nombre de archivo seguro
                    safe_title = metric_title.replace(' ', '_').replace('(', '').replace(')', '')
                    safe_type = chart_type.replace(' ', '_')
                    
                    filename = f"{safe_title}_{safe_type}_{current_time}.png"
                    full_path = os.path.join(folder_path, filename)
                    
                    try:
                        fig.savefig(full_path, dpi=300, bbox_inches='tight')
                        print(f"Guardado: {filename}")
                        saved_count += 1
                    except Exception as e:
                        print(f"Error al guardar {filename}: {e}")
                        traceback.print_exc()
                
                if saved_count > 0:
                    messagebox.showinfo("Éxito", f"Se guardaron {saved_count} gráficos en:\n{folder_path}")
                else:
                    messagebox.showwarning("Advertencia", "No se encontraron gráficos para guardar")
                    
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron guardar los gráficos:\n{str(e)}")
                traceback.print_exc()
        
        # Botón para guardar todos los gráficos
        save_all_button = tk.Button(top_frame, text="Guardar todos los gráficos", 
                                   font=('Arial', 11, 'bold'),
                                   command=save_all_charts,
                                   relief=tk.RAISED, bd=2, padx=10, pady=5,
                                   cursor="hand2", bg="#3498db", fg="white")
        save_all_button.pack(side=tk.RIGHT, padx=5)
        
        # Canvas y scrollbar
        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Frame para contenido
        display_frame = ttk.Frame(scrollable_frame, padding="10")
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Solo las métricas solicitadas
        selected_metrics = [
            ('cache hits (from query)', 'Cache Hits (from query)'),
            ('cache misses (from query)', 'Cache Misses (from query)'),
            ('Incoming Queries A', 'Incoming Queries A')
        ]
        
        # Colores para gráficos
        colors = {
            'cache hits (from query)': ('#2ecc71', '#27ae60'),
            'cache misses (from query)': ('#e74c3c', '#c0392b'),
            'Incoming Queries A': ('#3498db', '#2980b9')
        }
        
        # Generar gráficos para cada métrica
        for metric, title in selected_metrics:
            partial_col = f"{metric} (parcial)"
            accum_col = metric
            
            # Verificar si las columnas existen
            has_partial = partial_col in df_with_partials.columns
            has_accum = accum_col in df_with_partials.columns
            
            if not has_partial and not has_accum:
                continue
            
            try:
                # Frame para esta métrica
                metric_frame = ttk.LabelFrame(display_frame, text=title, padding="10")
                metric_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=5)
                
                # Preparar datos temporales
                time_data = []
                for idx, row in df_with_partials.iterrows():
                    timestamp = str(row['Timestamp'])
                    hora = str(row['Hora'])
                    time_data.append(f"{timestamp} {hora}")
                
                # Calcular segundos transcurridos desde el inicio
                x_seconds = list(range(len(time_data)))
                x_labels = [str(i) for i in x_seconds]
                
                # Extraer valores
                partial_values = []
                accum_values = []

                if has_partial:
                    partial_values_raw = pd.to_numeric(df_with_partials[partial_col], errors='coerce').fillna(0).tolist()
                    # Excluir el primer valor y añadir 0 al inicio
                    if len(partial_values_raw) > 1:
                        partial_values = [0] + partial_values_raw[1:]
                    else:
                        partial_values = partial_values_raw

                if has_accum:
                    accum_values = pd.to_numeric(df_with_partials[accum_col], errors='coerce').fillna(0).tolist()
                
                # Obtener colores
                partial_color, accum_color = colors.get(metric, ('#95a5a6', '#7f8c8d'))
                
                # Frame para contener ambos gráficos lado a lado
                charts_frame = ttk.Frame(metric_frame)
                charts_frame.pack(fill=tk.BOTH, expand=True)
                
                # ===== GRÁFICO PARCIAL (IZQUIERDA) =====
                if has_partial and partial_values:
                    partial_frame = ttk.Frame(charts_frame)
                    partial_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
                    
                    # Header sin botón de guardar individual
                    header_frame = ttk.Frame(partial_frame)
                    header_frame.pack(fill=tk.X)
                    
                    # Gráfico
                    fig_partial, ax_partial = plt.subplots(figsize=(5.5, 3.5))
                    
                    if len(partial_values) > 1:
                        ax_partial.plot(x_seconds[1:], partial_values[1:], marker='o', markersize=4, 
                                        linewidth=2, color=partial_color, alpha=0.8)                   
                    ax_partial.set_ylabel('Incremento', fontsize=9)
                    ax_partial.set_xlabel('Tiempo (s)', fontsize=9)
                    ax_partial.set_title('Valores parciales', fontsize=10)
                    ax_partial.grid(True, alpha=0.3, axis='y')
                    
                    # Configurar ticks del eje X
                    if len(x_seconds) > 10:
                        step = max(1, len(x_seconds) // 10)
                        tick_indices = list(range(0, len(x_seconds), step))
                        if len(x_seconds) - 1 not in tick_indices:
                            tick_indices.append(len(x_seconds) - 1)
                        
                        x_seconds_partial = [x_seconds[i] for i in tick_indices]
                        x_labels_partial = [x_labels[i] for i in tick_indices]
                        
                        ax_partial.set_xticks(x_seconds_partial)
                        ax_partial.set_xticklabels(x_labels_partial)
                    else:
                        ax_partial.set_xticks(x_seconds)
                        ax_partial.set_xticklabels(x_labels)
                    
                    ax_partial.tick_params(axis='x', rotation=45, labelsize=8)
                    
                    plt.tight_layout()
                    
                    # Almacenar referencia a la figura
                    self.all_figures.append((fig_partial, title, 'parcial'))
                    
                    canvas_partial = FigureCanvasTkAgg(fig_partial, partial_frame)
                    canvas_partial.draw()
                    canvas_partial.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # ===== GRÁFICO ACUMULADO (DERECHA) =====
                if has_accum and accum_values:
                    accum_frame = ttk.Frame(charts_frame)
                    accum_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
                    
                    # Header sin botón de guardar individual
                    header_frame = ttk.Frame(accum_frame)
                    header_frame.pack(fill=tk.X)
                    
                    # Gráfico
                    fig_accum, ax_accum = plt.subplots(figsize=(5.5, 3.5))
                    
                    # Recalcular acumulados desde el segundo valor parcial
                    if has_partial and len(partial_values) > 1:
                        # Recalcular acumulados desde 0 usando los valores parciales modificados
                        accum_values_recalc = [0]
                        cumsum = 0
                        for pval in partial_values[1:]:  # Empezar desde el segundo valor (que es el original segundo)
                            cumsum += pval
                            accum_values_recalc.append(cumsum)
                        
                        x_seconds_accum = list(range(len(accum_values_recalc)))
                        accum_values_with_zero = accum_values_recalc
                    else:
                        x_seconds_accum = [0] + [s + 1 for s in x_seconds]
                        accum_values_with_zero = [0] + accum_values

                    # Y luego en el plot usar:
                    ax_accum.plot(x_seconds_accum, accum_values_with_zero, marker='o', markersize=4, 
                                linewidth=2, color=accum_color, alpha=0.8)
                    
                    ax_accum.set_ylabel('Valor total', fontsize=9)
                    ax_accum.set_xlabel('Tiempo (s)', fontsize=9)
                    ax_accum.set_title('Valores acumulados', fontsize=10)
                    ax_accum.grid(True, alpha=0.3)
                    
                    # Configurar ticks del eje X
                    if len(x_seconds_accum) > 10:
                        step = max(1, len(x_seconds_accum) // 10)
                        tick_indices = list(range(0, len(x_seconds_accum), step))
                        if len(x_seconds_accum) - 1 not in tick_indices:
                            tick_indices.append(len(x_seconds_accum) - 1)
                        
                        ax_accum.set_xticks([x_seconds_accum[i] for i in tick_indices])
                        ax_accum.set_xticklabels([str(x_seconds_accum[i]) for i in tick_indices])
                    else:
                        ax_accum.set_xticks(x_seconds_accum)
                        ax_accum.set_xticklabels([str(s) for s in x_seconds_accum])
                    
                    ax_accum.tick_params(axis='x', rotation=45, labelsize=8)
                    
                    plt.tight_layout()
                    
                    # Almacenar referencia a la figura
                    self.all_figures.append((fig_accum, title, 'acumulado'))
                    
                    canvas_accum = FigureCanvasTkAgg(fig_accum, accum_frame)
                    canvas_accum.draw()
                    canvas_accum.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                # ===== RESUMEN COMPARATIVO =====
                if has_partial and partial_values and accum_values:
                    summary_frame = ttk.Frame(metric_frame)
                    summary_frame.pack(fill=tk.X, pady=5, padx=10)
                    
                    accum_final = accum_values[-1] if accum_values else 0
                    
            except Exception as e:
                error_msg = f"Error al procesar {title}: {str(e)}"
                print(f"DEBUG ERROR: {error_msg}")
                error_label = ttk.Label(metric_frame, text=error_msg, foreground='red')
                error_label.pack()
        
        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def get_short_label(self, full_label):
        """Convierte etiquetas largas en versiones más cortas"""
        # Diccionario simple para tus columnas específicas
        mappings = {
            'cache hits': 'Cache Hits',
            'cache hits (from query)': 'Cache Hits (query)',
            'cache misses': 'Cache Misses',
            'cache misses (from query)': 'Cache Misses (query)',
            'Incoming Queries A': 'Incoming Queries'
        }
        
        # Retornar mapeo si existe, sino retornar el original
        return mappings.get(full_label, full_label)