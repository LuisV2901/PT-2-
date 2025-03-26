import socket
import threading
import tkinter as tk
from tkinter import ttk
import pandas as pd
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Clase para la ventana de carga con animación de spinner
class LoadingWindow:
    def __init__(self, parent, condition_func):
        self.parent = parent
        self.condition_func = condition_func  # Función que retorna True cuando se cumple la condición
        self.top = tk.Toplevel(parent)
        self.top.title("Cargando...")
        # Tamaño reducido a 100x100 píxeles
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
    def __init__(self, parent, notebook, robot_id, interface):
        self.parent = parent  # Referencia a la ventana principal, si se necesita
        self.robot_id = robot_id
        self.led_state = False
        self.interface = interface
        self.loading_done = False  
        self.location = None
        # Crear frame para el robot y agregarlo al notebook
        self.frame = tk.Frame(notebook, bg='white')
        notebook.add(self.frame, text=f"Robot {robot_id}")
        # Construir la interfaz del robot
        self.robot_panel()

    def robot_panel(self):
        # Barra superior de controles
        control_frame = tk.Frame(self.frame, bg='#002147')
        control_frame.pack(fill='x')
        button_style = {'bg': '#002147', 'fg': 'white'}
        # Label con el número del robot
        label_numero = tk.Label(control_frame, text=f"{self.robot_id}", bg='#002147', fg='white', font=("Helvetica", 12))
        label_numero.pack(side='left', padx=20, pady=20)
        # Botones de acción (llaman a métodos que se pueden sobrescribir)
        tk.Button(control_frame, text="Iniciar Mediciones", command=self.start_measurement, **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(control_frame, text="Regresar Robots", command=self.return_robots, **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(control_frame, text="Solicitar Ubicación", command=self.request_location, **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(control_frame, text="Movimientos Manuales", command=self.manual_movement, **button_style).pack(side='left', padx=5, pady=5)
        tk.Button(control_frame, text="Checar conexión", command=self.check_connection, **button_style).pack(side='left', padx=5, pady=5)
        
        # LED simulado con un Label
        self.led_label = tk.Label(control_frame, text="●", fg="gray", bg='#002147', font=("Helvetica", 20))
        self.led_label.pack(side='left', padx=5, pady=5)
        
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
        self.data_table = ttk.Treeview(self.frame, columns=("Sensor", "Valor"), show='headings')
        for col in ("Sensor", "Valor"):
            self.data_table.heading(col, text=col)
        self.data_table.pack(fill='both', expand=True, padx=5, pady=5)

    def update_location(self,x,y):
        self.location.set_data([x], [y])  # Actualizar las coordenadas del punto
        self.figure.canvas.draw()  # Redibujar el gráfico
    
    def connection(self):
        self.loading_done = False
        self.connection_status = True
        self.led_label.config(fg="green")
    
    # Métodos de acción que se pueden sobrescribir para cada robot
    def start_measurement(self):
        print(f"Robot {self.robot_id}: Solicitó Mediciones")
        self.interface.send_message_to_client(f"{self.robot_id}:IM")
    
    def return_robots(self):
        print(f"Robot {self.robot_id}: Regresar Robots")
        self.interface.send_message_to_client(f"{self.robot_id}:RR")

    def request_location(self):
        print(f"Robot {self.robot_id}: Solicitar Ubicación")
        self.interface.send_message_to_client(f"{self.robot_id}:SU")

    def manual_movement(self):
        print(f"Robot {self.robot_id}: Movimientos Manuales")
        self.interface.send_message_to_client(f"{self.robot_id}:MM")

    def check_connection(self):
        print(f"Robot {self.robot_id}: Checar conexión")
        self.interface.send_message_to_client(f"{self.robot_id}:CC")

# Ejemplo de subclase para un robot que se desempeña de manera especial
class RobotEspecial(BaseRobot):
    def start_measurement(self):
        super().start_measurement()
        print(f"Robot Especial {self.robot_id}: Iniciando mediciones con parámetros especiales.")
        # Aquí puedes agregar comportamientos adicionales o específicos

class RobotInterface():
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Interfaz de Control de Robots")
        self.root.geometry("1000x700")
        self.root.configure(bg='white')
        self.server_socket = None
        self.client_socket = None
        self.addr = None
        # Notebook para separar cada robot y la ventana general
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.robots = {}  # Diccionario para almacenar las instancias de cada robot
        self.id_robots = [1, 2, 3, 4]
        for i in self.id_robots:
            # En este ejemplo, se utiliza RobotEspecial para los robots pares
            if i % 2 == 0:
                robot = RobotEspecial(self, self.notebook, i, self)
            else:
                robot = BaseRobot(self, self.notebook, i, self)
            self.robots[i] = robot

        # Pestaña para la Ventana General
        general_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(general_frame, text="General")
        button_style = {'bg': '#002147', 'fg': 'white'}
        tk.Button(general_frame, text="Iniciar Conexion", command=self.start_connection, **button_style).pack( padx=5, pady=5)
        tk.Button(general_frame, text="Detener Conexion", command=self.stop, **button_style).pack( padx=5, pady=5)
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
        ax.set_title("Mapa General de Sensores")
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        canvas = FigureCanvasTkAgg(self.figure, master=general_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True, padx=5, pady=5)

        # Tabla de datos general
        general_data_table = ttk.Treeview(general_frame, columns=("Robot", "Sensor", "Valor"), show='headings')
        for col in ("Robot", "Sensor", "Valor"):
            general_data_table.heading(col, text=col)
        general_data_table.pack(fill='both', expand=True, padx=5, pady=5)
    def update_robot_position(self,robot_id, x, y):
        if robot_id in self.robots_location:
            self.robots_location[robot_id].set_data([x], [y])  # Actualizar las coordenadas del punto
            self.robots_location_labels[robot_id].set_position((x, y))
            self.figure.canvas.draw()  # Redibujar el gráfico
        else:
            print(f"Robot ID {robot_id} no encontrado.")

        #socket_server.start_server()
    def start_connection(self):
        print("Iniciando comunicacion")
        self.host='localhost' 
        self.port=65432
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Servidor escuchando en {self.host}:{self.port}...")
        
        self.client_socket, self.addr = self.server_socket.accept()  # Espera a que un cliente se conecte
        print(f"Conectado con {self.addr}")
        threading.Thread(target=self.handle_client, args=(self.client_socket,), daemon=True).start()

    def handle_client(self,client_socket):
        try:    
            with client_socket:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    message = data.decode()
                    print(f"Recibido: {message}")
                    # Verifica si el mensaje tiene el formato correcto (ID:COMANDO)

                    robot_id, command = message.split(':')
                    robot_id = int(robot_id.strip())
                    command = command.strip()

                        # Verificar que el ID del robot existe
                    if robot_id in self.robots:
                        robot = self.robots[robot_id]
                            
                        # Llamar a la función correspondiente según el comando
                        if command[:2] == "CC":
                            robot.connection()
                        elif command[:2] == "SU":
                            # Utilizar una expresión regular para encontrar los números
                            coordinates = re.findall(r'\d+', command)
                            x,y = list(map(int, coordinates))
                            robot.update_location(x,y)
                            self.update_robot_position('LR1',x,y)
                            
                        else:
                            print(f"Comando desconocido para el robot {robot_id}: {command}")
                    else:
                        print(f"ID de robot no válido: {robot_id}")
                                             
        except Exception as e:
            print(f"Error en la conexión con el cliente: {e}")
    # Función para enviar mensajes al cliente desde el servidor
    def send_message_to_client(self,message):
        if message:
            self.client_socket.sendall(message.encode())
            print(f"Servidor envió: {message}")
    
    def stop(self):
        self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()

if __name__ == "__main__":

    app = RobotInterface()
    app.root.mainloop()
