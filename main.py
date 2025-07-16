import tkinter as tk
import matplotlib.pyplot as plt
import diccionario_sensores as dic
import csv, re, serial, time, threading
from datetime import datetime
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from progress import LoadingWindow
import Interfaz_trayectorias
from analisis import analizar_csv
from cutpgm import seleccionar_y_recortar_mapa

import yaml
import os
from PIL import Image
import numpy as np
from tkinter import filedialog

# Clase base para los robots
class BaseRobot:
    """Clase base con funcionalidades comunes para todos los robots"""
    def __init__(self, notebook, robot_id, interface, LoRa):
        self.interface = interface
        self.robot_id = robot_id
        self.LoRa = LoRa
        self._setup_initial_state()
        self._init_ui(notebook)
    
    def _setup_initial_state(self):
        """Inicializa todas las variables de estado"""
        self.connection_status = True
        self.led_state = False
        self.medicion = 0
        self.checkpoint = 0
        self.battery = 0
        self.hours = 0
        self.minutes = 0
        self.posicionm = None # Posición manual del robot
        self.yaml = ""

        # Variables para mediciones
        self.zone = False
        self.in_measurement = False
        self.complete_measurement = False
        self.mediciones = {}
        self.checkpoints = {}
        self.puntos_muestreo = {}
        self.mediciones_completadas = False
        
    def _init_ui(self, notebook):
        """Configura la interfaz de usuario del robot"""
        self.frame = tk.Frame(notebook, bg='white')
        notebook.add(self.frame, text=f"Robot {self.robot_id}")
        
        self._create_control_bar()
        self._setup_plot()
        self._create_data_table()
        self._create_footer()

    def _create_control_bar(self):
        """Crea la barra superior de controles"""
        control_frame = tk.Frame(self.frame, bg='#002147')
        control_frame.pack(fill='x')
        
        button_style = {'bg': '#002147', 'fg': 'white'}
        
        tk.Label(control_frame, text=f"{self.robot_id}", bg='#002147', 
                fg='white', font=("Helvetica", 12)).pack(side='left', padx=20, pady=20)
        
        commands = [
            ("Iniciar Mediciones", "IM"),
            ("Regresar Robot", "RR"),
            ("Solicitar Ubicación", "SU"),
            ("Movimientos Manuales", "MM"),
            ("Información", "CK"),
            ("Solicitar Medicion", "RM"),
            ("Definir puntos de muestreo", "TE"),
            ("Cerrar conexión", "CC")
        ]
        
        for text, cmd in commands:
            tk.Button(control_frame, text=text, command=lambda c=cmd: self.request(c), 
                     **button_style).pack(side='left', padx=5, pady=5)
        
        self.led_label = tk.Label(control_frame, text="●", fg="gray", 
                                 bg='#002147', font=("Helvetica", 20))
        self.led_label.pack(side='left', padx=5, pady=5)
        
        self.battery_label = tk.Label(control_frame, text="Nivel de batería: 0%", 
                                    fg="white", bg='#002147', font=("Helvetica", 12))
        self.battery_label.pack(side='right', padx=5, pady=5)
        
        self.time_label = tk.Label(control_frame, text="Tiempo: 00:00", 
                                  fg="white", bg='#002147', font=("Helvetica", 12))
        self.time_label.pack(side='right', padx=5, pady=5)
     
    def _setup_plot(self):
        """Configura el gráfico para mostrar la ubicación del robot"""
        self.figure, self.ax = plt.subplots()
        self.ax.set_xlim(-100, 100)
        self.ax.set_ylim(-100, 100)
        self.location, = self.ax.plot(0, 0, 'ro')
        self.coord_label = self.ax.text(0, 0, f"(0, 0)", color='red', fontsize=10, va='bottom', ha='left')
        self.ax.set_title(f"Posición del Robot {self.robot_id}")
        self.ax.set_xlabel("Eje X")
        self.ax.set_ylabel("Eje Y")
        canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True, padx=5, pady=5)
        self.xmin = -100
        self.xmax = 100 
        self.ymin = -100
        self.ymax = 100
        self.ax.set_xlim(self.xmin, self.xmax)
        self.ax.set_ylim(self.ymin, self.ymax)

    def _setup_plot_YAML(self):
        
        ruta_yaml = filedialog.askopenfilename(
            title="Selecciona el archivo YAML del mapa",
            filetypes=[("YAML files", "*.yaml *.yml")]
        )
        if not ruta_yaml:
            print("No se seleccionó ningún archivo YAML.")
            return
        self.yaml = ruta_yaml
        self.zone == True
        # Cargar YAML
        with open(ruta_yaml, 'r') as f:
            config = yaml.safe_load(f)

        imagen_relativa = config["image"]
        resolution = config["resolution"]
        origin = config["origin"]
        directorio_yaml = os.path.dirname(ruta_yaml)
        ruta_imagen = os.path.join(directorio_yaml, imagen_relativa)

        imagen = Image.open(ruta_imagen)
        ancho, alto = imagen.size

        # Convertir origen de mundo a píxeles
        x_m, y_m = origin[0], origin[1]
        x_px = int(-x_m / resolution)
        y_px = int(alto - (-y_m / resolution))

        # === REUTILIZAR FIGURA EXISTENTE EN VEZ DE CREAR UNA NUEVA ===
        self.ax.clear()  # Limpia el contenido actual del eje

        # Mostrar imagen y puntos
        self.ax.imshow(imagen, cmap='gray')
        self.ax.scatter([x_px], [y_px], color='red', s=60, label="Origin")
        self.ax.set_title(f"Robot {self.robot_id} | Mapeo generado")
        self.ax.legend()
        self.ax.set_xlim(0, ancho)
        self.ax.set_ylim(alto, 0)
        self.ax.set_xlabel("X (px)")
        self.ax.set_ylabel("Y (px)")

        self.figure.canvas.mpl_connect('button_press_event', self.YAML_onclick)
        self.figure.tight_layout()
        self.figure.canvas.draw_idle()  # Redibuja el gráfico actualizado

        # Guardar info
        self.puntos_pixeles = []
        self.puntos_mundo = []
        self.puntos_plot = []
        self.etiquetas_puntos = []
        self.imagen_alto = alto
        self.resolution = resolution
        self.origin = origin
        self.xmin = 0
        self.xmax = origin[0] + ancho * resolution
        self.ymin = 0
        self.ymax = origin[1] + alto * resolution   

    def YAML_onclick(self,event):
        if not event.inaxes:
            return

        x_click = int(event.xdata)
        y_click = int(event.ydata)

        # BOTÓN IZQUIERDO: agregar punto
        if event.button == 1 and self.in_measurement == False:
            self.puntos_pixeles.append((x_click, y_click))

            x_world = round(x_click * self.resolution + self.origin[0],2)
            y_world = round((self.imagen_alto - y_click) * self.resolution + self.origin[1],2)
            self.puntos_mundo.append((x_world, y_world))

            punto = self.ax.plot(x_click, y_click, 'bo')[0]
            self.puntos_plot.append(punto)

            # Dibujar texto al lado del punto
            texto = f"({x_world:.2f}, {y_world:.2f})"
            etiqueta = self.ax.text(x_click + 5, y_click, texto, fontsize=8, color='blue')  # Puedes ajustar +5 si queda muy lejos
            self.etiquetas_puntos.append(etiqueta)

            print(f"➕ Punto agregado en píxeles: ({x_click}, {y_click}) -> metros: ({x_world:.2f}, {y_world:.2f})")

        # BOTÓN DERECHO: eliminar punto más cercano
        elif event.button == 3 and self.puntos_pixeles and self.in_measurement == False:
            # Calcular distancias a todos los puntos guardados
            distancias = [np.hypot(px - x_click, py - y_click) for px, py in self.puntos_pixeles]
            idx_min = int(np.argmin(distancias))

            if distancias[idx_min] < 15:  # tolerancia en píxeles
                # Eliminar datos
                eliminado_pix = self.puntos_pixeles.pop(idx_min)
                eliminado_mundo = self.puntos_mundo.pop(idx_min)
                punto_plot = self.puntos_plot.pop(idx_min)
                punto_plot.remove()
                etiqueta = self.etiquetas_puntos.pop(idx_min)
                etiqueta.remove()

                print(f"❌ Punto eliminado: ({eliminado_pix}) -> ({eliminado_mundo[0]:.2f}, {eliminado_mundo[1]:.2f})")
            else:
                print("No hay puntos suficientemente cerca para eliminar.")

        plt.draw()

    def eliminar_punto(self,id):
        print(self.puntos_mundo)
        print(self.puntos_plot)
        eliminado_pix = self.puntos_pixeles.pop(id)
        eliminado_mundo = self.puntos_mundo.pop(id)
        punto_plot = self.puntos_plot.pop(id)
        punto_plot.remove()
        etiqueta = self.etiquetas_puntos.pop(id)
        etiqueta.remove()
        print(f"❌ Punto eliminado: ({eliminado_pix}) -> ({eliminado_mundo[0]:.2f}, {eliminado_mundo[1]:.2f})")
            
    def _create_data_table(self):
        """Crea la tabla de datos para el robot"""
        self.data_table = ttk.Treeview(self.frame, columns=("Checkpoint", "Hora", "Sensor", "Valor"), show='headings', height=10)
        for col in ("Checkpoint", "Hora", "Sensor", "Valor"):
            self.data_table.heading(col, text=col)
        
        # Crear scrollbar vertical
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.data_table.yview)
        self.data_table.configure(yscrollcommand=scrollbar.set)
        
        self.data_table.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

    def _create_footer(self):
        """Crea el pie de página con botones adicionales"""
        footer_frame = tk.Frame(self.frame, bg='white')
        footer_frame.pack(fill='x', pady=10)

        btn_generar_reportes = tk.Button(
            footer_frame,
            text="Generar Reportes",
            command=self.create_reports, 
            bg='#002147',
            fg='white',
            font=("Helvetica", 10, "bold")
        )
        btn_generar_reportes.pack(pady=5)

        btn_limpiar_tabla = tk.Button(
            footer_frame,
            text="Limpiar tabla",
            command=self.clean, 
            bg='#002147',
            fg='white',
            font=("Helvetica", 10, "bold")
        )
        btn_limpiar_tabla.pack(pady=5)
    
        btn_save_map = tk.Button(
            footer_frame,
            text="Guardar mapa",
            command=self.savemap, 
            bg='#002147',
            fg='white',
            font=("Helvetica", 10, "bold")
        )
        btn_save_map.pack(pady=5)

    def set_LoRa(self, idLora):
        """Establece el módulo LoRa asociado al robot"""
        self.LoRa = LoRaModule(idLora)
        print(f"Robot {self.robot_id} configurado con LoRa ID: {idLora}")
    # Funciones para actualizar informacion recibida por el robot
    def update_ck(self,ck):
        self.checkpoint = int(ck)
        x_value, y_value = self.location.get_data()
        self.checkpoints[int(ck)] = (x_value[0], y_value[0])
    
    def clean(self):
        for row in  self.data_table.get_children():
            self.data_table.delete(row)
    
    def savemap(self):
        self.interface.send_message_to_client(self.robot_id,"save_map")

    def update_battery_level(self,level):
        if isinstance(level, float):
            self.battery_label.config(text=f"Nivel de batería: {level:.2f}%")
        else:
            self.battery_label.config(text=f"Nivel de batería: {level}%")

    # Función para establecer horas y minutos
    def set_time(self, hours, minutes):
        self.hours = hours
        self.minutes = minutes
        self.update_time_label()

    # Función para actualizar la etiqueta de tiempo
    def update_time_label(self):
        self.time_label.config(text=f"Tiempo: {self.hours:02d}:{self.minutes:02d}")

    def reset_time_label(self):
        """Reinicia la etiqueta de tiempo a 00:00"""
        self.hours = 0
        self.minutes = 0
        self.update_time_label()
    
    def increase_measure_count(self):
        self.medicion+=1

    def restart_measure_count(self):
        self.medicion = 0

    def insert_data(self, Time, Sensor, Value):
        x_value, y_value = self.location.get_data()
        self.data_table.insert("", "end", values=(f"CK:{self.checkpoint} ({x_value[0]},{y_value[0]})", f"{Time}",f"{Sensor}",f"{Value}"))

    def update_location(self,x,y):
        self.location.set_data([x], [y])
        if self.yaml == "":
            self.coord_label.set_position((x, y))
            self.coord_label.set_text(f"({x}, {y})")
            self.figure.canvas.draw()
        else:
            x_px = int((x - self.origin[0]) / self.resolution)
            y_px = int(self.imagen_alto - ((y - self.origin[1]) / self.resolution))

            self.ax.scatter([x_px], [y_px], color='green')

            # Dibujar texto al lado del punto
            texto = f"({x:.2f}, {y:.2f})"
            self.ax.text(x_px + 5, y_px, texto, fontsize=8, color='green') 
            self.figure.canvas.draw_idle()

    def sent_xy(self,x,y,w):
        print(f"Mandando CK {self.checkpoint} con destino a X:{x} Y:{y}")
        message = f"/x{x}/y{y}/w{w}"
        self.interface.send_message_to_client(self.robot_id,message)

    def update_limits(self, xmin, xmax, ymin, ymax):
        self.xmin = float(xmin)
        self.xmax = float(xmax)
        self.ymin = float(ymin)
        self.ymax = float(ymax)
        self.ax.set_xlim(self.xmin, self.xmax)
        self.ax.set_ylim(self.ymin, self.ymax)
        self.ax.figure.canvas.draw()
        print(f"Actualizando limites del mapa a: X({xmin}, {xmax}), Y({ymin}, {ymax})")

    def connection(self,status):
        self.connection_status = status
        if status:
            self.led_label.config(fg="green")
        else:
            self.led_label.config(fg="gray")

    def create_reports(self):
        # Crear nueva ventana de formulario
        forms = tk.Toplevel(self.frame)
        forms.title("Información de mediciones")
        forms.geometry("300x250")
        forms.configure(bg='white')

        # Etiquetas y campos de entrada
        tk.Label(forms, text="Nombre del Reporte:", bg='white').pack(pady=(10, 0))
        entry_nombre = tk.Entry(forms, width=30)
        entry_nombre.pack()

        tk.Label(forms, text="Comentarios:", bg='white').pack(pady=(10, 0))
        entry_comentarios = tk.Text(forms, width=30, height=4)
        entry_comentarios.pack()

        # Botón de enviar
        def generate_report():
            nombre = entry_nombre.get()
            comentarios = entry_comentarios.get("1.0", "end").strip()
            columns = self.data_table["columns"]
                # Abrir el archivo CSV para escritura
            with open(f"{nombre} robot {self.robot_id}.csv", mode='w', newline='') as file:

                writer = csv.writer(file)
                writer.writerow([f"Robot: {self.robot_id}"])
                writer.writerow([f"Comentarios: {comentarios}"])
                writer.writerow(["xmin, xmax, ymin, ymax",f"({self.xmin},{self.xmax},{self.ymin},{self.ymax})"])
                writer.writerow(["========================"])
                writer.writerow(columns)
                    
                for row_id in self.data_table.get_children():
                    row = self.data_table.item(row_id)['values']
                    writer.writerow(row)
                print(f"Archivo {nombre}.csv generado con exito")
            forms.destroy()

        tk.Button(forms, text="Aceptar", command=generate_report, bg='#002147', fg='white').pack(pady=10)

    def reintentar_ck(self):
        print(f"Reintentando checkpoint {self.checkpoint+1}: ahora en {self.puntos_muestreo[self.checkpoint][0]:.2f}, {self.puntos_muestreo[self.checkpoint][1]:.2f}")
        self.sent_xy(self.puntos_muestreo[self.checkpoint][0],self.puntos_muestreo[self.checkpoint][1],0)
    
    def reintentar_med(self):
        print(f"Reintentando medición {self.medicion+1} de {self.n} muestras")
        self.interface.send_message_to_client(self.robot_id, "RM")

    # Funciones para solicitar informacion al robot
    def request(self, comando):
        if self.connection_status:
            if comando == "IM":
                print(f"Robot {self.robot_id}: Solicitó Mediciones")
                self.n = 0
                self.t = 0
                self.puntos_muestreo = []
                self.checkpoint = 0
                self.restart_measure_count() 
                x_value, y_value = self.location.get_data()  

                if self.zone == False:
                    self.Map_data()
                try:
                    if self.zone == False and self.yaml == "":
                        raise ValueError("Debes definir los límites del mapa antes de iniciar las mediciones.")
                    
                    if self.yaml == "":
                        Trayectoria = Interfaz_trayectorias.VentanaTrayectorias(
                            master=self.frame,
                            xmin=self.xmin, xmax=self.xmax, ymin=self.ymin, ymax=self.ymax,
                            x0=x_value[0], y0=y_value[0], xc=0, yc=0,
                            fs=2
                        )
                                        
                        Trayectoria.root.wait_window()
                        self.in_measurement = True
                        self.n = Trayectoria.muestrasn
                        self.t = Trayectoria.tiempo
                        self.puntos_muestreo = Trayectoria.puntos_de_muestreo
                        self.iniciar_mediciones()
                    else:
                        # Crear ventana Toplevel con el frame principal
                        ventana = tk.Toplevel(self.frame)
                        ventana.title("Interfaz de Control")
                        ventana.geometry("400x300")

                        # Mostrar puntos
                        tk.Label(ventana, text="Puntos de muestreo:").pack(pady=5)

                        text_puntos = tk.Text(ventana, height=8, wrap="none")
                        text_puntos.pack(padx=10, fill='both', expand=True)

                        for punto in self.puntos_mundo:
                            text_puntos.insert(tk.END, f"{punto}\n")
                        text_puntos.config(state='disabled')

                        # Entradas de parámetros
                        frame_inputs = tk.Frame(ventana)
                        frame_inputs.pack(pady=10)

                        tk.Label(frame_inputs, text="n (número de muestras):").grid(row=0, column=0, sticky='e', padx=5, pady=2)
                        entry_n = tk.Entry(frame_inputs)
                        entry_n.grid(row=0, column=1)

                        tk.Label(frame_inputs, text="t (tiempo total en seg):").grid(row=1, column=0, sticky='e', padx=5, pady=2)
                        entry_t = tk.Entry(frame_inputs)
                        entry_t.grid(row=1, column=1)

                        # Función para validar y cerrar
                        def confirmar():
                            try:
                                self.n = int(entry_n.get())
                                self.t = float(entry_t.get())
                                self.puntos_muestreo = self.puntos_mundo
                                print("Puntos:", self.puntos_muestreo)
                                print("n:", self.n)
                                print("t:", self.t)
                                ventana.destroy()
                                self.iniciar_mediciones()
                            except ValueError:
                                messagebox.showerror("Error", "Ingrese valores válidos para n y t.")

                        # Botón de confirmar
                        tk.Button(ventana, text="Aceptar", command=confirmar).pack(pady=10)
                except Exception as e:
                    print(f"Error al iniciar mediciones: {e}")
                    messagebox.showerror("Error", "No se pudo iniciar la medición. Verifica los parámetros.")

            elif comando == "RR":
                print(f"Robot {self.robot_id}: Regresar Robot")
                self.interface.send_message_to_client(self.robot_id,"/x0/y0/w0")

            elif comando == "TE":
                print(f"Robot {self.robot_id}: Definir puntos de muestreo")
                self.in_measurement = False
                
            elif comando == "SU":
                print(f"Robot {self.robot_id}: Solicitar Ubicación")
                self.interface.send_message_to_client(self.robot_id,"SU")
                self.checkpoint = 0
                self.posicionm = None # Posición manual del robot
                # Variables para mediciones
                self.zone = False
                self.in_measurement = False
                self.complete_measurement = False
                self.mediciones = {}
                self.checkpoints = {}
                self.puntos_muestreo = {}
                self.mediciones_completadas = False
            elif comando == "MM":
                print(f"Robot {self.robot_id}: Movimientos Manuales")
                # Crear ventana principal
                ventana = tk.Toplevel(self.frame)
                ventana.title("Interfaz de Control")

                # Etiquetas y entradas
                tk.Label(ventana, text="Valor X:").grid(row=0, column=0, padx=10, pady=5)
                entrada_x = tk.Entry(ventana)
                entrada_x.grid(row=0, column=1, padx=10, pady=5)

                tk.Label(ventana, text="Valor Y:").grid(row=1, column=0, padx=10, pady=5)
                entrada_y = tk.Entry(ventana)
                entrada_y.grid(row=1, column=1, padx=10, pady=5)

                tk.Label(ventana, text="Valor W:").grid(row=2, column=0, padx=10, pady=5)
                entrada_w = tk.Entry(ventana)
                entrada_w.grid(row=2, column=1, padx=10, pady=5)

                def obtener_valores():
                    try:
                        x = float(entrada_x.get())
                        y = float(entrada_y.get())
                        w = float(entrada_w.get())
                        self.interface.send_message_to_client(self.robot_id, f"/x{x}/y{y}/w{w}")
                        self.posicionm = (x, y)
                        print("Valores enviados correctamente.")
                    except ValueError:
                        messagebox.showerror(title="Error", message="Por favor ingresa solo números.")

                # Botones
                tk.Button(ventana, text="Aceptar", command=obtener_valores).grid(row=3, column=0, pady=10)
                tk.Button(ventana, text="Direcciones", command=lambda: self.abrir_ventana_direcciones(ventana)).grid(row=3, column=1, pady=10)

            elif comando == "CK":
                print(f"Robot {self.robot_id}: Cargar información")
                self.interface.send_message_to_client(self.robot_id,"CK")
                # Solicitar al usuario que introduzca los valores manualmente
                #x_value = y_value = None
                self.zone = True
                self._setup_plot_YAML()
            elif comando == "RM":
                print(f"Robot {self.robot_id}: Solicitar Medicion")
                self.interface.send_message_to_client(self.robot_id,"RM")
            elif comando == "CC":
                print(f"Robot {self.robot_id}: Cerrando conexión")
                self.interface.send_message_to_client(self.robot_id,"CC")
        else:
            messagebox.showwarning("Error", "No hay conexion con el robot")

    def iniciar_mediciones(self):
        for i, punto in enumerate(self.puntos_muestreo):
            print(f"Checkpoint: {i}, Punto: ({punto[0]:.2f}, {punto[1]:.2f})")
        if self.n <= 0 or self.t <= 0:
            raise ValueError("Número de muestras o tiempo entre muestras no puede ser cero o negativo.")
        if not self.puntos_muestreo:
            raise ValueError("No se generaron puntos de muestreo.")
        if len(self.puntos_muestreo) >= 1:
            self.loading_window = LoadingWindow(self.frame,len(self.puntos_muestreo),self.n, retry_ck_callback=self.reintentar_ck,  retry_med_callback=self.reintentar_med)
        print(f"Tiempo total de muestreo {len(self.puntos_muestreo)*self.t*self.n} segundos")
        self.sent_xy(self.puntos_muestreo[self.checkpoint][0],self.puntos_muestreo[self.checkpoint][1],0)
        self.in_measurement = True

    def Map_data(self):
        try:
                    # Crear formulario para ingresar los valores
            form = tk.Toplevel(self.frame)
            form.title("Introducir información manualmente")
            form.geometry("300x350")
            form.configure(bg='white')

            tk.Label(form, text="Posición X:", bg='white').pack(pady=(10, 0))
            entry_x = tk.Entry(form)
            entry_x.pack()

            tk.Label(form, text="Posición Y:", bg='white').pack(pady=(10, 0))
            entry_y = tk.Entry(form)
            entry_y.pack()

            tk.Label(form, text="X mínimo del mapa:", bg='white').pack(pady=(10, 0))
            entry_xmin = tk.Entry(form)
            entry_xmin.pack()

            tk.Label(form, text="X máximo del mapa:", bg='white').pack(pady=(10, 0))
            entry_xmax = tk.Entry(form)
            entry_xmax.pack()

            tk.Label(form, text="Y mínimo del mapa:", bg='white').pack(pady=(10, 0))
            entry_ymin = tk.Entry(form)
            entry_ymin.pack()

            tk.Label(form, text="Y máximo del mapa:", bg='white').pack(pady=(10, 0))
            entry_ymax = tk.Entry(form)
            entry_ymax.pack()

            def aceptar():
                try:
                    x_value = float(entry_x.get())
                    y_value = float(entry_y.get())
                    xmin = float(entry_xmin.get())
                    xmax = float(entry_xmax.get())
                    ymin = float(entry_ymin.get())
                    ymax = float(entry_ymax.get())
                    self.zone = True
                    self.update_location(x_value, y_value)
                    self.update_limits(xmin, xmax, ymin, ymax)
                    form.destroy()
                except Exception:
                    messagebox.showerror("Error", "Debes introducir valores numéricos para todos los campos.")

            tk.Button(form, text="Aceptar", command=aceptar, bg='#002147', fg='white').pack(pady=15)
        except Exception as e:
            messagebox.showerror("Error", "Debes introducir valores numéricos para X e Y.")
            return

    def Map_data_from_yaml(self):
        """Carga los datos del mapa desde un archivo YAML y recorta la imagen del mapa"""
        ruta_yaml = seleccionar_y_recortar_mapa()
        print(f"Ruta del YAML: {ruta_yaml}")
        xmin = float(f"{ruta_yaml['xmin']:.2f}")
        xmax = float(f"{ruta_yaml['xmax']:.2f}")
        ymin = float(f"{ruta_yaml['ymin']:.2f}")
        ymax = float(f"{ruta_yaml['ymax']:.2f}")
        self.zone = True
        self.update_location(0,0)
        self.update_limits(xmin, xmax, ymin, ymax)       
        """if ruta_yaml is None:
            return

        # Leer el archivo .yaml
        with open(ruta_yaml, 'r') as f:
            config = yaml.safe_load(f)

        image_rel_path = config["image"]
        resolution = config["resolution"]
        origin = config["origin"]

        # Obtener ruta absoluta del .pgm
        dir_yaml = os.path.dirname(ruta_yaml)
        ruta_imagen = os.path.join(dir_yaml, image_rel_path)

        # Cargar imagen
        imagen = Image.open(ruta_imagen)
        ancho, alto = imagen.size

        # Recortar la imagen y obtener los puntos
        recorte_info = recortar_imagen(imagen, resolution, origin, ancho, alto, ruta_yaml, ruta_imagen)
        
        if recorte_info is not None:
            self.update_limits(recorte_info['xmin'], recorte_info['xmax'], recorte_info['ymin'], recorte_info['ymax'])
            #self.update_location((recorte_info['xmin'] + recorte_info['xmax']) / 2, (recorte_info['ymin'] + recorte_info['ymax']) / 2)
            self.zone = True
        """

    def add_event(self,ck,num):
        if self.loading_window:
            self.loading_window.increment_progress(ck,num)

    def abrir_ventana_direcciones(self, parent_ventana):
        ventana_direcciones = tk.Toplevel(parent_ventana)
        ventana_direcciones.title("Control de Direcciones")

        def enviar_direccion(direccion):
            self.interface.send_message_to_client(self.robot_id, f"/{direccion}")

        btn_adelante = tk.Button(ventana_direcciones, text="↑ Delante")
        btn_adelante.grid(row=0, column=1, pady=5)
        btn_adelante.bind("<ButtonPress>", lambda e: enviar_direccion("q"))
        btn_adelante.bind("<ButtonRelease>", lambda e: enviar_direccion("x"))

        btn_giro_izquierda = tk.Button(ventana_direcciones, text="← Izquierda")
        btn_giro_izquierda.grid(row=1, column=0, padx=5)
        btn_giro_izquierda.bind("<ButtonPress>", lambda e: enviar_direccion("a"))
        btn_giro_izquierda.bind("<ButtonRelease>", lambda e: enviar_direccion("x"))

        btn_giro_derecha = tk.Button(ventana_direcciones, text="→ Derecha")
        btn_giro_derecha.grid(row=1, column=2, padx=5)
        btn_giro_derecha.bind("<ButtonPress>", lambda e: enviar_direccion("d"))
        btn_giro_derecha.bind("<ButtonRelease>", lambda e: enviar_direccion("x"))
        
        btn_atras = tk.Button(ventana_direcciones, text="↓ Atrás")
        btn_atras.grid(row=2, column=1, padx=5)
        btn_atras.bind("<ButtonPress>", lambda e: enviar_direccion("s"))
        btn_atras.bind("<ButtonRelease>", lambda e: enviar_direccion("x"))

        btn_parar = tk.Button(ventana_direcciones, text="Parar")
        btn_parar.grid(row=1, column=1, pady=5)
        btn_parar.bind("<ButtonPress>", lambda e: enviar_direccion("x"))

# Subclase para un robot que se desempeña de manera especial
class RobotEspecial(BaseRobot):

    def _create_control_bar(self):
        """Crea una barra superior de controles personalizada para el robot especial"""
        control_frame = tk.Frame(self.frame, bg='#002147')
        control_frame.pack(fill='x')

        button_style = {'bg': '#002147', 'fg': 'white'}

        tk.Label(control_frame, text=f"{self.robot_id}",fg='white', bg='#002147', font=("Helvetica", 13, "bold")).pack(side='left', padx=20, pady=20)

        # Botones personalizados para el robot especial
        commands = [
            ("Iniciar mediciones", "TE"),
            ("Detener mediciones", "DT"),
            ("Solicitar Estado", "SE"),
            ("Enviar Comando", "EC"),
            ("Cerrar conexión", "CC")
        ]

        for text, cmd in commands:
            tk.Button(control_frame, text=text, command=lambda c=cmd: self.request(c), 
                     **button_style).pack(side='left', padx=5, pady=5)

        self.led_label = tk.Label(control_frame, text="●", fg="gray", 
                                 bg="#002147", font=("Helvetica", 20))
        self.led_label.pack(side='left', padx=5, pady=5)

    def _create_footer(self):
        """Crea el pie de página con botones adicionales"""
        footer_frame = tk.Frame(self.frame, bg='white')
        footer_frame.pack(fill='x', pady=10)

        btn_generar_reportes = tk.Button(
            footer_frame,
            text="Generar Reportes",
            command=self.create_reports, 
            bg='#002147',
            fg='white',
            font=("Helvetica", 10, "bold")
        )
        btn_generar_reportes.pack(pady=5)

        btn_limpiar_tabla = tk.Button(
            footer_frame,
            text="Limpiar tabla",
            command=self.clean, 
            bg='#002147',
            fg='white',
            font=("Helvetica", 10, "bold")
        )
        btn_limpiar_tabla.pack(pady=5)

    def update_battery_level(self,level):
        return
    def abrir_ventana_direcciones(self, parent_ventana):
        return
    def set_time(self, hours, minutes):
        return
    def update_time_label(self):
        return
    def savemap(self):
        return
    def reset_time_label(self):
        return
    
class LoRaModule():
    def __init__(self, idLora):
        self.idLora = idLora
        self.mensajeenviado = False
        self.respuesta = True
        self.robot_request = None
    
    def set_robot_request(self, robot_id):
        self.robot_request = robot_id
    def get_robot_request(self):
        return self.robot_request
    def set_mensajeenviado(self, estado):
        self.mensajeenviado = estado
    def get_mensajeenviado(self):
        return self.mensajeenviado
    def set_respuesta(self, estado):
        self.respuesta = estado
    def get_respuesta(self):
        return self.respuesta

class RobotInterface():
    # Clase que maneja la interfaz de usuario y la comunicación con los robots
    def __init__(self):
        # Inicialización de la ventana principal
        self._setup_initial_state()
        self._init_ui()    

    def _setup_initial_state(self):
        """Inicializa todas las variables de estado"""  
        # Configuración del puerto serial
        SERIAL_PORT = "" 
        BAUD_RATE = 115200
        self.configuration = False
        self.ser = serial.Serial()
        self.mensaje_enviado = False
        self.respuesta = False

        # Diccionario para almacenar los robots
        self.robots = {}  
        self.id_robots = [1, 2, 3, 4]
        self.loras = {}  
        self.id_loras = [1, 2]

    def _init_ui(self):
        self.root = tk.Tk()
        self.root.title("Panel de control para Robots")
        self.root.geometry("1500x1000")
        self.root.configure(bg='white')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_general_window()
        self._setup_plot()
        self._create_data_table()
        self._create_footer()
    
    def create_general_window(self):
        # Notebook para separar cada robot y la ventana general
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Pestaña para la Ventana General
        self.general_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.general_frame, text="General")

        # Frame principal centrado para controles y entradas
        controls_outer_frame = tk.Frame(self.general_frame, bg='white')
        controls_outer_frame.pack(fill='x', pady=10)

        # Frame interno para centrar los controles
        controls_frame = tk.Frame(controls_outer_frame, bg='white')
        controls_frame.pack(anchor='center')

        button_style = {'bg': '#002147', 'fg': 'white'}

        # Botones de control
        btn_iniciar = tk.Button(controls_frame, text="Iniciar Conexion", command=self.start_connection, **button_style)
        btn_detener = tk.Button(controls_frame, text="Detener Conexion", command=self.stop, **button_style)
        btn_iniciar.grid(row=0, column=0, padx=8, pady=5)
        btn_detener.grid(row=0, column=1, padx=8, pady=5)

        # Entradas y etiquetas en una sola línea, centradas
        entry_frame = tk.Frame(controls_frame, bg='white')
        entry_frame.grid(row=0, column=2, padx=20)

        tk.Button(entry_frame, text="Comandos AT", command=self.at, **button_style).pack(side='left', padx=2)

        tk.Label(entry_frame, text="Puerto Serial:", bg='white').pack(side='left', padx=2)
        self.port_entry = tk.Entry(entry_frame, width=10)
        self.port_entry.pack(side='left', padx=2)

        tk.Label(entry_frame, text="Baudios:", bg='white').pack(side='left', padx=2)
        self.baud_entry = tk.Entry(entry_frame, width=10)
        self.baud_entry.insert(0, "115200")
        self.baud_entry.pack(side='left', padx=2)


        for i in self.id_loras:
            # Se utiliza LoRaModule para los módulos LoRa
            lora = LoRaModule(i)
            self.loras[i] = lora

        for i in self.id_robots:
            if i == 1 or i == 2 or i == 3:
                robot = BaseRobot(self.notebook, i, self, 1)
            else:
                robot = RobotEspecial(self.notebook, i, self, 2)
            self.robots[i] = robot

    def _setup_plot(self):
        # Mapa general
        self.figure, ax = plt.subplots()
        self.set_map_limits(ax)
        ax.set_title("Mapa General de Robots")
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        canvas = FigureCanvasTkAgg(self.figure, master=self.general_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True, padx=5, pady=5)

        # Agregar robots al mapa general
        self.robots_location = {
            'LR1': ax.plot(0, 0, 'ro')[0],
            'LR2': ax.plot(0, 0, 'bo')[0],
            'LR3': ax.plot(0, 0, 'go')[0],
            'LR4': ax.plot(0, 0, 'o', color='purple')[0]
        }
        self.robots_location_labels = {
            # Agregar etiquetas para cada robot
            'LR1':ax.text(0, 0, 'Robot 1', color='red', fontsize=12),
            'LR2':ax.text(0, 0, 'Robot 2', color='blue', fontsize=12),
            'LR3':ax.text(0, 0, 'Robot 3', color='green', fontsize=12),
            'LR4':ax.text(0, 0, 'Robot 4', color='purple', fontsize=12)
        }

    def _create_data_table(self):
        # Tabla de datos general
        self.general_data_table = ttk.Treeview(self.general_frame, columns=("Robot", "Sensor", "Valor"), show='headings')
        for col in ("Robot", "Sensor", "Valor"):
            self.general_data_table.heading(col, text=col)
        self.general_data_table.pack(fill='both', expand=True, padx=5, pady=5)

    def _create_footer(self):
        footer_frame = tk.Frame(self.general_frame, bg='white')
        footer_frame.pack(fill='x', pady=10)

        btn_generar_reportes = tk.Button(
            footer_frame,
            text="Generar Reportes",
            command=self.create_reports, 
            bg='#002147',
            fg='white',
            font=("Helvetica", 10, "bold")
        )
        btn_generar_reportes.pack(pady=5)

        btn_limpiar_tabla = tk.Button(
            footer_frame,
            text="Limpiar tabla",
            command=self.limpiar_tabla, 
            bg='#002147',
            fg='white',
            font=("Helvetica", 10, "bold")
        )
        btn_limpiar_tabla.pack(pady=5)
        btn_analizar_csv = tk.Button(
            footer_frame,
            text="Analizar CSV",
            command=self.analizar_csv,
            bg='#002147',
            fg='white',
            font=("Helvetica", 10, "bold")
        )
        btn_analizar_csv.pack(pady=5)
    
    # --- FUNCIONES DE LA INTERFAZ ---
    # Inicia la conexión serial y espera a que el ESP32 envíe "READY"
    def start_connection(self):
        print("Iniciando comunicacion serial")
        if not self.ser.is_open and self.configuration == False:
            self.ser.port = "COM"+self.port_entry.get()
            self.ser.baudrate = int(self.baud_entry.get())
            self.ser.open()
            print("Conectado al puerto serial\n")
            # Esperar a que llegue "READY" del ESP32 en un hilo separado
            def wait_for_ready():
                ready = ""
                while "READY" not in ready:
                    if self.ser.in_waiting:
                        ready += self.ser.read(self.ser.in_waiting).decode(errors="ignore")
                    time.sleep(0.1)
                time.sleep(2)
                print("LoRa configurado")
                threading.Thread(target=self.handle_client, daemon=True).start()
                print("Buscando robots conectados")
                self.configuration = True
                self.root.after(0, self.show_robot_buttons)
            threading.Thread(target=wait_for_ready, daemon=True).start()

        elif self.ser.is_open:
            # Solo abrir la ventana si no existe ya una ventana de selección de robot
            for window in self.root.winfo_children():
                if isinstance(window, tk.Toplevel) and window.title() == "Seleccionar robot":
                    window.lift()
                    window.focus_force()
                    break
            else:
                self.show_robot_buttons()
            self.configuration = True

    # Detiene la conexión serial y cierra la comunicación con los robots
    def stop(self):
        print("Cerrando comunicación serial")
        if self.ser.is_open:
            for robot in self.robots:
                self.robots[robot].connection(False)
            self.ser.close()
            self.configuration = False
            print("Conexión cerrada correctamente\n")
        else:
            self.configuration = False
            print("La conexión ya estaba cerrada")
        # Limpiar el mapa general y la tabla de datos
        self.general_data_table.delete(*self.general_data_table.get_children())
        for robot in self.robots:
            self.reset_conf(0, self.robots[robot])

    # Ventana para seleccionar el robot e iniciar la comunicación
    def show_robot_buttons(self):
        if self.configuration == False:
            messagebox.showwarning("Advertencia", "Por favor, inicia la conexión primero.")
            return
        button_window = tk.Toplevel(self.root)
        button_window.title("Seleccionar robot")
        width, height = 250, 250

        screen_width = button_window.winfo_screenwidth()
        screen_height = button_window.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))

        button_window.geometry(f"{width}x{height}+{x}+{y}")
        button_window.resizable(True, True)

        label = tk.Label(button_window, text="Selecciona un robot:")
        label.pack(pady=10)

        for i in range(1, 5):  # Botones del 1 al 4
            btn = tk.Button(
                button_window,
                text=f"Robot {i}",
                width=15,
                command=lambda r=i: self.send_message_to_client(r, "IC")
            )
            btn.pack(pady=5)

    # Limpia la tabla de datos general
    def limpiar_tabla(self):
        # Ventana para elegir borrar todo o por número de robot
        limpiar_win = tk.Toplevel(self.root)
        limpiar_win.title("Limpiar tabla")
        limpiar_win.geometry("300x200")
        limpiar_win.configure(bg='white')

        def borrar_todo():
            self.general_data_table.delete(*self.general_data_table.get_children())
            limpiar_win.destroy()

        def borrar_por_robot():
            num_robot = entry_robot.get()
            if not num_robot:
                messagebox.showwarning("Advertencia", "Ingresa el número de robot.")
                return
            for row_id in self.general_data_table.get_children():
                values = self.general_data_table.item(row_id)['values']
                if str(values[0]) == num_robot:
                    self.general_data_table.delete(row_id)
            limpiar_win.destroy()

        tk.Label(limpiar_win, text="¿Qué desea borrar?", bg='white').pack(pady=10)
        tk.Button(limpiar_win, text="Borrar todo", command=borrar_todo, bg='#002147', fg='white').pack(pady=5)
        tk.Label(limpiar_win, text="O borrar por número de robot:", bg='white').pack(pady=(10,0))
        entry_robot = tk.Entry(limpiar_win)
        entry_robot.pack(pady=2)
        tk.Button(limpiar_win, text="Borrar por robot", command=borrar_por_robot, bg='#002147', fg='white').pack(pady=5)

    # Define los límites del mapa general
    def set_map_limits(self, ax, xlim=(-100, 100), ylim=(-100, 100)):
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)

    # crea los reportes de mediciones general
    def create_reports(self):
            # Crear nueva ventana de formulario
            forms = tk.Toplevel(self.frame)
            forms.title("Información de mediciones")
            forms.geometry("300x250")
            forms.configure(bg='white')

            tk.Label(forms, text="Nombre del Reporte:", bg='white').pack(pady=(10, 0))
            entry_nombre = tk.Entry(forms, width=30)
            entry_nombre.pack()

            tk.Label(forms, text="Autor:", bg='white').pack(pady=(10, 0))
            entry_autor = tk.Entry(forms, width=30)
            entry_autor.pack()

            tk.Label(forms, text="Comentarios:", bg='white').pack(pady=(10, 0))
            entry_comentarios = tk.Text(forms, width=30, height=4)
            entry_comentarios.pack()

            def generate_report():
                nombre = entry_nombre.get()
                autor = entry_autor.get()
                comentarios = entry_comentarios.get("1.0", "end").strip()
                columns = self.data_table["columns"]
                with open(f"{nombre}.csv", mode='w', newline='') as file:

                    writer = csv.writer(file)
                    writer.writerow([f"Robot: {self.robot_id}"])
                    writer.writerow([f"Autor: {autor}"])
                    writer.writerow([f"Comentarios: {comentarios}"])
                    writer.writerow(["========================"])
                    writer.writerow(columns)
                    for row_id in self.data_table.get_children():
                        row = self.data_table.item(row_id)['values']
                        writer.writerow(row)
                    print(f"Archivo {nombre}.csv generado con exito")
                forms.destroy()
            tk.Button(forms, text="Aceptar", command=generate_report, bg='#002147', fg='white').pack(pady=10)
            
    # Se envía comando AT al ESP32, especialmente para configurar LoRa
    def at(self):

        if not self.ser.is_open:
            messagebox.showerror("Error", "La conexión serial no está abierta")
            return
            
        # Crear ventana emergente
        at_window = tk.Toplevel(self.root)
        at_window.title("Enviar Comando AT")
        at_window.geometry("500x300")
        # Estilos
        label_style = {'font': ('Arial', 10), 'padx': 5, 'pady': 5}
        entry_style = {'font': ('Arial', 10), 'width': 30}
        button_style = {'bg': '#002147', 'fg': 'white', 'font': ('Arial', 10)}
        # Frame principal
        main_frame = tk.Frame(at_window, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Selección del módulo LoRa
        tk.Label(main_frame, text="Módulo LoRa:", **label_style).grid(row=0, column=0, sticky='e')
        module_var = tk.StringVar()       

        lora_modules = [f"LoRa {i}" for i in range(1, 3)]  # Simulación de módulos LoRa
        module_combobox = ttk.Combobox(main_frame, textvariable=module_var, values=lora_modules)
        module_combobox.grid(row=0, column=1, pady=5, sticky='w')
        module_combobox.current(0)  # Seleccionar el primer módulo por defecto
        # 2. Comandos AT comunes
        tk.Label(main_frame, text="Comando AT:", **label_style).grid(row=1, column=0, sticky='e')
        command_var = tk.StringVar()

        common_commands = [
            "AT+RESET",
            "AT+IPR",
            "AT+ADDRESS",
            "AT+NETWORKID",
            "AT+MODE",
            "AT+PARAMETER",
            "AT+SEND=",
            "AT+RECV"
        ]
        
        cmd_combobox = ttk.Combobox(main_frame, textvariable=command_var, values=common_commands)
        cmd_combobox.grid(row=1, column=1, pady=5, sticky='w')
 
        # 3. Parámetros del comando
        tk.Label(main_frame, text="Parámetros:", **label_style).grid(row=2, column=0, sticky='e')
        params_entry = tk.Entry(main_frame, **entry_style)
        params_entry.grid(row=2, column=1, pady=5, sticky='w')

        # 4. Comando completo (solo lectura)
        tk.Label(main_frame, text="Comando completo:", **label_style).grid(row=3, column=0, sticky='e')
        full_command = tk.Entry(main_frame, state='readonly', **entry_style)
        full_command.grid(row=3, column=1, pady=5, sticky='w')

        # 5. Botones
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        # Botón para construir comando
        tk.Button(button_frame, text="Construir Comando", 
                command=lambda: _build_at_command(module_var, command_var, params_entry, full_command),
                **button_style).pack(side=tk.LEFT, padx=5)

        # Botón para enviar comando
        tk.Button(button_frame, text="Enviar Comando", 
                command=lambda: _send_at_command(full_command.get(), at_window),
                **button_style).pack(side=tk.LEFT, padx=5)

        # Botón para cerrar
        tk.Button(button_frame, text="Cancelar", 
                command=at_window.destroy,
                bg='gray', fg='white').pack(side=tk.LEFT, padx=5)
        
        def _build_at_command(module_var, command_var, params_entry, full_command):
            """Construye el comando AT completo basado en la selección del módulo y el comando"""
            module = module_var.get()
            command = command_var.get()
            params = params_entry.get().strip()

            if not command:
                messagebox.showwarning("Advertencia", "Por favor selecciona un comando AT.")
                return

            # Construir el comando completo
            if params:
                full_cmd = f"{module[4:]}{command}{params}"
            else:
                full_cmd = f"{module[4:]}{command}"

            full_command.config(state='normal')
            full_command.delete(0, tk.END)
            full_command.insert(0, full_cmd)
            full_command.config(state='readonly')

        def _send_at_command(full_cmd, at_window):
            """Envía el comando AT al módulo LoRa y cierra la ventana"""
            if not full_cmd:
                messagebox.showwarning("Advertencia", "Por favor construye un comando AT antes de enviarlo.")
                return
            if self.ser.is_open:
                try:
                    self.ser.write(full_cmd.encode())
                    print(f"Comando AT enviado: {full_cmd}")
                    messagebox.showinfo("Éxito", "Comando AT enviado correctamente.")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo enviar el comando AT: {e}")
            else:
                messagebox.showerror("Error", "La conexión serial no está abierta.")
            
            at_window.destroy()

    # Envía un mensaje al robot especificado        
    def send_message_to_client(self,id,message):
        def wait_and_send():
            robot = self.robots.get(id)
            lora_obj = self.loras[robot.LoRa]

            # Esperar hasta que el campo respuesta sea True
            if not lora_obj.get_respuesta():
                if message.startswith("/x"):
                    lora_obj.set_respuesta(False)
                else:
                    print(f"Esperando respuesta del LoRa {robot.LoRa} del robot {lora_obj.get_robot_request()} antes de enviar mensaje...")
            start_time = time.time()  # Guarda el tiempo de inicio

            while not lora_obj.get_respuesta():
                # Si han pasado más de 5 segundos, salir del bucle
                if time.time() - start_time > 5:
                    print("Tiempo de espera agotado. No se recibió respuesta en 5 segundos.")
                    break

                # Permitir el envío si el robot que espera es el mismo al que se quiere mandar
                if lora_obj.get_robot_request() == id:
                    print(f"Excepción de espera: el robot {id} está solicitando el mensaje.")
                    break

                time.sleep(0.5)

                
            if self.ser.is_open and not self.mensaje_enviado:
                mensaje = message
                lora_obj.set_respuesta(False)
                if mensaje:
                    # Diferenciar comportamiento según el tipo de robot
                    robot = self.robots.get(id)
                    if robot.LoRa == 2:
                        # Puedes personalizar el mensaje o el manejo aquí si es necesario
                        print(f"Enviando mensaje a {id}: {mensaje}")
                        self.ser.write((f"2AT+SEND={id},{len(mensaje)},{mensaje}").encode())
                    else:
                        print(f"Enviando mensaje a {id}: {mensaje}")
                        self.ser.write((f"1AT+SEND={id},{len(mensaje)},{mensaje}").encode())
                    print(f"Mensaje enviado por la interfaz: {mensaje}")

                    if mensaje.startswith("/x"):
                        self.loras[self.robots[id].LoRa].set_mensajeenviado(True)
                    else:
                        self.loras[self.robots[id].LoRa].set_mensajeenviado(False)
                        self.loras[self.robots[id].LoRa].set_robot_request(id)
                        print(f"Id del robot que solicita el mensaje: {self.loras[self.robots[id].LoRa].get_robot_request()}")

                    if mensaje.startswith("/x") or mensaje.startswith("UR"):
                        self.loras[self.robots[id].LoRa].set_respuesta(True)
                    else:
                        self.loras[self.robots[id].LoRa].set_respuesta(False)
        
        threading.Thread(target=wait_and_send, daemon=True).start()
                
    # Cierra todas las ventanas y gráficos al cerrar la aplicación
    def on_closing(self):
        self.stop()
        plt.close('all')
        self.root.destroy()

    # funcion qie recibe mensajes de los robots y los procesa de acuerdo a su contenido
    def handle_client(self):
        while self.ser.is_open:
            try:
                linea = self.ser.readline().decode().strip()
                line = linea[9:]
                if line:
                    # Verifica si el mensaje es un mensaje recibido por LoRa
                    if line.startswith("+RCV="):
                        datos = line.replace("+RCV=", "").split(",")
                        if len(datos) >= 5:
                            self.respuesta = True
                            address = int(datos[0])
                            longitud = int(datos[1])
                            contenido = datos[2]
                            rssi = int(datos[3])
                            snr = int(datos[4])
                            
                            self.loras[self.robots[address].LoRa].set_respuesta(True)
                            print(f"Respuesta recibida del LoRa {self.robots[address].LoRa} del robot {address} con respuesta: {self.loras[self.robots[address].LoRa].get_respuesta()}")
                            mensaje_descompuesto = (
                                f"Mensaje LoRa recibido:\n"
                                f"Dirección: {address}\n"
                                f"Longitud: {longitud} bytes\n"
                                f"Contenido: {contenido}\n"
                                f"RSSI: {rssi} dBm\n"
                                f"SNR: {snr}\n"
                            )
                            print(mensaje_descompuesto)
                            robot = self.robots[address]
                            if contenido[:2] == "IC": # Iniciar conexión
                                robot.connection(True)
                                messagebox.showinfo(message=f"Robot {address} conectado", title="Conexion")

                            elif contenido[:2] == "CC": # Cerrar conexión
                                self.reset_conf(address, robot)
                                messagebox.showinfo(message=f"Robot {address} desconectado", title="Conexion")
                            elif contenido[:2] == "MS": # Guardar mapa
                               messagebox.showinfo(message="Mapa guardado exitosamente", title="Mapa")

                            elif contenido[:2] == "DS": #Dato sensor 
                                self.add_data(address, contenido, robot)

                            elif contenido[:2] == "AU":  # Actualizar ubicación
                                # Enviar mensaje "UR" y esperar "+OK" antes de actualizar ubicación
                                # self.send_message_to_client(address, "UR")
                                # Esperar a recibir "+OK" antes de continuar
                                self.loras[self.robots[address].LoRa].set_respuesta(False)
                                self.update_location(address, contenido, robot)

                            elif contenido[:2] == "BT": # Actualizar valor de la batería
                                # Buscar valor de batería (BT)
                                bateria_match = re.search(r'BT(\d+(?:\.\d+)?)', contenido)
                                bateria = float(bateria_match.group(1)) if bateria_match else None
                                print(f"Actualizando batería del robot {address} a {bateria}")
                                bat = self.calculate_battery_percentage(bateria)
                                robot.update_battery_level(bat)
                                # Buscar horas (/h)
                                horas_match = re.search(r'/h(\d+)', contenido[2:])
                                horas = int(horas_match.group(1)) if horas_match else None
                                # Buscar minutos (/m)
                                minutos_match = re.search(r'/m(\d+)', contenido[2:])
                                minutos = int(minutos_match.group(1)) if minutos_match else None
                                if horas is not None and minutos is not None:
                                    robot.set_time(horas, minutos)
                                    robot.time_label.config(text=f"Tiempo: {horas:02d}:{minutos:02d}")
                                
                            elif contenido[:2] == "CK": # Actualizar checkpoint
                                ck = contenido[2:]
                                robot.update_ck(ck)

                            elif contenido[:2] == "UL": # Actualizar límites del mapa
                                try:
                                    valores = contenido[2:].split('/')
                                    xmin, xmax, ymin, ymax = map(float, valores)
                                    robot.update_limits(xmin, xmax, ymin, ymax)
                                    print(f"Limites actualizados a: X({xmin}, {xmax}), Y({ymin}, {ymax})")
                                except ValueError:
                                    print(f"Error al actualizar limites: {contenido[2:]}")
                            else:
                                print(f"Comando desconocido para el robot {address}: {contenido}")
                        else:
                            print(f"Serial: (formato inválido): {line}")
                    elif line[9:]=="+OK": 
                        print(f"Mensaje enviado correctamente: {line}")
                        self.mensaje_enviado = False
                    else:
                        print(f"Serial: {line}")

            except Exception as e:
                print(f"Error al leer serial: {e}")
                pass

            time.sleep(0.1)

    # Resetea la configuración del robot y limpia sus datos
    def reset_conf(self, address, robot):
        robot.connection(False)
        if address in self.robots_location:
            messagebox.showinfo(message=f"Robot {address} desconectado", title="Conexion")
        robot.connection(False)
        robot.checkpoints = {}
        robot.medicion = 0
        robot.mediciones = {}
        robot.puntos_muestreo = {}
        robot.update_location(0,0)
        robot.checkpoint = 0
        robot.update_battery_level(0)
        robot.clean()
        robot.update_ck(0)
        robot.reset_time_label()
        robot.loading_window = None
        robot.complete_measurement = False
        robot.in_measurement = False
        robot.posicionm = None
        self.update_robot_position('LR'+str(address), 0, 0)
        lora_obj = self.loras[robot.LoRa]
        lora_obj.set_mensajeenviado(False)
        lora_obj.set_respuesta(False)


    # Agrega los datos de los sensores a la tabla y actualiza el robot
    def add_data(self, address, contenido, robot):
        hora_actual = datetime.now().strftime("%H:%M:%S")
        # Busca todas las coincidencias de dos letras seguidas de un número (entero o decimal)
        datos = re.findall(r'([A-Z]{2})(\d+(?:\.\d+)?)', contenido[2:])
        # Buscar valor de batería (BT)
        bateria_match = re.search(r'BT(\d+(?:\.\d+)?)', contenido)
        bateria = float(bateria_match.group(1)) if bateria_match else None
        # Buscar horas (/h)
        horas_match = re.search(r'/h(\d+)', contenido[2:])
        horas = int(horas_match.group(1)) if horas_match else None
        # Buscar minutos (/m)
        minutos_match = re.search(r'/m(\d+)', contenido[2:])
        minutos = int(minutos_match.group(1)) if minutos_match else None
        resultado = {}

        if bateria is not None:
            bat = self.calculate_battery_percentage(bateria)
            robot.update_battery_level(bat)
        if horas is not None and minutos is not None:
            robot.set_time(horas, minutos)
        for clave, valor in datos:
            if clave in dic.Clave_sensores:
                resultado[clave] = float(valor)

        # Mostrar los valores obtenidos en un messagebox
        if robot.in_measurement == False and robot.complete_measurement == False:
            # Mostrar los valores en columnas, separados por tabulaciones
            col_width = 25  # Ajusta este valor según necesites
            valores_str = f"{'Sensor':<{col_width}}{'Valor':<{col_width}}\n{'-'*(col_width*2)}\n"
            for clave, valor in resultado.items():
                descripcion = dic.Clave_sensores[clave]
                valores_str += f"{descripcion:<{col_width}}{valor:<{col_width}}\n"
            messagebox.showinfo("Valores obtenidos", f"Robot {address}:\n{valores_str}")

        if robot.in_measurement == True and robot.complete_measurement == True:
            messagebox.showinfo(
                    message=f"Medición del CK {robot.checkpoint} completada, enviando al nuevo",
                    title="Medición completada"
                )
            #robot.sent_xy(robot.puntos_muestreo[robot.checkpoint][0],robot.puntos_muestreo[robot.checkpoint][1],0)
            robot.sent_xy(0,0,0)
            robot.loading_window.increment_progress(robot.checkpoint,robot.medicion)
            robot.complete_measurement = True

        #if robot.loading_window and robot.complete_measurement == False and robot.medicion <= robot.n:
        if robot.in_measurement == True and robot.complete_measurement == False:

            for clave, valor in resultado.items():
                print(f"{clave}: {valor}")
                descripcion = dic.Clave_sensores[clave]
                robot.insert_data(hora_actual, descripcion, valor)
                self.general_data_table.insert("", "end", values=(f"{address}", f"{descripcion}", f"{valor}"))

            print(f"CK: {robot.checkpoint}, M: {robot.medicion}")

            robot.increase_measure_count()
            robot.add_event(robot.checkpoint,robot.medicion)
            
            if robot.medicion < robot.n: 
                time.sleep(robot.t)
                self.send_message_to_client(robot.robot_id, "RM")
            else:
                if robot.checkpoint < len(robot.puntos_muestreo):
                    messagebox.showinfo(
                            message=f"Medición del CK {robot.checkpoint} completada, enviando al nuevo",
                            title="Medición completada"
                        )
                    robot.sent_xy(robot.puntos_muestreo[robot.checkpoint][0],robot.puntos_muestreo[robot.checkpoint][1],0)
                    robot.loading_window.Update_ck(robot.checkpoint,robot.medicion)
                    robot.complete_measurement = True
                else:
                    messagebox.showinfo(
                            message=f"Medición del CK {robot.checkpoint} completada, no hay más puntos de muestreo\nRegresando al punto de inicio robot {robot.robot_id}",
                            title=f"Medición completada del robot {robot.robot_id}"
                        )
                    robot.sent_xy(0,0,0)
                    #robot.loading_window.Update_ck(robot.checkpoint,robot.medicion)
                    robot.complete_measurement = False
                    robot.in_measurement == False
                    lora_obj = self.loras[robot.LoRa]
                    lora_obj.set_mensajeenviado(False)
                    lora_obj.set_respuesta(False)
                    robot.complete_measurement = False
                    robot.mediciones = {}
                    robot.checkpoints = {}
                    robot.puntos_muestreo = {}
                    robot.mediciones_completadas = False
        

    #  Actualiza la ubicación del robot y muestra los errores si los hay
    def update_location(self, address, contenido, robot):
        x_match = re.search(r'X(-?\d+(?:\.\d+)?)', contenido)
        x_valor = float(x_match.group(1)) if x_match else None
        print("x:", x_valor, type(x_valor))

        y_match = re.search(r'Y(-?\d+(?:\.\d+)?)', contenido)
        y_valor = float(y_match.group(1)) if y_match else None
        print("y:", y_valor, type(y_valor))

        if contenido[2:4] == "E1":
            print(f"Se recibió el error de ubicación {contenido[2:]}")
            # Obtener la ubicación actual y la esperada
            ubicacion_actual = (x_valor, y_valor)
            if robot.in_measurement == True:
                ubicacion_esperada = robot.puntos_muestreo[robot.checkpoint]
            elif robot.posicionm is not None:
                ubicacion_esperada = robot.posicionm
                #robot.posicionm = None
            elif robot.in_measurement == False:
                ubicacion_esperada = (0, 0)
            else:
                ubicacion_esperada = (None, None)
            mensaje = (
            f"Error de ubicación E1.\n"
            f"Ubicación recibida: {ubicacion_actual}\n"
            f"Ubicación esperada: {ubicacion_esperada}\n"
            "¿Desea reintentar ir a este punto?"
            )
            self.error_function(address, robot, x_valor, y_valor, ubicacion_esperada, mensaje)

        elif contenido[2:4] == "E2":
            print(f"Se recibió el error de ubicación {contenido[2:]}")
        
        elif contenido[2:4] == "E3":
            print(f"Se recibió el error de ubicación {contenido[2:]}")
        
        if isinstance(x_valor, float) and isinstance(y_valor, float) and contenido[2:4] != "E1":
            robot.update_location(x_valor,y_valor)
            robot.eliminar_punto(robot.checkpoint)
            self.update_robot_position('LR'+str(address),x_valor,y_valor)

            if  robot.in_measurement == True and robot.checkpoint == 0 and robot.complete_measurement == False:
                # Si está en medición y es el primer checkpoint, enviar mensaje de medición
                robot.update_ck(robot.checkpoint+1)
                self.send_message_to_client(robot.robot_id, "RM")
                robot.loading_window.Update_ck(robot.checkpoint,robot.medicion)
                print(f"CK: {robot.checkpoint}, M: {robot.medicion}")

            if robot.in_measurement == True and robot.complete_measurement == True:
                robot.restart_measure_count()
                self.send_message_to_client(robot.robot_id, "RM")
                robot.update_ck(robot.checkpoint+1)
                print(f"CK actualizado a {robot.checkpoint}")
                robot.loading_window.Update_ck(robot.checkpoint,robot.medicion)
                robot.complete_measurement = False

            elif robot.in_measurement == True and robot.complete_measurement == False:
                print(f"CK: {robot.checkpoint}, M: {robot.medicion}")
                robot.loading_window.Update_ck(robot.checkpoint,robot.medicion)
                self.send_message_to_client(robot.robot_id, "RM")

            else:
                self.send_message_to_client(robot.robot_id, "UR")
                print(f"Ubicación actualizada del robot {address}: ({x_valor}, {y_valor})")

    def error_function(self, address, robot, x_valor, y_valor, ubicacion_esperada, mensaje):
        if robot.in_measurement == True:
            respuesta = messagebox.askyesnocancel("Error de ubicación", mensaje + "\n\n- Sí para reintentar \n- No para usar la ubicación actual\n- Cancelar y pasar al siguiente CK.")
        if robot.in_measurement == False:
            respuesta = messagebox.askyesnocancel("Error de ubicación", mensaje + "\n\n- Sí para reintentar \n- No para usar la ubicación actual\n- Cancelar y permanecer en la ubicación actual.")
        
        if respuesta is True:
            print("Reintentando ir a la ubicación esperada.")
            if ubicacion_esperada != (None, None):
                self.send_message_to_client(robot.robot_id, f"/x{ubicacion_esperada[0]}/y{ubicacion_esperada[1]}/w0")
            else:
                print("No se pudo determinar la ubicación esperada.")
        elif respuesta is False:
                
            if robot.in_measurement and robot.checkpoint < len(robot.puntos_muestreo):
                print("Usando la ubicación actual como nuevo checkpoint y comenzando mediciones.")
                robot.puntos_muestreo[robot.checkpoint] = (x_valor, y_valor)
                robot.update_location(x_valor, y_valor)
                self.update_robot_position('LR'+str(address),x_valor,y_valor)
                    # Comienza la medición en la nueva ubicación
                self.send_message_to_client(robot.robot_id, "RM")
                robot.update_ck(robot.checkpoint+1)
                print(f"CK actualizado a {robot.checkpoint}")
                robot.restart_measure_count()
                robot.loading_window.Update_ck(robot.checkpoint,robot.medicion)
                robot.complete_measurement = False
            else:
                self.send_message_to_client(robot.robot_id, "UR")
        else:
            print("Envío a posición cancelado.")
                # Si está en proceso de medición, pasar al siguiente checkpoint y marcar como completadas las mediciones
            if robot.in_measurement == False:
                self.send_message_to_client(robot.robot_id, "UR")
            if robot.in_measurement:
                robot.complete_measurement = True
                print(f"CK actualizado a {robot.checkpoint}")
                robot.restart_measure_count()
                print(f"{robot.medicion} mediciones completadas de {robot.n}")
                robot.update_ck(robot.checkpoint + 1)
                robot.loading_window.Update_ck(robot.checkpoint, robot.medicion)
                while robot.medicion < robot.n: 
                    robot.increase_measure_count()
                    robot.add_event(robot.checkpoint,robot.medicion)
                    time.sleep(0.2)

                    # Mandar al robot al siguiente checkpoint
                if robot.checkpoint < len(robot.puntos_muestreo):
                    next_ck = robot.puntos_muestreo[robot.checkpoint]
                    self.send_message_to_client(robot.robot_id, f"/x{next_ck[0]}/y{next_ck[1]}/w0")
        
    # Actualiza la posición de un robot en el mapa general
    def update_robot_position(self,robot_id, x, y):
        if robot_id in self.robots_location:
            self.robots_location[robot_id].set_data([x], [y]) 
            self.robots_location_labels[robot_id].set_position((x, y))
            self.figure.canvas.draw() 
        else:
            print(f"Robot ID {robot_id} no encontrado.")

    def analizar_csv(self, archivo=None):
        """Analiza un archivo CSV y genera un gráfico de puntos con estadísticas"""
        try:
            analizar_csv(archivo)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo analizar el archivo: {e}")

    def calculate_battery_percentage(self, voltage):
        # Asumiendo que el voltaje máximo es 4.2V y el mínimo es 3.0V
        if voltage >= 4.2:
            return 100
        elif voltage <= 3.0:
            #messagebox.showwarning("Advertencia", "Batería muy baja")
            print("Batería muy baja")   
            return 0
        else:
            return (voltage - 3.0) / (4.2 - 3.0) * 100

if __name__ == "__main__":
    app = RobotInterface()
    app.root.mainloop()

