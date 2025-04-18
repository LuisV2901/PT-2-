import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RobotInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interfaz de Control de Robots")
        self.geometry("1000x700")
        self.configure(bg='white')

        # Pestañas para robots y ventana general
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.led_states = {}  # Diccionario para manejar el estado de cada LED
        self.id_robots = [1,2,3,4]
        for i in range(1, 5):
            robot_frame = tk.Frame(self.notebook, bg='white')
            self.notebook.add(robot_frame, text=f"Robot {i}")

            # Barra superior con botones de control
            control_frame = tk.Frame(robot_frame, bg='#002147')
            control_frame.pack(fill='x')
            button_style = {'bg': '#002147', 'fg': 'white'}
            # Crear el Label con el número
            label_numero = tk.Label(control_frame, text=f"{i}", bg='#002147', fg='white', font=("Helvetica", 12))
            label_numero.pack(side='left',padx=20, pady=20)

            tk.Button(control_frame, text="Iniciar Mediciones", command=self.start_measurement, **button_style).pack(side='left', padx=5, pady=5)
            tk.Button(control_frame, text="Regresar Robots", command=self.return_robots, **button_style).pack(side='left', padx=5, pady=5)
            tk.Button(control_frame, text="Solicitar Ubicación", command=self.request_location, **button_style).pack(side='left', padx=5, pady=5)
            tk.Button(control_frame, text="Movimientos Manuales", command=self.manual_movement, **button_style).pack(side='left', padx=5, pady=5)

            # LED (usaremos un Label para simularlo)
            self.led_states[i] = False  # Estado inicial del LED
            led_label = tk.Label(control_frame, text="●", fg="gray", bg='#002147', font=("Helvetica", 20))
            led_label.pack(side='left', padx=5, pady=5)

            # Función para encender/apagar el LED
            def toggle_led(robot_id=i, led_label=led_label):
                self.led_states[robot_id] = not self.led_states[robot_id]
                led_label.config(fg="green" if self.led_states[robot_id] else "gray")
            # Botón para controlar el LED
            tk.Button(control_frame, text="LED", command=toggle_led, **button_style).pack(side='left', padx=5, pady=5)
            
            # Plano cartesiano para visualización de posición
            figure, ax = plt.subplots()
            ax.set_xlim(-30, 30)
            ax.set_ylim(-30, 30)
            ax.plot(0, 0, 'ro')  # Punto rojo en (0,0)
            ax.set_title(f"Posición del Robot {i}")
            ax.set_xlabel("Eje X")
            ax.set_ylabel("Eje Y")
            canvas = FigureCanvasTkAgg(figure, master=robot_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill='both', expand=True, padx=5, pady=5)

            # Tabla de datos por robot
            data_table = ttk.Treeview(robot_frame, columns=("Sensor", "Valor"), show='headings')
            for col in ["Sensor", "Valor"]:
                data_table.heading(col, text=col)
            data_table.pack(fill='both', expand=True, padx=5, pady=5)

        # Ventana General
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
        for col in ["Robot", "Sensor", "Valor"]:
            general_data_table.heading(col, text=col)
        general_data_table.pack(fill='both', expand=True, padx=5, pady=5)

    def start_measurement(self):
        print("Iniciar Mediciones")

    def return_robots(self):
        print("Regresar Robots")

    def request_location(self):
        print("Solicitar Ubicación")

    def manual_movement(self):
        print("Movimientos Manuales")

if __name__ == "__main__":
    app = RobotInterface()
    app.mainloop()
