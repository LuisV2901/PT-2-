import socket
import threading
import tkinter as tk
from tkinter import ttk
import pandas as pd
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
    def __init__(self, parent, notebook, robot_id):
        self.parent = parent  # Referencia a la ventana principal, si se necesita
        self.robot_id = robot_id
        self.led_state = False
        # Crear frame para el robot y agregarlo al notebook
        self.frame = tk.Frame(notebook, bg='white')
        notebook.add(self.frame, text=f"Robot {robot_id}")
        # Construir la interfaz del robot
        self.build_ui()
        self.loading_done = False  # Bandera para la condición de carga

    def build_ui(self):
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
        
        tk.Button(control_frame, text="Conectar", command=self.connection, **button_style).pack(side='left', padx=5, pady=5)
        # LED simulado con un Label
        self.led_label = tk.Label(control_frame, text="●", fg="gray", bg='#002147', font=("Helvetica", 20))
        self.led_label.pack(side='left', padx=5, pady=5)
        
        # Canvas de Matplotlib para el plano cartesiano
        figure, ax = plt.subplots()
        ax.set_xlim(-30, 30)
        ax.set_ylim(-30, 30)
        ax.plot(0, 0, 'ro')  # Punto rojo en (0,0)
        ax.set_title(f"Posición del Robot {self.robot_id}")
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        self.canvas = FigureCanvasTkAgg(figure, master=self.frame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tabla de datos para el robot
        self.data_table = ttk.Treeview(self.frame, columns=("Sensor", "Valor"), show='headings')
        for col in ("Sensor", "Valor"):
            self.data_table.heading(col, text=col)
        self.data_table.pack(fill='both', expand=True, padx=5, pady=5)

    def connection(self):
        self.loading_done = False
        self.connection_status = False
        LoadingWindow(self.parent, lambda: self.connection_status)

        threading.Thread(target=self.start_server, daemon=True).start() 
        #self.led_state = not self.led_state
        #self.led_label.config(fg="green" if self.led_state else "gray")

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('localhost', 65432))
        server_socket.listen()
        print("Esperando conexión...")
        client_socket, addr = server_socket.accept()
        print(f"Conectado a {addr}")
        self.connection_status = True
        self.led_label.config(fg="green")
        
    def complete_loading(self):
        
        self.loading_done = True
        print(f"Robot {self.robot_id}: Carga completada.")
    # Métodos de acción que se pueden sobrescribir para cada robot
    def start_measurement(self):
        print(f"Robot {self.robot_id}: Iniciar Mediciones")

    def return_robots(self):
        print(f"Robot {self.robot_id}: Regresar Robots")

    def request_location(self):
        print(f"Robot {self.robot_id}: Solicitar Ubicación")

    def manual_movement(self):
        print(f"Robot {self.robot_id}: Movimientos Manuales")

# Ejemplo de subclase para un robot que se desempeña de manera especial
class RobotEspecial(BaseRobot):
    def start_measurement(self):
        super().start_measurement()
        print(f"Robot Especial {self.robot_id}: Iniciando mediciones con parámetros especiales.")
        # Aquí puedes agregar comportamientos adicionales o específicos

class RobotInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interfaz de Control de Robots")
        self.geometry("1000x700")
        self.configure(bg='white')

        # Notebook para separar cada robot y la ventana general
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.robots = {}  # Diccionario para almacenar las instancias de cada robot
        self.id_robots = [1, 2, 3, 4]
        for i in self.id_robots:
            # En este ejemplo, se utiliza RobotEspecial para los robots pares
            if i % 2 == 0:
                robot = RobotEspecial(self, self.notebook, i)
            else:
                robot = BaseRobot(self, self.notebook, i)
            self.robots[i] = robot

        # Pestaña para la Ventana General
        general_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(general_frame, text="General")

        # Mapa general
        figure, ax = plt.subplots()
        ax.set_xlim(-30, 30)
        ax.set_ylim(-30, 30)
        ax.plot(0, 0, 'ro')  # Punto rojo en (0,0)
        ax.set_title("Mapa General de Sensores")
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        canvas = FigureCanvasTkAgg(figure, master=general_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True, padx=5, pady=5)

        # Tabla de datos general
        general_data_table = ttk.Treeview(general_frame, columns=("Robot", "Sensor", "Valor"), show='headings')
        for col in ("Robot", "Sensor", "Valor"):
            general_data_table.heading(col, text=col)
        general_data_table.pack(fill='both', expand=True, padx=5, pady=5)

if __name__ == "__main__":
    app = RobotInterface()
    app.mainloop()
