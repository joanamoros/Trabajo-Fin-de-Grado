#!/usr/bin/env python3
# ============================================================================
# dnsperf_gui.py - Interfaz gráfica simplificada para DNSperf
# ============================================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import subprocess
import threading
import os
import sys
import json  # Para guardar IPs permanentemente
import time

class DNSperfGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Herramienta DNSperf")
        self.root.geometry("900x750")
        
        # Variables para los parámetros
        self.ip_servidor = tk.StringVar()
        self.archivo_consultas = tk.StringVar()
        
        # Variables para segmentos
        self.num_segmentos = tk.StringVar(value="1")
        self.duraciones_segmentos = []  # Lista de duraciones
        self.qps_segmentos = []  # Lista de valores QPS por segmento
        
        # Configuración SSH para MV
        self.mv_host = "192.168.1.149"  # casa
        # self.mv_host = "10.1.44.11"    # uni
        self.mv_usuario = "vboxuser"
        self.mv_ruta_script = "/root/real_time_export.sh"
        
        # Estado del proceso
        self.proceso_dnsperf = None
        self.proceso_export_mv = None
        self.en_ejecucion = False
        self.export_mv_en_ejecucion = False
        
        # Cargar IPs guardadas permanentemente
        self.ips_conocidas = self.cargar_ips_guardadas()
        
        self.configurar_interfaz()
    
    def cargar_ips_guardadas(self):
        """Carga las IPs guardadas permanentemente desde archivo"""
        try:
            if os.path.exists("ips_guardadas.json"):
                with open("ips_guardadas.json", "r") as f:
                    ips = json.load(f)
                    # Asegurar que las IPs por defecto están incluidas
                    ips_por_defecto = ["127.0.0.1", "192.168.1.155", "10.1.44.14"]
                    for ip in ips_por_defecto:
                        if ip not in ips:
                            ips.append(ip)
                    return ips
        except:
            pass
        # Si no existe el archivo, usar valores por defecto
        return ["127.0.0.1", "192.168.1.155", "10.1.44.14"]
    
    def guardar_ips(self):
        """Guarda las IPs permanentemente en archivo"""
        try:
            with open("ips_guardadas.json", "w") as f:
                json.dump(self.ips_conocidas, f)
        except Exception as e:
            print(f"Error guardando IPs: {e}")
    
    def configurar_interfaz(self):
        """Configura toda la interfaz gráfica simplificada"""
        # Frame principal con notebook (pestañas)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña 1: Configuración Principal
        marco_principal = ttk.Frame(notebook)
        notebook.add(marco_principal, text="Configuración Principal")
        self.configurar_pestana_principal(marco_principal)
        
        # Pestaña 2: Salida de Consola
        marco_consola = ttk.Frame(notebook)
        notebook.add(marco_consola, text="Salida de Consola")
        self.configurar_pestana_consola(marco_consola)
        
        # Barra de estado
        self.barra_estado = ttk.Label(self.root, text="Listo", relief=tk.SUNKEN, anchor=tk.W)
        self.barra_estado.pack(side=tk.BOTTOM, fill=tk.X)
    
    def configurar_pestana_principal(self, padre):
        """Configura la pestaña principal simplificada"""
        marco_principal = ttk.Frame(padre, padding="20")
        marco_principal.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = ttk.Label(marco_principal, text="Configuración DNSperf", font=('Arial', 16, 'bold'))
        titulo.pack(pady=(0, 20))
        
        # Frame para IP del servidor
        marco_servidor = ttk.LabelFrame(marco_principal, text="Servidor DNS", padding="15")
        marco_servidor.pack(fill=tk.X, pady=10)
        
        ttk.Label(marco_servidor, text="IP del servidor:", font=('Arial', 10)).grid(row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        
        # Combo box para IPs conocidas
        combo_ip = ttk.Combobox(marco_servidor, textvariable=self.ip_servidor, values=self.ips_conocidas, width=25, state="normal")
        combo_ip.grid(row=0, column=1, pady=5, sticky="w")
        
        ttk.Button(marco_servidor, text="+ Añadir IP", command=self.anadir_nueva_ip, width=10).grid(row=0, column=2, padx=10)
        
        # Frame para archivo de consultas
        marco_archivo = ttk.LabelFrame(marco_principal, text="Archivo de consultas", padding="15")
        marco_archivo.pack(fill=tk.X, pady=10)
        
        ttk.Label(marco_archivo, text="Archivo de consultas:", font=('Arial', 10)).grid(row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        
        marco_entrada = ttk.Frame(marco_archivo)
        marco_entrada.grid(row=0, column=1, columnspan=2, sticky="w", pady=5)
        
        ttk.Entry(marco_entrada, textvariable=self.archivo_consultas, width=40).pack(side=tk.LEFT)
        ttk.Button(marco_entrada, text="Examinar", command=self.examinar_archivo_consultas, width=10).pack(side=tk.LEFT, padx=5)
        
        # Información del archivo
        self.etiqueta_info_archivo = ttk.Label(marco_archivo, text="Ningún archivo seleccionado", font=('Arial', 9), foreground='gray')
        self.etiqueta_info_archivo.grid(row=1, column=1, columnspan=2, sticky="w", pady=(5, 0))
        
        # Frame para configuración de segmentos
        marco_segmentos = ttk.LabelFrame(marco_principal, text="Configuración de segmentos", padding="15")
        marco_segmentos.pack(fill=tk.X, pady=10)
        
        # Número de segmentos
        ttk.Label(marco_segmentos, text="Número de segmentos:", font=('Arial', 10)).grid(row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        
        self.spinbox_segmentos = ttk.Spinbox(marco_segmentos, textvariable=self.num_segmentos, from_=1, to=10, width=5, command=self.actualizar_campos_segmentos)
        self.spinbox_segmentos.grid(row=0, column=1, sticky="w", pady=5)
        
        ttk.Button(marco_segmentos, text="Configurar segmentos", command=self.configurar_segmentos, width=20).grid(row=0, column=2, padx=(20, 0))
        
        # Frame para información de segmentos
        self.marco_info_segmentos = ttk.LabelFrame(marco_segmentos, text="Segmentos configurados", padding="10")
        self.marco_info_segmentos.grid(row=1, column=0, columnspan=3, sticky="we", pady=(10, 0))
        
        self.etiqueta_info_segmentos = ttk.Label(self.marco_info_segmentos, text="1 segmento: 30s con QPS=100", font=('Arial', 9))
        self.etiqueta_info_segmentos.pack()
        
        # Frame para botones de acción
        marco_botones = ttk.Frame(marco_principal)
        marco_botones.pack(pady=30)
        
        ttk.Button(marco_botones, text="Iniciar DNSperf", command=self.iniciar_dnsperf, width=20, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(marco_botones, text="Detener DNSperf", command=self.detener_dnsperf, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(marco_botones, text="Ver comando", command=self.mostrar_comando, width=20).pack(side=tk.LEFT, padx=5)
        
        # Configurar estilo para botón principal
        estilo = ttk.Style()
        estilo.configure("Accent.TButton", font=('Arial', 10, 'bold'))


    def configurar_segmentos(self):
        """Abre ventana para configurar segmentos individualmente"""
        num_segmentos = int(self.num_segmentos.get())
        
        # Inicializar listas si están vacías
        if len(self.duraciones_segmentos) != num_segmentos:
            self.duraciones_segmentos = ["30"] * num_segmentos
            self.qps_segmentos = ["100"] * num_segmentos
        
        # Crear ventana de configuración
        ventana_segmentos = tk.Toplevel(self.root)
        ventana_segmentos.title(f"Configurar {num_segmentos} Segmentos")
        ventana_segmentos.geometry("550x450")
        ventana_segmentos.resizable(False, False)
        
        # Frame principal
        marco_principal = ttk.Frame(ventana_segmentos, padding="20")
        marco_principal.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(marco_principal, text=f"Configuración de {num_segmentos} Segmentos", font=('Arial', 12, 'bold')).pack(pady=(0, 20))
        
        # Frame con scroll
        marco_contenedor = ttk.Frame(marco_principal)
        marco_contenedor.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(marco_contenedor, highlightthickness=0)
        scrollbar = ttk.Scrollbar(marco_contenedor, orient="vertical", command=canvas.yview)
        marco_desplazable = ttk.Frame(canvas)
        
        marco_desplazable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=marco_desplazable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Campos para cada segmento
        self.entradas_duracion = []
        self.entradas_qps = []
        
        for i in range(num_segmentos):
            marco_segmento = ttk.LabelFrame(marco_desplazable, text=f"Segmento {i+1}", padding="10")
            marco_segmento.pack(fill=tk.X, pady=5, padx=5)
            
            # Duración
            ttk.Label(marco_segmento, text="Duración (s):").grid(row=0, column=0, padx=(0, 5))
            duracion_var = tk.StringVar(value=self.duraciones_segmentos[i])
            entrada_duracion = ttk.Spinbox(marco_segmento, textvariable=duracion_var, from_=1, to=600, width=10)
            entrada_duracion.grid(row=0, column=1, padx=(0, 20))
            self.entradas_duracion.append(duracion_var)
            
            # QPS
            ttk.Label(marco_segmento, text="QPS:").grid(row=0, column=2, padx=(20, 5))
            qps_var = tk.StringVar(value=self.qps_segmentos[i])
            entrada_qps = ttk.Spinbox(marco_segmento, textvariable=qps_var, from_=1, to=10000, width=10)
            entrada_qps.grid(row=0, column=3)
            self.entradas_qps.append(qps_var)
        
        # Botones
        marco_botones = ttk.Frame(marco_principal)
        marco_botones.pack(pady=20)
        
        ttk.Button(marco_botones, text="Guardar", command=lambda: self.guardar_config_segmentos(ventana_segmentos)).pack(side=tk.LEFT, padx=5)
        ttk.Button(marco_botones, text="Cancelar", command=ventana_segmentos.destroy).pack(side=tk.LEFT, padx=5)
        
        # Configurar scroll
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def guardar_config_segmentos(self, ventana):
        """Guarda la configuración de segmentos"""
        num_segmentos = int(self.num_segmentos.get())
        self.duraciones_segmentos = []
        self.qps_segmentos = []
        
        for i in range(num_segmentos):
            self.duraciones_segmentos.append(self.entradas_duracion[i].get())
            self.qps_segmentos.append(self.entradas_qps[i].get())
        
        # Actualizar información en la interfaz principal
        info_text = ""
        for i in range(num_segmentos):
            info_text += f"S{i+1}: {self.duraciones_segmentos[i]}s (QPS={self.qps_segmentos[i]}) "
            if i < num_segmentos - 1:
                info_text += "| "
        
        self.etiqueta_info_segmentos.config(text=info_text[:80] + "..." if len(info_text) > 80 else info_text)
        
        ventana.destroy()
        self.actualizar_estado(f"Configurados {num_segmentos} segmentos")
    
    def actualizar_campos_segmentos(self):
        """Actualiza los campos cuando cambia el número de segmentos"""
        # Reiniciar configuración cuando cambia el número de segmentos
        self.duraciones_segmentos = []
        self.qps_segmentos = []
        self.etiqueta_info_segmentos.config(text=f"{self.num_segmentos.get()} segmentos sin configurar")
    
    def configurar_pestana_consola(self, padre):
        """Configura la pestaña de salida de consola"""
        marco_principal = ttk.Frame(padre, padding="10")
        marco_principal.pack(fill=tk.BOTH, expand=True)
        
        # Área de texto para salida
        self.texto_consola = scrolledtext.ScrolledText(
            marco_principal, 
            wrap=tk.WORD,
            bg='black',
            fg='white',
            font=('Courier', 10),
            height=20
        )
        self.texto_consola.pack(fill=tk.BOTH, expand=True)
        
        # Botones para la consola
        marco_botones = ttk.Frame(marco_principal)
        marco_botones.pack(pady=10)
        
        ttk.Button(marco_botones, text="Limpiar Consola", command=self.limpiar_consola).pack(side=tk.LEFT, padx=5)
        ttk.Button(marco_botones, text="Guardar Salida", command=self.guardar_salida).pack(side=tk.LEFT, padx=5)
    
    def anadir_nueva_ip(self):
        """Añade una nueva IP a la lista de IPs conocidas y la guarda permanentemente"""
        nueva_ip = simpledialog.askstring("Añadir Nueva IP", "Introduce la nueva dirección IP del servidor DNS:")
        
        if nueva_ip:
            # Validar formato de IP básico
            if not self.validar_formato_ip(nueva_ip):
                messagebox.showerror("IP Inválida", "Por favor introduce una dirección IP válida (ej: 192.168.1.100)")
                return
            
            if nueva_ip not in self.ips_conocidas:
                self.ips_conocidas.append(nueva_ip)
                
                # Actualizar todos los comboboxes en la interfaz
                for widget in self.root.winfo_children():
                    if isinstance(widget, ttk.Notebook):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Frame):
                                for combo in child.winfo_children():
                                    if isinstance(combo, ttk.Combobox):
                                        combo['values'] = self.ips_conocidas
                
                self.ip_servidor.set(nueva_ip)
                self.actualizar_estado(f"IP añadida: {nueva_ip}")
                
                # Guardar IPs permanentemente
                self.guardar_ips()
                
                messagebox.showinfo("Éxito", f"IP {nueva_ip} añadida y guardada permanentemente")
            else:
                messagebox.showinfo("Información", f"IP {nueva_ip} ya existe en la lista")
    
    def validar_formato_ip(self, ip):
        """Valida el formato básico de una IP"""
        partes = ip.split('.')
        if len(partes) != 4:
            return False
        
        for parte in partes:
            try:
                num = int(parte)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
        
        return True
    
    def examinar_archivo_consultas(self):
        """Abre diálogo para seleccionar archivo de consultas"""
        nombre_archivo = filedialog.askopenfilename(
            title="Seleccionar archivo de consultas",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if nombre_archivo:
            self.archivo_consultas.set(nombre_archivo)
            # Mostrar información del archivo
            try:
                tamano_archivo = os.path.getsize(nombre_archivo)
                contador_lineas = 0
                with open(nombre_archivo, 'r') as f:
                    contador_lineas = sum(1 for _ in f)
                
                self.etiqueta_info_archivo.config(
                    text=f"Archivo: {os.path.basename(nombre_archivo)} | Tamaño: {tamano_archivo:,} bytes | Líneas: {contador_lineas}",
                    foreground='black'
                )
                self.actualizar_estado(f"Archivo seleccionado: {os.path.basename(nombre_archivo)}")
            except:
                self.etiqueta_info_archivo.config(text=f"Archivo: {os.path.basename(nombre_archivo)}")
    
    def validar_parametros(self):
        """Valida todos los parámetros antes de ejecutar"""
        errores = []
        
        # Validar IP del servidor
        if not self.ip_servidor.get():
            errores.append("La IP del servidor DNS es requerida")
        elif not self.validar_formato_ip(self.ip_servidor.get()):
            errores.append("Formato de dirección IP inválido")
        
        # Validar archivo de consultas
        if not self.archivo_consultas.get():
            errores.append("El archivo de consultas es requerido")
        elif not os.path.isfile(self.archivo_consultas.get()):
            errores.append(f"Archivo de consultas no encontrado: {self.archivo_consultas.get()}")
        
        # Validar configuración de segmentos
        num_segmentos = int(self.num_segmentos.get())
        if len(self.duraciones_segmentos) != num_segmentos or len(self.qps_segmentos) != num_segmentos:
            errores.append(f"Debe configurar los {num_segmentos} segmentos")
        else:
            for i in range(num_segmentos):
                try:
                    duracion = int(self.duraciones_segmentos[i])
                    if duracion <= 0:
                        errores.append(f"Duración del segmento {i+1} debe ser positiva")
                    elif duracion > 3600:
                        errores.append(f"Duración del segmento {i+1} no puede exceder 3600 segundos")
                except ValueError:
                    errores.append(f"Duración del segmento {i+1} debe ser un número")
                
                try:
                    qps = int(self.qps_segmentos[i])
                    if qps <= 0:
                        errores.append(f"QPS del segmento {i+1} debe ser positivo")
                except ValueError:
                    errores.append(f"QPS del segmento {i+1} debe ser un número")
        
        return errores
    
    def construir_comando(self):
        """Construye el comando para ejecutar dnsperf con segmentos"""
        num_segmentos = int(self.num_segmentos.get())
        
        # Crear strings de duraciones y QPS separados por comas
        duraciones_str = ','.join(self.duraciones_segmentos)
        qps_str = ','.join(self.qps_segmentos)
        
        # Construir parámetros en el nuevo formato
        parametros = [
            self.ip_servidor.get(),
            str(num_segmentos),
            f'"{duraciones_str}"',
            f'"{qps_str}"',
            f'"{self.archivo_consultas.get()}"'
        ]
        
        # Construir comando bash
        comando_bash = f"./dnsperf_cubo.sh {' '.join(parametros)}"
        return comando_bash
    
    def mostrar_comando(self):
        """Muestra el comando que se ejecutará"""
        errores = self.validar_parametros()
        if errores:
            messagebox.showerror("Errores de Validación", "\n".join(errores))
            return
        
        comando = self.construir_comando()
        messagebox.showinfo("Comando DNSperf", f"Comando a ejecutar:\n\n{comando}")
    
    def iniciar_dnsperf(self):
        """Inicia la ejecución de dnsperf y real_time_export.sh en MV"""
        if self.en_ejecucion:
            messagebox.showwarning("Ya en Ejecución", "¡DNSperf ya está en ejecución!")
            return
        
        # Validar parámetros
        errores = self.validar_parametros()
        if errores:
            messagebox.showerror("Errores de Validación", "\n".join(errores))
            return
        
        # Mostrar resumen
        num_segmentos = int(self.num_segmentos.get())
        mensaje_confirmacion = f"¿Iniciar DNSperf con estos parámetros?\n\n"
        mensaje_confirmacion += f"Servidor: {self.ip_servidor.get()}\n"
        mensaje_confirmacion += f"Segmentos: {num_segmentos}\n"
        mensaje_confirmacion += f"Se ejecutará: sudo /usr/local/sbin/rndc flush al inicio\n"
        
        for i in range(num_segmentos):
            mensaje_confirmacion += f"  Segmento {i+1}: {self.duraciones_segmentos[i]}s (QPS={self.qps_segmentos[i]})\n"
        
        mensaje_confirmacion += f"\nArchivo de consultas: {os.path.basename(self.archivo_consultas.get())}\n"
        # mensaje_confirmacion += "real_time_export.sh se ejecutará automáticamente en la MV (sincronizado)."
        mensaje_confirmacion += "real_time_export.sh se ejecutará automáticamente en la MV."
        
        if not messagebox.askyesno("Confirmar Ejecución", mensaje_confirmacion):
            return
        
        # Actualizar estado
        self.en_ejecucion = True
        self.actualizar_estado("Iniciando DNSperf y exportación en MV...")
        
        # Limpiar consola y mostrar información
        self.texto_consola.delete(1.0, tk.END)
        self.texto_consola.insert(tk.END, "="*60 + "\n")
        self.texto_consola.insert(tk.END, "INICIANDO SIMULACIÓN DNSPERF\n")
        self.texto_consola.insert(tk.END, "="*60 + "\n")
        self.texto_consola.insert(tk.END, f"Servidor: {self.ip_servidor.get()}\n")
        self.texto_consola.insert(tk.END, f"Segmentos: {num_segmentos}\n")
        self.texto_consola.insert(tk.END, f"Flush al inicio: sudo /usr/local/sbin/rndc flush\n")
        
        for i in range(num_segmentos):
            self.texto_consola.insert(tk.END, f"  S{i+1}: {self.duraciones_segmentos[i]}s (QPS={self.qps_segmentos[i]})\n")
        
        self.texto_consola.insert(tk.END, f"Archivo de consultas: {os.path.basename(self.archivo_consultas.get())}\n")
        self.texto_consola.insert(tk.END, "="*60 + "\n\n")
        self.texto_consola.see(tk.END)
        
        # Ejecutar en hilo separado
        hilo = threading.Thread(target=self.ejecutar_dnsperf_con_control_mv)
        hilo.daemon = True
        hilo.start()
    
    def ejecutar_dnsperf_con_control_mv(self):
        """Ejecuta dnsperf en el cubo Y real_time_export.sh en la MV automáticamente"""
        try:
            import time
            
            # Calcular tiempo total de la simulación
            total_time = 0
            num_segmentos = int(self.num_segmentos.get())
            for i in range(num_segmentos):
                total_time += int(self.duraciones_segmentos[i])
            
            # 1. Iniciar real_time_export.sh en MV automáticamente
            self.root.after(0, lambda: self.texto_consola.insert(tk.END, "\n Iniciando real_time_export.sh en MV...\n"))
            
            # Iniciar en MV con tiempo limitado
            hilo_mv = threading.Thread(target=self.iniciar_export_mv_sincronizado, args=(total_time,))
            hilo_mv.daemon = True
            hilo_mv.start()
            
            # Esperar un momento para que inicie
            time.sleep(2)
            
            # 2. Construir y ejecutar comando DNSperf usando el nuevo script
            comando_dnsperf = self.construir_comando()
            
            self.root.after(0, lambda: self.texto_consola.insert(tk.END, f"\n Ejecutando: {comando_dnsperf}\n"))
            self.root.after(0, lambda: self.texto_consola.insert(tk.END, "="*60 + "\n"))
            
            # Ejecutar el script dnsperf_cubo.sh (que ya maneja múltiples segmentos)
            proceso = subprocess.Popen(
                comando_dnsperf,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.proceso_dnsperf = proceso
            
            # Leer salida en tiempo real
            for linea in iter(proceso.stdout.readline, ''):
                if linea:
                    self.root.after(0, self.anadir_a_consola, linea)
            
            exit_code = proceso.wait()
            
            # 3. Esperar a que real_time_export.sh termine (debería terminar automáticamente)
            time.sleep(2)
            
            # Asegurarse de detener real_time_export.sh si aún está ejecutándose
            if self.export_mv_en_ejecucion:
                self.root.after(0, lambda: self.texto_consola.insert(tk.END, "\n Deteniendo real_time_export.sh en MV...\n"))
                self.detener_export_mv()
            
            # Actualizar estado al terminar
            self.root.after(0, self.al_terminar_dnsperf, exit_code)
            
        except Exception as e:
            mensaje_error = f"Error ejecutando DNSperf: {str(e)}"
            self.root.after(0, lambda: self.texto_consola.insert(tk.END, f"\n{mensaje_error}\n"))
            self.root.after(0, lambda: self.actualizar_estado(f"Error: {str(e)}"))
            
            # Asegurarse de detener MV si hay error
            if self.export_mv_en_ejecucion:
                self.detener_export_mv()
            
            self.en_ejecucion = False
    
    def iniciar_export_mv_sincronizado(self, total_time):
        """Inicia real_time_export.sh en MV con tiempo limitado"""
        try:
            comando_ssh = f'ssh {self.mv_usuario}@{self.mv_host} "sudo {self.mv_ruta_script} {total_time}"'
            
            # Ejecutar en background
            self.proceso_export_mv = subprocess.Popen(
                ["bash", "-c", comando_ssh],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.export_mv_en_ejecucion = True
            self.root.after(0, lambda: self.actualizar_estado("Exportación en ejecución en MV"))
            self.root.after(0, lambda: self.texto_consola.insert(
                tk.END, f" real_time_export.sh iniciado en MV (tiempo total: {total_time}s)\n"))
            
            # Leer salida de la MV en tiempo real
            def leer_salida_mv():
                for linea in iter(self.proceso_export_mv.stdout.readline, ''):
                    if linea:
                        self.root.after(0, self.anadir_a_consola, f"[MV] {linea}")
            
            hilo_lectura = threading.Thread(target=leer_salida_mv)
            hilo_lectura.daemon = True
            hilo_lectura.start()
                
        except Exception as e:
            self.root.after(0, lambda: self.texto_consola.insert(
                tk.END, f" Error al iniciar en MV: {str(e)}\n"))
    
    def ejecutar_dnsperf_nuevo_formato(self):
        """Ejecuta dnsperf usando el nuevo script con segmentos"""
        try:
            import time
            
            # Construir comando
            comando = self.construir_comando()
            if not comando:
                return 1
            
            self.root.after(0, lambda: self.texto_consola.insert(
                tk.END, f"\n Ejecutando DNSperf con segmentos...\n"
            ))
            self.root.after(0, lambda: self.texto_consola.insert(
                tk.END, f"Comando: {comando}\n\n"
            ))
            
            # Ejecutar el script modificado
            proceso = subprocess.Popen(
                comando,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.proceso_dnsperf = proceso
            
            # Leer salida en tiempo real
            for linea in iter(proceso.stdout.readline, ''):
                if linea:
                    self.root.after(0, self.anadir_a_consola, linea)
            
            exit_code = proceso.wait()
            return exit_code
            
        except Exception as e:
            self.root.after(0, lambda: self.texto_consola.insert(
                tk.END, f"\n Error ejecutando DNSperf: {str(e)}\n"
            ))
            return 1
    
    def detener_export_mv(self):
        """Detiene real_time_export.sh en la MV"""
        if not self.export_mv_en_ejecucion:
            return
        
        try:
            comando_terminar = f'ssh {self.mv_usuario}@{self.mv_host} "sudo pkill -f real_time_export.sh"'
            subprocess.run(["bash", "-c", comando_terminar], 
                         capture_output=True, text=True, timeout=5)
            
            self.texto_consola.insert(tk.END, " real_time_export.sh detenido en MV\n")
            self.export_mv_en_ejecucion = False
            self.proceso_export_mv = None
            
        except Exception as e:
            self.texto_consola.insert(tk.END, f"Advertencia al detener MV: {str(e)}\n")
    
    def anadir_a_consola(self, texto):
        """Añade texto a la consola (thread-safe)"""
        self.texto_consola.insert(tk.END, texto)
        self.texto_consola.see(tk.END)
    
    def al_terminar_dnsperf(self, codigo_retorno):
        """Maneja la finalización de dnsperf"""
        self.en_ejecucion = False
        self.proceso_dnsperf = None
        
        if codigo_retorno == 0:
            self.actualizar_estado("DNSperf completado exitosamente")
            self.texto_consola.insert(tk.END, "\n" + "="*60 + "\n")
            self.texto_consola.insert(tk.END, " DNSPERF COMPLETADO EXITOSAMENTE\n")
            self.texto_consola.insert(tk.END, "="*60 + "\n")
        else:
            self.actualizar_estado(f"DNSperf falló con código {codigo_retorno}")
            self.texto_consola.insert(tk.END, f"\n DNSperf falló con código {codigo_retorno}\n")
    
    def detener_dnsperf(self):
        """Detiene la ejecución de dnsperf Y el export en MV"""
        if not self.en_ejecucion:
            messagebox.showinfo("No en Ejecución", "DNSperf no está en ejecución")
            return
        
        # Detener dnsperf local
        if self.proceso_dnsperf:
            self.proceso_dnsperf.terminate()
            self.actualizar_estado("Deteniendo DNSperf...")
            self.texto_consola.insert(tk.END, "\n DNSperf detenido por el usuario\n")
        
        # Detener export en MV automáticamente
        if self.export_mv_en_ejecucion:
            self.detener_export_mv()
        
        self.en_ejecucion = False
    
    def limpiar_consola(self):
        """Limpia la consola de salida"""
        self.texto_consola.delete(1.0, tk.END)
        self.actualizar_estado("Consola limpiada")
    
    def guardar_salida(self):
        """Guarda la salida de la consola a un archivo"""
        if not self.texto_consola.get(1.0, tk.END).strip():
            messagebox.showwarning("Consola Vacía", "No hay salida para guardar")
            return
        
        nombre_archivo = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Archivos log", "*.log"), ("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
            initialfile=f"salida_dnsperf_{os.path.basename(self.archivo_consultas.get())}.log"
        )
        
        if nombre_archivo:
            try:
                with open(nombre_archivo, 'w') as f:
                    f.write(self.texto_consola.get(1.0, tk.END))
                self.actualizar_estado(f"Salida guardada en {os.path.basename(nombre_archivo)}")
                messagebox.showinfo("Éxito", f"Salida guardada en:\n{nombre_archivo}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")
    
    def actualizar_estado(self, mensaje):
        """Actualiza la barra de estado"""
        self.barra_estado.config(text=f"Estado: {mensaje}")


def main():
    """Función principal"""
    root = tk.Tk()
    
    # Verificar que el script bash existe
    if not os.path.exists("./dnsperf_cubo.sh"):
        # Crear un script bash con el nuevo formato
        with open("dnsperf_cubo.sh", "w") as f:
            f.write()
        os.chmod("dnsperf_cubo.sh", 0o755)
        print("Script dnsperf_cubo.sh creado con el nuevo formato")
    
    app = DNSperfGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()