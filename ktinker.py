import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class SignedGridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grid con Coordenadas Negativas")
        

        self.grid_range = 25  # Rango en ambas direcciones (positivo y negativo)
        self.cell_size = 30
        self.circle_ratio = 0.25
        

        self.data_points = {}
        
        # Crear marco principal
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Marco de controles (siempre visible)
        self.control_frame = tk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Controles de tamaño
        tk.Label(self.control_frame, text="Tamaño de celda:").pack(side=tk.LEFT)
        self.size_slider = tk.Scale(self.control_frame, from_=20, to=50, orient=tk.HORIZONTAL,
                                  command=self.resize_grid)
        self.size_slider.set(self.cell_size)
        self.size_slider.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Marco para entrada de datos (siempre visible)
        self.entry_frame = tk.Frame(self.main_frame)
        self.entry_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Campos de entrada
        tk.Label(self.entry_frame, text="X:").grid(row=0, column=0)
        self.x_entry = tk.Entry(self.entry_frame, width=5)
        self.x_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(self.entry_frame, text="Y:").grid(row=0, column=2)
        self.y_entry = tk.Entry(self.entry_frame, width=5)
        self.y_entry.grid(row=0, column=3, padx=5)
        
        tk.Label(self.entry_frame, text="Datos:").grid(row=0, column=4)
        self.data_entry = tk.Entry(self.entry_frame, width=20)
        self.data_entry.grid(row=0, column=5, padx=5)
        

        self.save_button = tk.Button(self.main_frame, text="Guardar Datos", command=self.save_data)
        self.save_button.pack(pady=5)

        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        

        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        

        total_size = (2 * self.grid_range + 1) * self.cell_size
        self.canvas = tk.Canvas(self.canvas_frame, bg='white',
                               xscrollcommand=self.h_scroll.set,
                               yscrollcommand=self.v_scroll.set,
                               scrollregion=(0, 0, total_size, total_size))
        
 
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        self.draw_grid()
        

        self.tooltip = None
        self.tooltip_label = None
        self.arrow = None

        self.canvas.bind("<Motion>", self.check_hover)
        self.canvas.bind("<Leave>", self.hide_tooltip)

        self.root.geometry("900x700")
    
    def draw_grid(self):
        """Dibuja el grid en el lienzo."""
        self.canvas.delete("all")
        
        total_cells = 2 * self.grid_range + 1
        total_size = total_cells * self.cell_size
        self.canvas.config(scrollregion=(0, 0, total_size, total_size))

        for i in range(total_cells + 1):

            self.canvas.create_line(i * self.cell_size, 0, 
                                  i * self.cell_size, total_size, 
                                  tags="grid_line")

            self.canvas.create_line(0, i * self.cell_size, 
                                  total_size, i * self.cell_size,
                                  tags="grid_line")
            

            if i % 5 == 0:
                coord = i - self.grid_range
                self.canvas.create_text(i * self.cell_size + self.cell_size//2, 10, 
                                      text=str(coord), font=('Arial', max(8, self.cell_size//6)),
                                      tags="coord_label")
                self.canvas.create_text(10, i * self.cell_size + self.cell_size//2, 
                                      text=str(coord), font=('Arial', max(8, self.cell_size//6)),
                                      tags="coord_label")

        center_pos = self.grid_range * self.cell_size
        self.canvas.create_line(center_pos, 0, center_pos, total_size, 
                              width=2, fill='red', tags="axis")
        self.canvas.create_line(0, center_pos, total_size, center_pos, 
                              width=2, fill='red', tags="axis")

        for (x, y), data in list(self.data_points.items()):
            self.create_circle(x, y, data["data"])
    
    def resize_grid(self, cell_size):
        """Redimensiona el grid según el tamaño de celda seleccionado."""
        self.cell_size = int(cell_size)
        self.draw_grid()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
    def save_data(self):
        """Guarda los datos en la coordenada especificada."""
        try:
            x = int(self.x_entry.get())
            y = int(self.y_entry.get())
            
            if abs(x) > self.grid_range or abs(y) > self.grid_range:
                messagebox.showerror("Error", f"Coordenadas fuera de rango ({-self.grid_range}-{self.grid_range})")
                return
                
            data = self.data_entry.get()
            if not data:
                messagebox.showerror("Error", "Por favor ingrese datos para guardar")
                return
                
            # Guardar o actualizar datos
            if (x, y) not in self.data_points:
                self.create_circle(x, y, data)
            else:
                self.data_points[(x, y)]["data"] = data
                self.canvas.itemconfig(self.data_points[(x, y)]["circle"], fill="lightblue")
            
            messagebox.showinfo("Éxito", f"Datos guardados en ({x}, {y})")
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese coordenadas válidas (números enteros)")
    
    def create_circle(self, x, y, data):
        """Crea un círculo en la posición especificada."""
        circle_size = self.cell_size * self.circle_ratio
        offset = (self.cell_size - circle_size) / 2
        

        canvas_x = (x + self.grid_range) * self.cell_size + offset
        canvas_y = (self.grid_range - y) * self.cell_size + offset
        
        x1 = canvas_x
        y1 = canvas_y
        x2 = x1 + circle_size
        y2 = y1 + circle_size
        
        circle = self.canvas.create_oval(x1, y1, x2, y2, fill="lightblue", 
                                       outline="blue", tags="data_point")
        
        self.data_points[(x, y)] = {
            "data": data,
            "circle": circle,
            "center_x": (x1 + x2) / 2,
            "center_y": (y1 + y2) / 2
        }
    
    def check_hover(self, event):
        """Verifica si el mouse está sobre un círculo de datos."""
        items = self.canvas.find_overlapping(event.x-5, event.y-5, event.x+5, event.y+5)
        self.hide_tooltip()
        
        for item in items:
            tags = self.canvas.gettags(item)
            if "data_point" in tags:
                for coords, point_data in self.data_points.items():
                    if point_data["circle"] == item:
                        self.show_tooltip(point_data["center_x"], point_data["center_y"], 
                                        coords, point_data["data"])
                        break
                break
    
    def show_tooltip(self, circle_x, circle_y, coords, data):
        """Muestra el tooltip sobre el círculo."""
        if self.tooltip is None:
            self.tooltip = tk.Toplevel(self.root)
            self.tooltip.overrideredirect(True)
            self.tooltip.wm_attributes("-topmost", True)
            
            self.tooltip_frame = tk.Frame(self.tooltip, bg='lightyellow', bd=2, relief='solid')
            self.tooltip_frame.pack(fill='both', expand=True)
            
            self.tooltip_label = tk.Label(self.tooltip_frame, text="", 
                                         bg='lightyellow', justify=tk.LEFT,
                                         wraplength=400)
            self.tooltip_label.pack(padx=5, pady=5)
            
            self.arrow = self.canvas.create_line(0, 0, 0, 0, arrow='last', 
                                               width=max(2, self.cell_size//20), 
                                               fill='black')
        
        
        full_text = f"Coordenada: ({coords[0]}, {coords[1]})\nDatos: {data}"
        self.tooltip_label.config(text=full_text, font=('Arial', 10))
        
        # Calcular tamaño necesario
        self.tooltip.update_idletasks()
        req_width = self.tooltip_label.winfo_reqwidth() + 20
        req_height = self.tooltip_label.winfo_reqheight() + 20

        canvas_x = self.canvas.canvasx(circle_x)
        canvas_y = self.canvas.canvasy(circle_y)   

        tooltip_x = self.canvas.winfo_rootx() + int(canvas_x) - req_width//2
        tooltip_y = self.canvas.winfo_rooty() + int(canvas_y) - req_height - 10

        if tooltip_y < 0:
            tooltip_y = self.canvas.winfo_rooty() + int(canvas_y) + 20

        self.tooltip.geometry(f"{req_width}x{req_height}+{tooltip_x}+{tooltip_y}")
        self.tooltip.deiconify()

        arrow_end_x = circle_x
        arrow_end_y = circle_y
        
        arrow_start_x = arrow_end_x
        if tooltip_y < self.canvas.winfo_rooty() + canvas_y:
            arrow_start_y = arrow_end_y - req_height
        else:
            arrow_start_y = arrow_end_y + 20
        
        self.canvas.coords(self.arrow, arrow_start_x, arrow_start_y, arrow_end_x, arrow_end_y)
        
        self.current_tooltip = self.tooltip
    
    def hide_tooltip(self, event=None):
        """Oculta el tooltip y la flecha."""
        if self.tooltip:
            self.tooltip.withdraw()
        if self.arrow:
            self.canvas.coords(self.arrow, 0, 0, 0, 0)
        self.current_tooltip = None

if __name__ == "__main__":
    root = tk.Tk()
    app = SignedGridApp(root)
    root.mainloop()