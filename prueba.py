import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class App:
    def __init__(self, root):
        self.root = root
        self.frame = ttk.Frame(root)
        self.frame.pack(fill='both', expand=True)

        # Crear el Treeview con scrollbar
        self.data_table = ttk.Treeview(self.frame, columns=("Checkpoint", "Hora", "Sensor", "Valor"), show='headings', height=10)
        for col in ("Checkpoint", "Hora", "Sensor", "Valor"):
            self.data_table.heading(col, text=col)
        
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.data_table.yview)
        self.data_table.configure(yscrollcommand=scrollbar.set)
        
        self.data_table.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')

        # Crear el botón para cambiar a gráficos
        self.change_button = ttk.Button(root, text="Cambiar a gráficos", command=self.toggle_view)
        self.change_button.pack(pady=10)

        self.graph_frame = None

    def show_graph(self):
        # Crear un nuevo frame para el gráfico
        self.graph_frame = ttk.Frame(self.root)
        self.graph_frame.pack(fill='both', expand=True)

        # Crear una gráfica de barras con 6 barras
        fig, ax = plt.subplots()
        ax.bar([1, 2, 3, 4, 5, 6], [10, 20, 30, 40, 50, 60])
        ax.set_title('Gráfico con 6 barras')
        
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side='left', fill='both', expand=True, padx=5, pady=5)

    def toggle_view(self):
        if self.data_table.winfo_ismapped():
            # Cambiar a gráfico
            self.data_table.pack_forget()
            self.show_graph()
            self.change_button.config(text="Regresar a la tabla")
        else:
            # Cambiar a tabla
            self.graph_frame.pack_forget()
            self.graph_frame.destroy()
            self.data_table.pack(side='left', fill='both', expand=True, padx=5, pady=5)
            self.change_button.config(text="Cambiar a gráficos")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()