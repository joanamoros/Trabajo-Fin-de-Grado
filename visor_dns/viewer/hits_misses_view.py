# visor_dns/viewer/hits_misses_view.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import csv
import math

class HitsMissesView:
    """Mixin para análisis de hits y misses por dominio"""
    
    def show_hits_misses_per_domain_gui(self):
        """Muestra directamente la ventana de análisis de hits/misses con gráficos"""
        import csv
        
        # Usar el directorio de snapshots por defecto
        snapshots_dir = "/media/sf_tfg_shared/cacheviewer/cache_snapshots"
        
        # Si no existe, preguntar al usuario
        if not os.path.exists(snapshots_dir):
            snapshots_dir = filedialog.askdirectory(
                title="Seleccionar carpeta con cache_snapshot_*.csv",
                initialdir="/media/sf_tfg_shared/cacheviewer/cache_snapshots"
            )
            
            if not snapshots_dir:
                return
        
        # Buscar archivos de snapshot
        try:
            files = os.listdir(snapshots_dir)
            snapshot_files = sorted([
                os.path.join(snapshots_dir, f) 
                for f in files 
                if f.startswith("cache_snapshot_") and f.endswith(".csv")
            ])
        except Exception as e:
            messagebox.showerror("Error", f"Error leyendo carpeta:\n{str(e)}")
            return
        
        if len(snapshot_files) < 2:
            messagebox.showinfo("Información", 
                            f"Se necesitan al menos 2 snapshots\n"
                            f"Encontrados: {len(snapshot_files)}\n"
                            f"Carpeta: {snapshot_files}")
            return
        
        # Calcular hits/misses primero
        all_results = self.calculate_hits_misses(snapshot_files)
        
        # Llamar a la función que muestra la ventana con gráficos
        self.show_hits_misses_charts(all_results, snapshot_files)
    
    def calculate_hits_misses(self, snapshot_files):
        """Calcula hits/misses desde los archivos de snapshot"""
        import csv
        
        results = {}
        previous_data = {}
        
        for i, file_path in enumerate(snapshot_files):
            current_data = {}
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Saltar cabecera
                    
                    current_domain = None
                    
                    for row in reader:
                        if len(row) >= 3:
                            domain = row[0].strip().rstrip('.')
                            ttl_str = row[2].strip().upper()
                            
                            if domain:
                                current_domain = domain
                                
                                if ttl_str == 'IN':
                                    ttl_val = float('inf')
                                else:
                                    try:
                                        ttl_val = int(float(ttl_str))
                                    except:
                                        ttl_val = None
                                
                                if current_domain and ttl_val is not None:
                                    current_data[current_domain] = ttl_val
            except Exception as e:
                continue

            # Para el primer snapshot (i == 0), todos los dominios son MISS
            if i == 0:
                for domain, ttl in current_data.items():
                    if domain not in results:
                        results[domain] = {'hits': 0, 'misses': 0, 'activity': []}
                    # Todos los dominios del primer snapshot son misses
                    results[domain]['misses'] += 1
                    results[domain]['activity'].append('MISS')
            
            else:
                for domain, ttl in current_data.items():
                    if domain not in results:
                        results[domain] = {'hits': 0, 'misses': 0, 'activity': []}
                    
                    if domain in previous_data:
                        prev_ttl = previous_data[domain]
                        if ttl < prev_ttl:
                            # TTL disminuyó - HIT (no se agotó el TTL anterior)
                            results[domain]['hits'] += 1
                            results[domain]['activity'].append('HIT')
                        elif ttl > prev_ttl:
                            # TTL aumentó - MISS (se agotó el TTL anterior)
                            results[domain]['misses'] += 1
                            results[domain]['activity'].append('MISS')
                        else:
                            # TTL igual - HIT (el TTL no se agotó)
                            results[domain]['hits'] += 1
                            results[domain]['activity'].append('HIT')
                    else:
                        # Dominio nuevo en este snapshot
                        results[domain]['misses'] += 1
                        results[domain]['activity'].append('MISS')
            
            previous_data = current_data
        
        return results
    
    def show_hits_misses_charts(self, all_results, snapshot_files=None):
        import pandas as pd
        import seaborn as sns
        import matplotlib.pyplot as plt
        import math
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        import csv  # Asegurarse de importar csv

        sns.set_theme(style="whitegrid")

        if not all_results:
            messagebox.showwarning("Sin datos", "No se pudieron calcular hits/misses")
            return

        # Función para obtener el TTL máximo de un dominio
        def get_max_ttl(domain, snapshot_files):
            """Obtiene el TTL máximo de un dominio de todos los snapshots donde aparece"""
            if not snapshot_files:
                return "N/A"
            
            max_ttl = None
            inf_found = False
            
            for file_path in snapshot_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader)  # Saltar cabecera
                        
                        for row in reader:
                            if len(row) >= 3:
                                current_domain = row[0].strip().rstrip('.')
                                
                                if current_domain == domain:
                                    ttl_str = row[2].strip().upper()
                                    
                                    if ttl_str == 'IN' or ttl_str == 'INF':
                                        inf_found = True
                                    else:
                                        try:
                                            ttl_val = int(float(ttl_str))
                                            if max_ttl is None or ttl_val > max_ttl:
                                                max_ttl = ttl_val
                                        except:
                                            continue
                except Exception as e:
                    continue
            
            if inf_found:
                return "INF"
            elif max_ttl is not None:
                return str(max_ttl)
            else:
                return "N/A"

        # Convertir resultados a DataFrame
        data_list = []
        for domain, stats in all_results.items():
            hits = stats['hits']
            misses = stats['misses']
            total = hits + misses
            if total > 0:
                # Obtener TTL máximo en lugar del inicial
                ttl_max = get_max_ttl(domain, snapshot_files)
                
                data_list.append({
                    'domain': domain,
                    'ttl_max': ttl_max,  # Cambiar nombre a ttl_max
                    'hits': hits,
                    'misses': misses,
                    'total': total,
                    'hit_ratio': hits / total * 100,
                    'activity': stats.get('activity', [])
                })

        df = pd.DataFrame(data_list)
        if df.empty:
            messagebox.showwarning("Sin datos", "No hay datos válidos para graficar")
            return

        # Ventana principal
        charts_window = tk.Toplevel(self.root)
        charts_window.title("Análisis de Hits/Misses por Dominio")
        charts_window.geometry("1500x950")

        main_frame = ttk.Frame(charts_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ============================================================
        # LAYOUT GENERAL
        # ============================================================
        main_frame.rowconfigure(0, weight=1)   # fila superior más pequeña
        main_frame.rowconfigure(1, weight=2)   # fila inferior más grande
        main_frame.columnconfigure(0, weight=3)   # tabla más ancha
        main_frame.columnconfigure(1, weight=2)   # donut más estrecho

        # Fila 1
        top_left = ttk.Frame(main_frame)
        top_left.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        top_right = ttk.Frame(main_frame)
        top_right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Fila 2
        bottom_left = ttk.Frame(main_frame)
        bottom_left.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        bottom_right = ttk.Frame(main_frame)
        bottom_right.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # Información de snapshots
        snapshot_info = f"Snapshots analizados: {len(snapshot_files) if snapshot_files else 0}"
        if snapshot_files and len(snapshot_files) > 0:
            snapshot_info += f" | Primero: {os.path.basename(snapshot_files[0])}"
            snapshot_info += f" | Último: {os.path.basename(snapshot_files[-1])}"
        
        info_label = ttk.Label(main_frame, text=snapshot_info, font=('Arial', 9))
        info_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # --- FILTRO DE BÚSQUEDA ---
        search_frame = ttk.Frame(top_left)
        search_frame.pack(fill=tk.X, pady=5)

        search_var = tk.StringVar()

        ttk.Label(search_frame, text="Filtrar dominio:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)

        # ============================================================
        # TABLA (arriba izquierda)
        # ============================================================
        table_frame = ttk.Frame(top_left)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Crear frame para la tabla y scrollbar
        table_container = ttk.Frame(table_frame)
        table_container.pack(fill=tk.BOTH, expand=True)

        # Cambiar nombre de columna a TTL MÁXIMO
        columns = ("domain", "ttl_max", "hits", "misses", "total", "hit_ratio")  # Cambiar ttl_initial a ttl_max
        domain_tree = ttk.Treeview(table_container, columns=columns, show="headings", height=10)

        # Diccionario para almacenar el estado de ordenación de cada columna
        sort_states = {col: {"ascending": False, "symbol": " ▼"} for col in columns}
        current_sort_column = None

        # Configurar encabezados con triángulos (actualizar texto a TTL MÁXIMO)
        domain_tree.heading("domain", text="DOMINIO")
        domain_tree.heading("ttl_max", text="TTL MÁXIMO")  # Cambiar texto
        domain_tree.heading("hits", text="HITS")
        domain_tree.heading("misses", text="MISSES")
        domain_tree.heading("total", text="TOTAL")
        domain_tree.heading("hit_ratio", text="% HIT")

        # Ajustar anchos de columna
        domain_tree.column("domain", width=180, anchor=tk.W)
        domain_tree.column("ttl_max", width=100, anchor=tk.CENTER)  # Cambiar nombre de columna
        domain_tree.column("hits", width=60, anchor=tk.CENTER)
        domain_tree.column("misses", width=60, anchor=tk.CENTER)
        domain_tree.column("total", width=60, anchor=tk.CENTER)
        domain_tree.column("hit_ratio", width=70, anchor=tk.CENTER)

        # Función para convertir valores de TTL a un formato ordenable
        def parse_ttl_value(ttl_str):
            """Convierte valores de TTL a números ordenables, manejando casos especiales"""
            if not ttl_str:
                return float('inf'), "N/A"  # Valor muy alto para ordenación
            
            ttl_str = str(ttl_str).strip().upper()
            
            # Manejamos casos especiales
            if ttl_str == "INF":
                return float('inf'), "INF"  # INFINITO (valor más alto)
            elif ttl_str == "N/A" or ttl_str == "NA" or ttl_str == "":
                return float('inf'), "N/A"  # Valor más alto después de INF
            else:
                try:
                    # Intentar convertir a número
                    ttl_num = float(ttl_str)
                    # Para ordenar numéricamente, usamos el valor numérico
                    return ttl_num, str(int(ttl_num)) if ttl_num.is_integer() else str(ttl_num)
                except ValueError:
                    # Si no es un número válido, lo tratamos como "N/A"
                    return float('inf'), "N/A"

        # Función para ordenar las columnas
        def sort_column(tree, col, descending):
            """Ordena el contenido de una columna cuando se hace clic en el encabezado"""
            # Obtener todos los elementos de la tabla
            data = [(tree.set(child, col), child) for child in tree.get_children('')]
            
            # Determinar el tipo de ordenación según la columna
            if col == "ttl_max":  # Cambiar a ttl_max
                # Para TTL, usar ordenación especial
                data = [(parse_ttl_value(item[0])[0], item[1], parse_ttl_value(item[0])[1]) 
                        for item in data]
            elif col in ["hits", "misses", "total", "hit_ratio"]:
                # Para columnas numéricas, convertir a float
                data = [(float(item[0]) if item[0] and item[0].replace('.', '').replace('-', '').isdigit() else 0, item[1]) 
                        for item in data]
            else:
                # Para columnas de texto, usar minúsculas para ordenación case-insensitive
                data = [(item[0].lower() if item[0] else "", item[1]) for item in data]
            
            # Ordenar los datos
            data.sort(reverse=descending)
            
            # Reordenar los elementos en el Treeview
            for index, (val, child, *_) in enumerate(data):
                tree.move(child, '', index)
            
            # Alternar dirección para el próximo clic
            return not descending

        # Función para manejar el clic en el encabezado
        def on_header_click(event):
            """Maneja el clic en los encabezados de columna"""
            region = domain_tree.identify("region", event.x, event.y)
            
            if region == "heading":
                # Obtener la columna clickeada
                column = domain_tree.identify_column(event.x)
                col_index = int(column.replace('#', '')) - 1
                
                if col_index < len(columns):
                    col_name = columns[col_index]
                    
                    # Actualizar estado de ordenación
                    is_descending = sort_states[col_name]["ascending"]
                    new_descending = not is_descending
                    
                    # Ordenar la columna
                    sort_column(domain_tree, col_name, new_descending)
                    
                    # Actualizar símbolos en todos los encabezados
                    for col in columns:
                        if col == col_name:
                            # Actualizar símbolo de la columna actual
                            sort_states[col]["ascending"] = new_descending
                            symbol = " ▲" if new_descending else " ▼"
                            sort_states[col]["symbol"] = symbol
                        else:
                            # Quitar símbolo de otras columnas
                            sort_states[col]["symbol"] = ""
                    
                    # Actualizar texto de los encabezados
                    domain_tree.heading("domain", text="DOMINIO" + sort_states["domain"]["symbol"])
                    domain_tree.heading("ttl_max", text="TTL MÁXIMO" + sort_states["ttl_max"]["symbol"])  # Cambiar a ttl_max
                    domain_tree.heading("hits", text="HITS" + sort_states["hits"]["symbol"])
                    domain_tree.heading("misses", text="MISSES" + sort_states["misses"]["symbol"])
                    domain_tree.heading("total", text="TOTAL" + sort_states["total"]["symbol"])
                    domain_tree.heading("hit_ratio", text="% HIT" + sort_states["hit_ratio"]["symbol"])

        # Vincular evento de clic a los encabezados
        domain_tree.bind("<Button-1>", on_header_click)

        # Añadir scrollbar vertical
        v_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=domain_tree.yview)
        domain_tree.configure(yscrollcommand=v_scrollbar.set)

        # Colocar tabla y scrollbar usando grid
        domain_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        # Configurar grid weights para que la tabla se expanda
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Crear un diccionario con los TTL máximos para optimizar
        max_ttl_cache = {}
        for domain in df["domain"].unique():
            max_ttl_cache[domain] = get_max_ttl(domain, snapshot_files)

        # Asegurarse de que la columna ttl_max existe en el DataFrame
        # (ya debería existir desde la creación inicial, pero por si acaso)
        if "ttl_max" not in df.columns:
            df["ttl_max"] = df["domain"].map(max_ttl_cache)

        def update_tree(*args):
            """Actualiza el contenido del Treeview con los datos filtrados"""
            domain_tree.delete(*domain_tree.get_children())
            
            text = search_var.get().lower().strip()
            
            if text:
                filtered = df[df["domain"].str.lower().str.contains(text)]
            else:
                filtered = df
            
            # Insertar datos en el Treeview
            for _, row in filtered.iterrows():
                domain_tree.insert("", tk.END, values=(
                    row["domain"], 
                    row["ttl_max"],  # Cambiar a ttl_max
                    row["hits"], 
                    row["misses"], 
                    row["total"], 
                    f"{row['hit_ratio']:.1f}"
                ))
            
            # Reiniciar estados de ordenación después de actualizar
            for col in columns:
                sort_states[col]["ascending"] = False
                sort_states[col]["symbol"] = ""
            
            # Actualizar encabezados sin símbolos
            domain_tree.heading("domain", text="DOMINIO")
            domain_tree.heading("ttl_max", text="TTL MÁXIMO")  # Cambiar texto
            domain_tree.heading("hits", text="HITS")
            domain_tree.heading("misses", text="MISSES")
            domain_tree.heading("total", text="TOTAL")
            domain_tree.heading("hit_ratio", text="% HIT")

        search_var.trace_add("write", update_tree)

        update_tree()


        # ============================================================
        # DONUT (arriba derecha) con botón para ver evolución del TTL
        # ============================================================
        donut_frame = ttk.Frame(top_right)
        donut_frame.pack(fill=tk.BOTH, expand=True)

        # Frame para el botón sobre el donut
        donut_button_frame = ttk.Frame(donut_frame)
        donut_button_frame.pack(fill=tk.X, pady=5)

        # Variable para almacenar el dominio actualmente mostrado en el donut
        current_domain_in_donut = None

        def draw_donut(domain, row):
            nonlocal current_domain_in_donut
            
            # Guardar el dominio actual
            current_domain_in_donut = domain
            
            # Limpiar frame del donut
            for w in donut_frame.winfo_children():
                w.destroy()
            
            # Frame para el botón
            button_frame = ttk.Frame(donut_frame)
            button_frame.pack(fill=tk.X, pady=5)
            
            # Botón para ver evolución del TTL
            ttk.Button(button_frame, text="Ver evolución del TTL", 
                      command=lambda: self.see_ttl_evolution_from_donut(domain, snapshot_files)).pack()
            
            # Frame para el gráfico donut
            chart_frame = ttk.Frame(donut_frame)
            chart_frame.pack(fill=tk.BOTH, expand=True)

            fig, ax = plt.subplots(figsize=(5, 4))

            labels = ["HITS", "MISSES"]
            sizes = [row["hits"], row["misses"]]
            colors = ["#2ecc71", "#e74c3c"]
            text_colors = ["#27ae60", "#c0392b"]  # Verde más oscuro y rojo más oscuro para texto

            wedges, _ = ax.pie(
                sizes,
                labels=None,
                startangle=90,
                colors=colors,
                wedgeprops={"linewidth": 1, "edgecolor": "white"}
            )

            centre_circle = plt.Circle((0, 0), 0.60, fc="white")
            ax.add_artist(centre_circle)

            total = sum(sizes)
            
            # Calcular y mostrar los porcentajes fuera del donut
            for i, wedge in enumerate(wedges):
                # Calcular porcentaje
                percentage = sizes[i] / total * 100
                pct_text = f"{percentage:.1f}%"
                
                # Calcular la posición para el texto fuera del donut
                ang = (wedge.theta2 + wedge.theta1) / 2
                # Multiplicar por 1.2 para ponerlo fuera del círculo (no demasiado lejos)
                x = 1.2 * math.cos(math.radians(ang))
                y = 1.2 * math.sin(math.radians(ang))
                
                # Asignar color según el tipo (verde para hits, rojo para misses)
                text_color = text_colors[i]
                
                # Añadir el texto con el color correspondiente
                ax.text(x, y, pct_text, ha="center", va="center",
                        fontsize=12, fontweight="bold", color=text_color)

            # Crear rectángulo negro con el nombre del dominio arriba a la izquierda
            domain_text = f"  {domain}  "

            # Añadir el texto del dominio en un rectángulo negro - arriba y a la izquierda del gráfico
            ax.text(-0.10, 1.00, domain_text, ha="left", va="bottom",
                    transform=ax.transAxes,
                    fontsize=13, fontweight="bold",
                    color="white",
                    bbox=dict(boxstyle="round,pad=0.5",
                            facecolor="black",
                            edgecolor="black",
                            linewidth=2,
                            alpha=0.9))

            # Crear leyenda personalizada
            handles = [
                plt.Line2D([0], [0], marker='o', color='w', label='HITS',
                          markerfacecolor="#2ecc71", markersize=12),
                plt.Line2D([0], [0], marker='o', color='w', label='MISSES',
                          markerfacecolor="#e74c3c", markersize=12)
            ]
            ax.legend(handles=handles, loc="upper right", frameon=True, fontsize=10)

            # Quitar el título original
            ax.set_title("")
            ax.axis("equal")

            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============================================================
        # HISTOGRAMA (abajo izquierda)
        # ============================================================
        hist_frame = ttk.Frame(bottom_left)
        hist_frame.pack(fill=tk.BOTH, expand=True)

        fig_hist, ax_hist = plt.subplots(figsize=(6, 4))
        sns.histplot(df["hit_ratio"], bins=20, kde=False, ax=ax_hist, color="#2ecc71")
        ax_hist.set_title("Distribución % HIT")

        canvas_hist = FigureCanvasTkAgg(fig_hist, hist_frame)
        canvas_hist.draw()
        canvas_hist.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ============================================================
        # ESTADÍSTICAS (abajo derecha)
        # ============================================================
        stats_frame = ttk.LabelFrame(bottom_right, text="Estadísticas Globales", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True)

        total_hits = df['hits'].sum()
        total_misses = df['misses'].sum()
        total_events = total_hits + total_misses
        overall_hit_rate = (total_hits / total_events * 100) if total_events > 0 else 0

        stats_text = f"""
    • Dominios analizados: {len(df):,}
    • Total HITS: {total_hits:,}
    • Total MISSES: {total_misses:,}
    • Total eventos: {total_events:,}
    • Tasa de Hit global: {overall_hit_rate:.1f}%
    """

        for line in stats_text.strip().split("\n"):
            ttk.Label(stats_frame, text=line, font=('Courier', 10)).pack(anchor="w")

        ttk.Label(stats_frame, text="\nDistribución por rangos de % HIT:", font=('Courier', 10, 'bold')).pack(anchor="w")

        bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        labels = ['0-10%', '11-20%', '21-30%', '31-40%', '41-50%','51-60%', '61-70%', '71-80%', '81-90%', '91-100%']

        df['hit_range'] = pd.cut(df['hit_ratio'], bins=bins, labels=labels, include_lowest=True)
        range_counts = df['hit_range'].value_counts().sort_index()

        for label, count in range_counts.items():
            pct = (count / len(df)) * 100
            ttk.Label(stats_frame, text=f"  {label}: {count} dominios ({pct:.1f}%)",
                    font=('Courier', 9)).pack(anchor="w")

        button_frame = ttk.Frame(stats_frame)
        button_frame.pack(pady=10)

        # Solo un botón de exportar a CSV (eliminé el de exportar gráfico)
        def export_data():
            export_file = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile="hits_misses_analysis.csv"
            )
            if export_file:
                df.to_csv(export_file, index=False, encoding='utf-8')
                messagebox.showinfo("Éxito", f"Datos exportados a:\n{export_file}")

        def refresh_snapshots():
            charts_window.destroy()
            self.show_hits_misses_per_domain_gui()

        ttk.Button(button_frame, text="Exportar a CSV", command=export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refrescar Snapshots", command=refresh_snapshots).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cerrar", command=charts_window.destroy).pack(side=tk.LEFT, padx=5)

        # ============================================================
        # EVENTO: ACTUALIZAR DONUT AL SELECCIONAR DOMINIO
        # ============================================================
        def show_domain_detail(event=None):
            selected = domain_tree.selection()
            if not selected:
                return
            domain = domain_tree.item(selected[0])["values"][0]
            row = df[df["domain"] == domain].iloc[0]
            draw_donut(domain, row)

        domain_tree.bind("<<TreeviewSelect>>", show_domain_detail)

        # Mostrar el primer dominio por defecto
        if len(df) > 0:
            first_domain = df.iloc[0]["domain"]
            first_row = df.iloc[0]
            draw_donut(first_domain, first_row)
            
            # Seleccionar el primer elemento en el treeview
            domain_tree.selection_set(domain_tree.get_children()[0])
    
    def see_ttl_evolution_from_donut(self, domain, snapshot_files):
        """Muestra la evolución del TTL para el dominio desde el donut"""
        if not snapshot_files:
            messagebox.showwarning("Sin snapshots", "No hay archivos de snapshot disponibles")
            return
        
        # Obtener todos los TTL del dominio a lo largo del tiempo
        ttl_data = self.get_ttl_evolution_for_domain(domain, snapshot_files)
        
        # Filtrar solo los valores válidos (no "N/A")
        valid_ttl_data = [(timestamp, ttl, snapshot) for timestamp, ttl, snapshot in ttl_data if ttl != "N/A"]
        
        if not valid_ttl_data:
            messagebox.showwarning("Sin datos", f"No se encontraron datos de TTL válidos para el dominio: {domain}")
            return
        
        # Extraer solo valores de TTL
        ttl_values = [ttl for _, ttl, _ in valid_ttl_data]
        
        # Calcular estados según la lógica: MISS si es el primero o si ttl_i > ttl_{i+1}
        # HIT si ttl_i < ttl_{i+1} (TTL disminuyó - no se agotó)
        estados = []
        for i in range(len(ttl_values)):
            if i == 0:
                # El primero siempre es MISS
                estados.append("MISS")
            else:
                # Comparar con el anterior
                if ttl_values[i] < ttl_values[i-1]:
                    # TTL disminuyó - HIT (el TTL anterior no se había agotado completamente)
                    estados.append("HIT")
                elif ttl_values[i] > ttl_values[i-1]:
                    # TTL aumentó - MISS (se agotó el TTL anterior)
                    estados.append("MISS")
                else:
                    # TTL igual - consideramos como HIT (el TTL no se agotó)
                    estados.append("HIT")
        
        # Crear ventana para mostrar la evolución del TTL
        ttl_window = tk.Toplevel(self.root)
        ttl_window.title(f"Evolución del TTL: {domain}")
        ttl_window.geometry("1200x400")  # Reducir altura
        
        # Frame principal
        main_frame = ttk.Frame(ttl_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, 
                               text=f"Evolución del TTL para: {domain}", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Canvas para scroll horizontal directamente en main_frame
        canvas = tk.Canvas(main_frame, height=120, bg='#dcdad5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        
        # Frame dentro del canvas
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar.set)
        
        # Empaquetar
        canvas.pack(fill=tk.X, expand=False, pady=(0, 5))
        scrollbar.pack(fill=tk.X, pady=(0, 10))
        
        # Frame para la tabla dentro del frame scrollable
        table_frame = ttk.Frame(scrollable_frame)
        table_frame.pack(pady=5)
        
        # Encabezado de tiempos (filas diferentes para tiempo y estado)
        ttk.Label(table_frame, text="Tiempo (s):", font=('Arial', 9, 'bold'), 
                 width=15).grid(row=1, column=0, padx=5, pady=2, sticky='w')
        
        # Fila para tiempos en segundos
        for i in range(len(ttl_values)):
            tiempo_segundos = i * 1  # Suponiendo 1 segundo entre snapshots
            time_label = ttk.Label(table_frame, text=f"{tiempo_segundos}", 
                                 font=('Arial', 9, 'bold'), width=8, anchor='center')
            time_label.grid(row=1, column=i+1, padx=2, pady=2)
        
        # Fila de TTL con colores
        ttk.Label(table_frame, text="TTL:", font=('Arial', 9, 'bold'), 
                 width=15).grid(row=2, column=0, padx=5, pady=2, sticky='w')
        
        # Crear celdas de TTL con colores
        for i in range(len(ttl_values)):
            # Crear frame para la celda
            cell_frame = tk.Frame(table_frame, relief='ridge', borderwidth=1)
            cell_frame.grid(row=2, column=i+1, padx=2, pady=2)
            
            # Crear label dentro del frame
            cell_label = tk.Label(cell_frame, text=str(ttl_values[i]), 
                                font=('Arial', 10, 'bold'), width=8, height=2)
            cell_label.pack(expand=True, fill='both')
            
            # Colorear según estado
            if estados[i] == "MISS":
                cell_label.config(bg='#ffcccc', fg='black')  # Rojo claro para MISS
            elif estados[i] == "HIT":
                cell_label.config(bg='#ccffcc', fg='black')  # Verde claro para HIT
        
        # Leyenda de colores
        legend_frame = ttk.Frame(main_frame)
        legend_frame.pack(pady=10)
        
        # Crear muestras de color
        miss_sample = tk.Label(legend_frame, text="   ", bg='#ffcccc', 
                              relief='ridge', borderwidth=1, width=3)
        miss_sample.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(legend_frame, text="MISS").pack(side=tk.LEFT, padx=(0, 20))
        
        hit_sample = tk.Label(legend_frame, text="   ", bg='#ccffcc', 
                             relief='ridge', borderwidth=1, width=3)
        hit_sample.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(legend_frame, text="HIT").pack(side=tk.LEFT)
        
        # Estadísticas
        stats_frame = ttk.LabelFrame(main_frame, text="Estadísticas de TTL", padding="10")
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Calcular estadísticas
        hits_count = estados.count("HIT")
        misses_count = estados.count("MISS")
        total_snapshots = len(ttl_values)
        
        # Calcular cambios en TTL
        cambios_ttl = [ttl_values[i] - ttl_values[i-1] for i in range(1, len(ttl_values))]
        
        stats_text = f"""
        • Total snapshots: {total_snapshots}
        • HITS: {hits_count} ({hits_count/total_snapshots*100:.1f}%)
        • MISSES: {misses_count} ({misses_count/total_snapshots*100:.1f}%)
        • TTL mínimo: {min(ttl_values)} segundos
        • TTL máximo: {max(ttl_values)} segundos
        • TTL promedio: {sum(ttl_values)/len(ttl_values):.1f} segundos
        • TTL inicial: {ttl_values[0]} segundos
        • TTL final: {ttl_values[-1]} segundos
        """
        
        # Mostrar estadísticas en dos columnas
        stats_lines = stats_text.strip().split("\n")
        half = len(stats_lines) // 2
        
        left_frame = ttk.Frame(stats_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        for line in stats_lines[:half]:
            ttk.Label(left_frame, text=line.strip(), 
                     font=('Courier', 9)).pack(anchor="w")
        
        right_frame = ttk.Frame(stats_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        for line in stats_lines[half:]:
            ttk.Label(right_frame, text=line.strip(), 
                     font=('Courier', 9)).pack(anchor="w")
        
        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # Preparar datos para exportar
        ttl_for_export = []
        for i, ttl in enumerate(ttl_values):
            tiempo = i * 1  # Tiempo en segundos
            ttl_for_export.append((f"T{tiempo}s", ttl, estados[i]))
                
        # Configurar el canvas para que se adapte al contenido
        table_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
    
    def get_ttl_evolution_for_domain(self, domain, snapshot_files):
        """Obtiene la evolución del TTL para un dominio específico"""
        ttl_data = []
        
        for i, file_path in enumerate(snapshot_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Saltar cabecera
                    
                    found = False
                    current_ttl = None
                    
                    for row in reader:
                        if len(row) >= 3:
                            current_domain = row[0].strip().rstrip('.')
                            
                            if current_domain == domain:
                                ttl_str = row[2].strip().upper()
                                
                                if ttl_str == 'IN':
                                    current_ttl = float('inf')
                                else:
                                    try:
                                        current_ttl = int(float(ttl_str))
                                    except:
                                        current_ttl = None
                                
                                if current_ttl is not None:
                                    snapshot_name = os.path.basename(file_path)
                                    ttl_data.append((f"Snapshot {i+1}", current_ttl, snapshot_name))
                                    found = True
                                    break
                    
                    if not found:
                        # Dominio no encontrado en este snapshot
                        snapshot_name = os.path.basename(file_path)
                        ttl_data.append((f"Snapshot {i+1}", "N/A", snapshot_name))
                        
            except Exception as e:
                continue
        
        return ttl_data
