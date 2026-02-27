# visor_dns/viewer/cache_view.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import os

class CacheView:
    """Mixin para visualización de caché DNS"""
    
    def load_cache_files(self):
        """Carga archivos de volcado de caché en formato CSV"""
        files = filedialog.askopenfilenames(title="Seleccionar archivos named_dump (CSV)",
                                        filetypes=[("CSV files", "*.csv")])
        
        if files:
            self.cache_files = list(files)
            self.cache_label.config(text=f"cache_real.csv - {len(self.cache_files)} archivos", 
                                font=('Arial', 9, 'bold'))
            self.cache_status_indicator.config(foreground="#27ae60", text="✓")
            messagebox.showinfo("Éxito", f"Se cargaron {len(self.cache_files)} archivos de caché")
    
    def show_cache_content(self):
        """Muestra el contenido de la caché DNS desde archivos CSV"""
        if not self.cache_files:
            messagebox.showwarning("Advertencia", 
                                "Primero debes cargar archivos de caché CSV\n"
                                "Usa el botón 'Cargar archivo cache_real.csv' en la sección de carga de archivos")
            return

        # Selección de archivo si hay varios
        if len(self.cache_files) > 1:
            selected_file = self.ask_select_cache_file()
            if not selected_file:
                return
        else:
            selected_file = self.cache_files[0]

        try:
            # Leer CSV inicial
            df = pd.read_csv(selected_file)

            # ==== FILTRAR ENTRADAS INVÁLIDAS ====
            # Mantener solo filas donde TTL sea un número entero
            df = df[pd.to_numeric(df['TTLs'], errors='coerce').notnull()]

            # Columnas esperadas
            required_columns = ['Domain', 'IP_Addresses', 'TTLs']
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror(
                    "Error",
                    f"El archivo {os.path.basename(selected_file)} no tiene el formato esperado.\n"
                    f"Se esperaban las columnas: {required_columns}"
                )
                return

            # Procesar datos
            cache_entries = self.process_cache_data(df)
            if not cache_entries:
                messagebox.showinfo("Información", "No se encontraron entradas válidas en el archivo de caché")
                return

            # Crear ventana de caché
            cache_window = tk.Toplevel(self.root)
            cache_window.title(f"Contenido de Caché - {os.path.basename(selected_file)}")
            cache_window.geometry("1000x600")

            main_frame = ttk.Frame(cache_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            info_text = f"Archivo: {os.path.basename(selected_file)} - Entradas únicas: {len(cache_entries)}"
            ttk.Label(main_frame, text=info_text, font=('Arial', 10, 'bold')).pack(pady=10)

            # Frame de filtro y botones
            filter_frame = ttk.Frame(main_frame)
            filter_frame.pack(fill=tk.X, pady=5)

            ttk.Label(filter_frame, text="Filtrar por dominio:", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 10))
            filter_var = tk.StringVar()
            filter_entry = ttk.Entry(filter_frame, textvariable=filter_var, width=30)
            filter_entry.pack(side=tk.LEFT, padx=(0, 10))

            # Treeview
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            tree = ttk.Treeview(tree_frame, columns=('Dominio', 'IPs', 'TTL'), show='headings')
            tree.heading('Dominio', text='Dominio')
            tree.heading('IPs', text='Direcciones IP')
            tree.heading('TTL', text='TTL (segundos)')
            tree.column('Dominio', width=250)
            tree.column('IPs', width=300)
            tree.column('TTL', width=100)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=v_scroll.set)
            v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            stats_label = ttk.Label(main_frame, text=f"Mostrando {len(cache_entries)} de {len(cache_entries)} entradas", font=('Arial', 9))
            stats_label.pack(pady=5)

            # ==== Funciones internas ====
            def populate_tree(entries):
                for item in tree.get_children():
                    tree.delete(item)
                filter_text = filter_var.get().lower().strip()
                shown = 0
                for entry in entries:
                    if not filter_text or filter_text in entry['domain'].lower():
                        ips_str = ", ".join(entry['ips']) if isinstance(entry['ips'], list) else str(entry['ips'])
                        tree.insert('', tk.END, values=(entry['domain'], ips_str, entry['ttl']))
                        shown += 1
                stats_label.config(text=f"Mostrando {shown} de {len(entries)} entradas")

            def apply_filter():
                populate_tree(cache_entries)

            def clear_filter():
                filter_var.set("")
                apply_filter()

            def refresh_cache():
                try:
                    df_new = pd.read_csv(selected_file)
                    new_entries = self.process_cache_data(df_new)
                    cache_entries.clear()
                    cache_entries.extend(new_entries)
                    populate_tree(cache_entries)
                except Exception as ex:
                    messagebox.showerror("Error", f"No se pudo refrescar la caché:\n{ex}")

            # ==== Botones ====
            ttk.Button(filter_frame, text="Filtrar", command=apply_filter).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(filter_frame, text="Limpiar", command=clear_filter).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(filter_frame, text="Refresh TTL", command=refresh_cache).pack(side=tk.LEFT)

            filter_entry.bind('<Return>', lambda e: apply_filter())

            # Carga inicial de datos
            populate_tree(cache_entries)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo de caché: {str(e)}")
    
    def process_cache_data(self, df):
        """Procesa los datos del CSV de caché para agrupar por dominio"""
        entries = []
        current_domain = None
        current_ips = []
        current_ttl = None
        
        for _, row in df.iterrows():
            domain = row['Domain']
            ip = row['IP_Addresses']
            ttl = row['TTLs']
            
            # Si el dominio no está vacío, es un nuevo dominio
            if pd.notna(domain) and domain != '':
                # Guardar el dominio anterior si existe
                if current_domain is not None:
                    entries.append({
                        'domain': current_domain,
                        'ips': current_ips.copy(),
                        'ttl': current_ttl
                    })
                
                # Comenzar nuevo dominio
                current_domain = domain
                current_ips = [ip] if pd.notna(ip) else []
                current_ttl = ttl
            else:
                # Es una IP adicional para el dominio actual
                if pd.notna(ip):
                    current_ips.append(ip)
        
        # Añadir el último dominio
        if current_domain is not None:
            entries.append({
                'domain': current_domain,
                'ips': current_ips,
                'ttl': current_ttl
            })
        
        return entries
    
    def ask_select_cache_file(self):
        """Pide al usuario que seleccione un archivo de caché cuando hay múltiples"""
        win = tk.Toplevel(self.root)
        win.title("Seleccionar archivo de caché")
        win.geometry("400x300")
        
        ttk.Label(win, text="Selecciona un archivo de caché:", font=('Arial', 11)).pack(pady=10)
        
        listbox = tk.Listbox(win)
        for file in self.cache_files:
            listbox.insert(tk.END, os.path.basename(file))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        selected_file = [None]
        
        def confirm():
            selection = listbox.curselection()
            if selection:
                selected_file[0] = self.cache_files[selection[0]]
                win.destroy()
            else:
                messagebox.showwarning("Advertencia", "Selecciona un archivo")
        
        ttk.Button(win, text="Seleccionar", command=confirm).pack(pady=10)
        
        win.wait_window()
        return selected_file[0]             