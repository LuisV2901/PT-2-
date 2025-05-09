import tkinter as tk
import matplotlib.pyplot as plt
import diccionario_sensores as dic
import csv, re, serial, time, threading
from datetime import datetime
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Clase para la ventana de carga con animación de spinner
class LoadingWindow:
    def __init__(self, parent, condition_func):
        self.parent = parent
        self.condition_func = condition_func  # Función que retorna True cuando se cumple la condición
        self.top = tk.Toplevel(parent)
        self.top.title("Cargando...")
        width, height = 100, 100
        # Calcular la posición para centrar la ventana
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.top.geometry(f"{width}x{height}+{x}+{y}")
        self.top.resizable(False, False)
        self.top.transient(parent)

        self.canvas = tk.Canvas(self.top, width=width, height=height)
        self.canvas.pack()
        # Crear un arco (spinner) de color rojo
        self.arc = self.canvas.create_arc(10, 10, 90, 90, start=0, extent=90, outline="red", width=5, style=tk.ARC)
        self.angle = 0

        self.animate_spinner()

    def animate_spinner(self):
        # Actualiza el ángulo y redibuja el arco
        self.angle = (self.angle + 10) % 360
        self.canvas.itemconfig(self.arc, start=self.angle)
        
        if not self.condition_func():
            # Si la condición no se ha cumplido, programa la siguiente actualización
            self.top.after(50, self.animate_spinner)
        else:
            # Si se cumple la condición, cierra la ventana de carga
            self.top.destroy()

# Clase base para los robots
class BaseRobot:
    def __init__(self, notebook, robot_id, interface):
        self.interface = interface
        self.connection_status = False
        self.robot_id = robot_id
        self.led_state = False
        self.loading_done = False  
        self.location = None
        self.checkpoint = 0
        self.checkpoints = 0
        self.battery = 0
        self.frame = tk.Frame(notebook, bg='white')
        notebook.add(self.frame, text=f"Robot {robot_id}")
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
        
        # LED indicador de conexion
        self.led_label = tk.Label(control_frame, text="●", fg="gray", bg='#002147', font=("Helvetica", 20))
        self.led_label.pack(side='left', padx=5, pady=5)

        # Indicador de bateria
        self.battery_label = tk.Label(control_frame, text="Nivel de batería: 0%", fg="white", bg='#002147', font=("Helvetica", 12))
        self.battery_label.pack(side='right', padx=5, pady=5)
 
        # Canvas de Matplotlib para el plano cartesiano
        self.figure, ax = plt.subplots()
        ax.set_xlim(-30, 30)
        ax.set_ylim(-30, 30)
        self.location, = ax.plot(0, 0, 'ro')
        ax.set_title(f"Posición del Robot {self.robot_id}")
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
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

    # Funciones para actualizar informacion recibida por el robot
    def update_battery_level(self,level):
        self.battery_label.config(text=f"Nivel de batería: {level}%")

    def insert_data(self, Time, Sensor, Value):
        self.data_table.insert("", "end", values=(f"{self.checkpoint}", f"{Time}",f"{Sensor}",f"{Value}"))

    def update_location(self,x,y):
        self.location.set_data([x], [y])  
        self.figure.canvas.draw()  
    
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

    
    # Funciones para solicitar informacion al robot

    def request(self, comando):
        if self.connection_status:
            if comando == "IM":
                print(f"Robot {self.robot_id}: Solicitó Mediciones")
                self.interface.send_message_to_client(self.robot_id,"IM")
            elif comando == "RR":
                print(f"Robot {self.robot_id}: Regresar Robots")
                self.interface.send_message_to_client(self.robot_id,"RR")
            elif comando == "SU":
                print(f"Robot {self.robot_id}: Solicitar Ubicación")
                self.interface.send_message_to_client(self.robot_id,"SU")
            elif comando == "MM":
                print(f"Robot {self.robot_id}: Movimientos Manuales")
                self.interface.send_message_to_client(self.robot_id,"MM")
            elif comando == "CK":
                print(f"Robot {self.robot_id}: Checar conexión")
                self.interface.send_message_to_client(self.robot_id,"CK")
        else:
            messagebox.showwarning("Error", "No hay conexion con el robot")


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

        # Configuración del puerto serial
        SERIAL_PORT = 'COM6'  # Cambia esto según tu sistema
        BAUD_RATE = 115200
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
        ventana = tk.Tk()
        ventana.title("Interfaz de Control")
        
        # Crear un marco para los botones
        frame = tk.Frame(ventana)
        frame.pack(pady=20)

        # Definir comandos de los botones
        def adelante_press(event):
            self.send_message_to_client(f"{robotID}:WO")
            print("Adelante presionado")

        def adelante_release(event):
            self.send_message_to_client(f"{robotID}:WF")
            print("Adelante soltado")

        def atras_press(event):
            self.send_message_to_client(f"{robotID}:SO")
            print("Atrás presionado")

        def atras_release(event):
            self.send_message_to_client(f"{robotID}:SF")
            print("Atrás soltado")

        def giro_derecha_press(event):
            self.send_message_to_client(f"{robotID}:DO")
            print("Giro a la derecha presionado")

        def giro_derecha_release(event):
            self.send_message_to_client(f"{robotID}:DF")
            print("Giro a la derecha soltado")

        def giro_izquierda_press(event):
            self.send_message_to_client(f"{robotID}:AO")
            print("Giro a la izquierda presionado")

        def giro_izquierda_release(event):
            self.send_message_to_client(f"{robotID}:AF")
            print("Giro a la izquierda soltado")

        def alto_press(event):
            self.send_message_to_client(f"{robotID}:TO")
            print("Alto presionado")

        def alto_release(event):
            self.send_message_to_client(f"{robotID}:TF")
            print(f"Conexión movimientos manuales finalizada con robot {robotID}")
            ventana.destroy()

        # Crear botones con texto y colocarlos en forma de cruz
        btn_adelante = tk.Button(frame, text="Adelante", width=10, height=2)
        btn_adelante.grid(row=0, column=1)
        btn_adelante.bind("<ButtonPress>", adelante_press)
        btn_adelante.bind("<ButtonRelease>", adelante_release)

        btn_giro_izquierda = tk.Button(frame, text="Izquierda", width=10, height=2)
        btn_giro_izquierda.grid(row=1, column=0)
        btn_giro_izquierda.bind("<ButtonPress>", giro_izquierda_press)
        btn_giro_izquierda.bind("<ButtonRelease>", giro_izquierda_release)

        btn_alto = tk.Button(frame, text="Alto", width=10, height=2)
        btn_alto.grid(row=1, column=1)
        btn_alto.bind("<ButtonPress>", alto_press)
        btn_alto.bind("<ButtonRelease>", alto_release)

        btn_giro_derecha = tk.Button(frame, text="Derecha", width=10, height=2)
        btn_giro_derecha.grid(row=1, column=2)
        btn_giro_derecha.bind("<ButtonPress>", giro_derecha_press)
        btn_giro_derecha.bind("<ButtonRelease>", giro_derecha_release)

        btn_atras = tk.Button(frame, text="Atrás", width=10, height=2)
        btn_atras.grid(row=2, column=1)
        btn_atras.bind("<ButtonPress>", atras_press)
        btn_atras.bind("<ButtonRelease>", atras_release)

        # Ejecutar la aplicación
        ventana.mainloop()

    def start_connection(self):
        print("Iniciando comunicacion serial con ESP32")
        if not self.ser.is_open:
            self.ser.open()
            print("Conectado al puerto serial\n")
            threading.Thread(target=self.handle_client, daemon=True).start()
            print("Buscando robots conectados")
            self.send_message_to_client(0,"IC")
        else:
            print("Comunicacion con ESP32 ya iniciada")

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
                            elif contenido[:2] == "MM":
                               self.manual_movements_interface(address)
                            elif contenido[:2] == "DS": #Dato sensor 
                                hora_actual = datetime.now().strftime("%H:%M:%S")
                                robot.insert_data(hora_actual,dic.Clave_sensores[f"{contenido[2:4]}"],contenido[4:])
                                clave = contenido[2:4]
                                descripcion = dic.Clave_sensores[clave]
                                self.general_data_table.insert("", "end", values=(f"{address}", f"{descripcion}", f"{contenido[4:]}"))

                            elif contenido[:2] == "AU":
                                x_match = re.search(r'X(-?\d+)', contenido)
                                x_valor = x_match.group(1) if x_match else None
                                
                                y_match = re.search(r'Y(-?\d+)', contenido)
                                y_valor = y_match.group(1) if y_match else None

                                robot.update_location(x_valor,y_valor)
                                self.update_robot_position('LR'+str(address),x_valor,y_valor)
                            else:
                                print(f"Comando desconocido para el robot {address}: {contenido}")

                        else:
                            print(f"ESP32 (formato inválido): {line}")
                    else:
                        print(f"ESP32: {line}")

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
    
    def stop(self):
        print("Cerrando comunicación serial con ESP32")
        if self.ser.is_open:
            self.ser.close()
            print("Conexión cerrada correctamente\n")
        else:
            print("La conexión ya estaba cerrada")


if __name__ == "__main__":

    app = RobotInterface()
    app.root.mainloop()

