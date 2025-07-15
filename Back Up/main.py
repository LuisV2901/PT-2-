import tkinter as tk
import matplotlib.pyplot as plt
import diccionario_sensores as dic
import csv, re, serial, time, threading
from datetime import datetime
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from progress import LoadingWindow
import Interfaz_trayectorias

# Clase base para los robots
class BaseRobot:
    def __init__(self, notebook, robot_id, interface):
        self.interface = interface
        self.led_state = False
        self.loading_window = None  
        self.checkpoints = {}
        self.medicion = 0
        self.mediciones = {}
        self.puntos_muestreo = {}
        self.frame = tk.Frame(notebook, bg='white')
        notebook.add(self.frame, text=f"Robot {robot_id}")
        self.ax = None
        self.n = 0
        self.t = 0
        #Información general
        self.connection_status = False
        self.robot_id = robot_id
        self.location = None
        self.checkpoint = 0
        self.battery = 0
        
        self.robot_panel()

    def robot_panel(self):
        # Barra superior de controles
        control_frame = tk.Frame(self.frame, bg='#002147')
        control_frame.pack(fill='x')
        button_style = {'bg': '#002147', 'fg': 'white'}
        # Label con el número del robot
        label_numero = tk.Label(control_frame, text=f"{self.robot_id}", bg='#002147', fg='white', font=("Helvetica", 12))
        label_numero.pack(side='left', padx=20, pady=20)
        
        tk.Button(control_frame, text="Iniciar Mediciones", command=lambda: self.request("IM"),  **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(control_frame, text="Regresar Robot", command=lambda: self.request("RR"), **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(control_frame, text="Solicitar Ubicación", command=lambda: self.request("SU"), **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(control_frame, text="Movimientos Manuales", command=lambda: self.request("MM"), **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(control_frame, text="Información", command=lambda: self.request("CK"), **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(control_frame, text="Cerrar conexión", command=lambda: self.request("CC"), **button_style).pack(side='left', padx=5, pady=5)
        
        # LED indicador de conexion
        self.led_label = tk.Label(control_frame, text="●", fg="gray", bg='#002147', font=("Helvetica", 20))
        self.led_label.pack(side='left', padx=5, pady=5)

        # Indicador de bateria
        self.battery_label = tk.Label(control_frame, text="Nivel de batería: 0%", fg="white", bg='#002147', font=("Helvetica", 12))
        self.battery_label.pack(side='right', padx=5, pady=5)
 
        # Canvas de Matplotlib para el plano cartesiano
        self.figure, self.ax = plt.subplots()
        self.ax.set_xlim(-30, 30)
        self.ax.set_ylim(-30, 30)
        self.location, = self.ax.plot(0, 0, 'ro')
        self.ax.set_title(f"Posición del Robot {self.robot_id}")
        self.ax.set_xlabel("Eje X")
        self.ax.set_ylabel("Eje Y")
        canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True, padx=5, pady=5)

    # Tabla de datos para el robot
        # Crear un Treeview con scrollbar
        self.data_table = ttk.Treeview(self.frame, columns=("Checkpoint", "Hora", "Sensor", "Valor"), show='headings', height=10)
        for col in ("Checkpoint", "Hora", "Sensor", "Valor"):
            self.data_table.heading(col, text=col)
        
        # Crear scrollbar vertical
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.data_table.yview)
        self.data_table.configure(yscrollcommand=scrollbar.set)
        
        self.data_table.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

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
        btn_savemap = tk.Button(
            footer_frame,
            text="Guardar mapa",
            command=self.savemap, 
            bg='#002147',
            fg='white',
            font=("Helvetica", 10, "bold")
        )
        btn_savemap.pack(pady=5)
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
        self.battery_label.config(text=f"Nivel de batería: {level}%")
    
    def increase_measure_count(self):
        self.medicion+=1

    def restart_measure_count(self):
        self.medicion = 0

    def insert_data(self, Time, Sensor, Value):
        self.data_table.insert("", "end", values=(f"{self.checkpoint}", f"{Time}",f"{Sensor}",f"{Value}"))

    def update_location(self,x,y):
        self.location.set_data([x], [y])  
        self.figure.canvas.draw()  

    def sent_xy(self,x,y,w):
        print(f"Mandando CK {self.checkpoint} con destino a X:{x} Y:{y}")
        message = f"NC/x{x}/y{y}/w{w}"
        self.interface.send_message_to_client(self.robot_id,message)

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
                writer.writerow(["========================"])
                writer.writerow(columns)
                    
                for row_id in self.data_table.get_children():
                    row = self.data_table.item(row_id)['values']
                    writer.writerow(row)
                print(f"Archivo {nombre}.csv generado con exito")
            forms.destroy()

        tk.Button(forms, text="Aceptar", command=generate_report, bg='#002147', fg='white').pack(pady=10)

    # Funciones para solicitar informacion al robot
    def request(self, comando):
        if self.connection_status:
            if comando == "IM":
                print(f"Robot {self.robot_id}: Solicitó Mediciones")
                self.n = 0
                self.t = 0
                Trayectoria = Interfaz_trayectorias.VentanaTrayectorias(
                    master=self.frame,
                    xmin=-100, xmax=0, ymin=-100, ymax=0,
                    x0=-50, y0=-20, xc=-50, yc=0,
                    fs=10
                )
                                
                Trayectoria.root.wait_window()
                
                self.n = Trayectoria.muestrasn
                self.t = Trayectoria.tiempo
                self.puntos_muestreo = Trayectoria.puntos_de_muestreo
                for i, punto in enumerate(self.puntos_muestreo):
                    print(f"Checkpoint: {i}, Punto: ({punto[0]:.2f}, {punto[1]:.2f})")
                self.loading_window = LoadingWindow(self.frame,len(self.puntos_muestreo),self.n)
                print(f"Tiempo total de muestreo {len(self.puntos_muestreo)*self.t*self.n} segundos")
                self.sent_xy(self.puntos_muestreo[self.checkpoint][0],self.puntos_muestreo[self.checkpoint][1],0)
            elif comando == "RR":
                print(f"Robot {self.robot_id}: Regresar Robot")
                self.interface.send_message_to_client(self.robot_id,"/x0/y0/w0")
            elif comando == "SU":
                print(f"Robot {self.robot_id}: Solicitar Ubicación")
                self.interface.send_message_to_client(self.robot_id,"SU")
            elif comando == "MM":
                print(f"Robot {self.robot_id}: Movimientos Manuales")
                        # Crear ventana principal
                ventana = tk.Tk()
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
                        print("Valores enviados correctamente.")
                    except ValueError:
                        messagebox.showerror("Error", "Por favor ingresa solo números.")

                def abrir_ventana_direcciones():
                    ventana_direcciones = tk.Toplevel(ventana)
                    ventana_direcciones.title("Control de Direcciones")

                    def enviar_direccion(direccion):
                        self.interface.send_message_to_client(self.robot_id, f"/{direccion}")

                    # Crear botones en forma de cruz
                    tk.Button(ventana_direcciones, text="↑ Delante", width=12,
                            command=lambda: enviar_direccion("q")).grid(row=0, column=1, pady=5)
                    tk.Button(ventana_direcciones, text="← Izquierda", width=12,
                            command=lambda: enviar_direccion("a")).grid(row=1, column=0, padx=5)
                    tk.Button(ventana_direcciones, text="→ Derecha", width=12,
                            command=lambda: enviar_direccion("d")).grid(row=1, column=2, padx=5)
                    tk.Button(ventana_direcciones, text="↓ Atrás", width=12,
                            command=lambda: enviar_direccion("s")).grid(row=2, column=1, pady=5)

                # Botones
                tk.Button(ventana, text="Aceptar", command=obtener_valores).grid(row=3, column=0, pady=10)
                tk.Button(ventana, text="Direcciones", command=abrir_ventana_direcciones).grid(row=3, column=1, pady=10)

                ventana.mainloop()
            elif comando == "CK":
                print(f"Robot {self.robot_id}: Checar conexión")
                self.interface.send_message_to_client(self.robot_id,"CK")
            elif comando == "CC":
                print(f"Robot {self.robot_id}: Cerrando conexión")
                self.interface.send_message_to_client(self.robot_id,"CC")
        else:
            messagebox.showwarning("Error", "No hay conexion con el robot")
    def add_event(self,ck,num):
        if self.loading_window:
            self.loading_window.increment_progress(ck,num)


# Subclase para un robot que se desempeña de manera especial
class RobotEspecial(BaseRobot):
    def start_measurement(self):
        super().start_measurement()
        print(f"Robot Especial {self.robot_id}: Iniciando mediciones con parámetros especiales.")
       
class RobotInterface():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Panel de control para Robots")
        self.root.geometry("1000x700")
        self.root.configure(bg='white')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Configuración del puerto serial
        SERIAL_PORT = "" 
        BAUD_RATE = 115200
        self.configuration = False
        self.ser = serial.Serial()
        self.ser.port = SERIAL_PORT
        self.ser.baudrate = BAUD_RATE
        self.ser.timeout = 1
        # Notebook para separar cada robot y la ventana general
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.robots = {}  # Diccionario para almacenar las instancias de cada robot
        self.id_robots = [1, 2, 3, 4]
        for i in self.id_robots:
            # En este ejemplo, se utiliza RobotEspecial para los robots pares
            if i % 2 == 0:
                robot = RobotEspecial(self.notebook, i, self)
            else:
                robot = BaseRobot(self.notebook, i, self)
            self.robots[i] = robot

        # Pestaña para la Ventana General
        general_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(general_frame, text="General")
        button_style = {'bg': '#002147', 'fg': 'white'}
        tk.Button(general_frame, text="Iniciar Conexion", command=self.start_connection, **button_style).pack( padx=5, pady=5)
        tk.Button(general_frame, text="Detener Conexion", command=self.stop, **button_style).pack( padx=5, pady=5)

        tk.Label(general_frame, text="Puerto Serial:", bg='white').pack(pady=(10, 0))
        self.port_entry = tk.Entry(general_frame)
        self.port_entry.pack(pady=5)

        tk.Label(general_frame, text="Baudios:", bg='white').pack(pady=(10, 0))
        self.baud_entry = tk.Entry(general_frame)
        self.baud_entry.pack(pady=5)

        # Mapa general
        self.figure, ax = plt.subplots()
        ax.set_xlim(-30, 30)
        ax.set_ylim(-30, 30)
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
        ax.set_title("Mapa General de Robots")
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        canvas = FigureCanvasTkAgg(self.figure, master=general_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True, padx=5, pady=5)

        # Tabla de datos general
        self.general_data_table = ttk.Treeview(general_frame, columns=("Robot", "Sensor", "Valor"), show='headings')
        for col in ("Robot", "Sensor", "Valor"):
            self.general_data_table.heading(col, text=col)
        self.general_data_table.pack(fill='both', expand=True, padx=5, pady=5)

        footer_frame = tk.Frame(general_frame, bg='white')
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

            tk.Label(forms, text="Autor:", bg='white').pack(pady=(10, 0))
            entry_autor = tk.Entry(forms, width=30)
            entry_autor.pack()

            tk.Label(forms, text="Comentarios:", bg='white').pack(pady=(10, 0))
            entry_comentarios = tk.Text(forms, width=30, height=4)
            entry_comentarios.pack()

            # Botón de enviar
            def generate_report():
                nombre = entry_nombre.get()
                autor = entry_autor.get()
                comentarios = entry_comentarios.get("1.0", "end").strip()
                columns = self.data_table["columns"]
                    # Abrir el archivo CSV para escritura
                with open(f"{nombre} robot {self.robot_id}.csv", mode='w', newline='') as file:

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
            
    def update_robot_position(self,robot_id, x, y):
        if robot_id in self.robots_location:
            self.robots_location[robot_id].set_data([x], [y]) 
            self.robots_location_labels[robot_id].set_position((x, y))
            self.figure.canvas.draw() 
        else:
            print(f"Robot ID {robot_id} no encontrado.")

    def manual_movements_interface(self, robotID):
        print(f"Conexión movimientos manuales inciado con robot {robotID}")

    def start_connection(self):
        print("Iniciando comunicacion serial")
        if not self.ser.is_open and self.configuration == False:
            self.ser.port = self.port_entry.get()
            self.ser.open()
            print("Conectado al puerto serial\n")
            # Esperar a que llegue "READY" del ESP32
            ready = ""
            while "READY" not in ready:
                if self.ser.in_waiting:
                    ready += self.ser.read(self.ser.in_waiting).decode(errors="ignore")
                time.sleep(0.1)
            time.sleep(2)
            print("LoRa configurado")
            threading.Thread(target=self.handle_client, daemon=True).start()
            print("Buscando robots conectados")
            # Crear ventana con botones
            self.configuration = True
            self.show_robot_buttons()
        else:
            self.show_robot_buttons()


    def show_robot_buttons(self):
        button_window = tk.Toplevel(self.root)  # Asegúrate de que self.parent es tu ventana principal (tk.Tk())
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

    def handle_client(self):
        while self.ser.is_open:
            try:
                line = self.ser.readline().decode().strip()
                if line:
                    # Verifica si el mensaje es un mensaje recibido por LoRa
                    if line.startswith("+RCV="):
                        datos = line.replace("+RCV=", "").split(",")
                        if len(datos) >= 5:
                            address = int(datos[0])
                            longitud = int(datos[1])
                            contenido = datos[2]
                            rssi = int(datos[3])
                            snr = int(datos[4])

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
                            if contenido[:2] == "IC":
                                robot.connection(True)
                                messagebox.showinfo(message=f"Robot {address} conectado", title="Conexion")
                            elif contenido == "CC":
                                robot.connection(False)
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
                            elif contenido[:2] == "MM":
                               self.manual_movements_interface(address)
                            elif contenido[:2] == "MS":
                               messagebox.showinfo(message="Mapa guardado exitosamente", title="Mapa")
                            elif contenido[:2] == "DS": #Dato sensor 
                                hora_actual = datetime.now().strftime("%H:%M:%S")
                                # Busca todas las coincidencias de dos letras seguidas de un número (entero o decimal)
                                datos = re.findall(r'([A-Z]{2})(\d+(?:\.\d+)?)', contenido[2:])
                                resultado = {clave: float(valor) if '.' in valor else int(valor) for clave, valor in datos}
                                # Mostrar resultados
                                for clave, valor in resultado.items():
                                    if robot.loading_window:
                                        print(f"CK: {robot.checkpoint}, M: {robot.medicion}") 
                                    print(f"{clave}: {valor}")
                                    descripcion = dic.Clave_sensores[clave]
                                    robot.insert_data(hora_actual,descripcion,valor)
                                    self.general_data_table.insert("", "end", values=(f"{address}", f"{descripcion}", f"{valor}"))
                                robot.increase_measure_count()
                                robot.add_event(robot.checkpoint,robot.medicion)
                                if robot.medicion == robot.n:
                                    if robot.loading_window:
                                        print(f"Medición del CK {robot.checkpoint} completado, enviando al nuevo")
                                        robot.restart_measure_count()
                                        robot.sent_xy(robot.puntos_muestreo[robot.checkpoint][0],robot.puntos_muestreo[robot.checkpoint][1],0)
                                        robot.loading_window.increment_progress(robot.checkpoint,robot.medicion)

                            elif contenido[:2] == "AU":
                                x_match = re.search(r'X(-?\d+)', contenido)
                                x_valor = int(x_match.group(1)) if x_match else None
                                print(x_valor)
                                y_match = re.search(r'Y(-?\d+)', contenido) 
                                y_valor = int(y_match.group(1)) if y_match else None
                                print(y_valor)
                                if contenido[2] == "E1":
                                    print(f"Se recibió el error de ubicación {contenido[2:]}")
                                elif contenido[2] == "E2":
                                    print(f"Se recibió el error de ubicación {contenido[2:]}")
                                elif contenido[2] == "E3":
                                    print(f"Se recibió el error de ubicación {contenido[2:]}")
                                if x_valor and y_valor :
                                    robot.update_location(x_valor,y_valor)
                                    self.update_robot_position('LR'+str(address),x_valor,y_valor)
                                    if robot.loading_window:
                                        robot.update_ck(robot.checkpoint+1)
                                        robot.loading_window.Update_ck(robot.checkpoint,robot.medicion)

                            elif contenido[:2] == "BT":
                                level = contenido[2:] 
                                robot.update_battery_level(level)
                            elif contenido[:2] == "CK":
                                ck = contenido[2:]
                                robot.update_ck(ck)
                            else:
                                print(f"Comando desconocido para el robot {address}: {contenido}")

                        else:
                            print(f"Serial: (formato inválido): {line}")
                    else:
                        print(f"Serial: {line}")
                        if line == "+ERR=12":
                            self.ser.write((f"AT+SEND?").encode())    
            except Exception as e:
                print(f"Error al leer serial: {e}")
                pass

            time.sleep(0.1)
        
    def send_message_to_client(self,id,message):
        if self.ser.is_open:
            mensaje = message
            if mensaje:
                self.ser.write((f"AT+SEND={id},{len(mensaje)},{mensaje}").encode())
                print(f"Mensaje enviado por la interfaz: {mensaje}")
    def on_closing(self):
        plt.close('all')
        self.root.destroy()

    def stop(self):
        print("Cerrando comunicación serial")
        if self.ser.is_open:
            for robot in self.robots:
                self.robots[robot].connection(False)
            self.ser.close()
            print("Conexión cerrada correctamente\n")
        else:
            print("La conexión ya estaba cerrada")


if __name__ == "__main__":

    app = RobotInterface()
    app.root.mainloop()

