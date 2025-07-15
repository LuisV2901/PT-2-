import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class EditorPuntosTabla(tk.Toplevel):
    def __init__(self, master, puntos, callback_aplicar, xmin, xmax, ymin, ymax):
        super().__init__(master)
        self.title("Editor de puntos")
        self.geometry("420x320")
        self.puntos = puntos.copy()
        self.callback_aplicar = callback_aplicar
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax

        self.tree = ttk.Treeview(self, columns=("X", "Y"), show="headings", selectmode="browse")
        self.tree.heading("X", text="X")
        self.tree.heading("Y", text="Y")
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<Double-1>", self.editar_celda)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Agregar", command=self.agregar_punto).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Eliminar", command=self.eliminar_punto).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="↑ Subir", command=self.subir_punto).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="↓ Bajar", command=self.bajar_punto).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Aplicar cambios", command=self.aplicar_cambios).pack(side=tk.RIGHT, padx=5)

        self._refrescar()

    def _refrescar(self):
        self.tree.delete(*self.tree.get_children())
        for i, (x, y) in enumerate(self.puntos):
            self.tree.insert("", "end", iid=i, values=(x, y))

    def editar_celda(self, event):
        item = self.tree.identify_row(event.y)
        columna = self.tree.identify_column(event.x)
        if not item or columna not in ("#1", "#2"):
            return
        col_idx = int(columna[1]) - 1
        old_val = self.tree.item(item, "values")[col_idx]
        nuevo = simpledialog.askstring("Editar", f"Nuevo valor para {'X' if col_idx == 0 else 'Y'}:", initialvalue=old_val)
        if nuevo is not None:
            try:
                nuevo = round(float(nuevo), 2)
                x, y = self.puntos[int(item)]
                if col_idx == 0:
                    x = nuevo
                else:
                    y = nuevo
                if not (self.xmin <= x <= self.xmax and self.ymin <= y <= self.ymax):
                    raise ValueError("Punto fuera del área válida")
                if (x, y) in self.puntos and self.puntos[int(item)] != (x, y):
                    raise ValueError("Punto duplicado")
                self.puntos[int(item)] = (x, y)
                self._refrescar()
            except Exception as e:
                messagebox.showerror("Error", f"Valor inválido: {e}")

    def agregar_punto(self):
        try:
            x = round(float(simpledialog.askstring("Agregar punto", "X:")), 2)
            y = round(float(simpledialog.askstring("Agregar punto", "Y:")), 2)
            if not (self.xmin <= x <= self.xmax and self.ymin <= y <= self.ymax):
                raise ValueError("Punto fuera del área válida")
            if (x, y) in self.puntos:
                raise ValueError("Punto duplicado")
            self.puntos.append((x, y))
            self._refrescar()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo agregar el punto: {e}")

    def eliminar_punto(self):
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            del self.puntos[idx]
            self._refrescar()

    def subir_punto(self):
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            if idx > 0:
                self.puntos[idx - 1], self.puntos[idx] = self.puntos[idx], self.puntos[idx - 1]
                self._refrescar()
                self.tree.selection_set(str(idx - 1))

    def bajar_punto(self):
        sel = self.tree.selection()
        if sel:
            idx = int(sel[0])
            if idx < len(self.puntos) - 1:
                self.puntos[idx + 1], self.puntos[idx] = self.puntos[idx], self.puntos[idx + 1]
                self._refrescar()
                self.tree.selection_set(str(idx + 1))

    def aplicar_cambios(self):
        self.callback_aplicar(self.puntos)

class VentanaTrayectorias:
    def __init__(self, master, xmin, xmax, ymin, ymax, x0, y0, xc, yc, fs):
        self.master = master
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.x0 = x0
        self.y0 = y0
        self.xc = xc
        self.yc = yc
        self.fs = 0.2

        self.muestrasn = 0
        self.tiempo = 0
        self.puntos_de_muestreo = []
        self.datos = False

        self.root = tk.Toplevel(master)
        self._crear_ventana()

    def _crear_ventana(self):
        self.root.title("Planeación de muestreo")
        self.ruta_actual = []
        self.ruta_coordenadas = []

        # Entradas
        tk.Label(self.root, text="Cantidad de mediciones por punto (N):").grid(row=2, column=0)
        self.entry_qty = tk.Entry(self.root)
        self.entry_qty.grid(row=2, column=1)

        tk.Label(self.root, text="Tiempo entre mediciones (t):").grid(row=3, column=0)
        self.entry_time = tk.Entry(self.root)
        self.entry_time.grid(row=3, column=1)

        tk.Label(self.root, text="Paso (P):").grid(row=4, column=0)
        self.paso_slider = tk.Scale(self.root, from_=1, to=50, orient=tk.HORIZONTAL, command=self._actualizar_grafica)
        self.paso_slider.grid(row=4, column=1)

        tk.Label(self.root, text="Distancia entre puntos(m):").grid(row=5, column=0)
        self.entry_intervalo = tk.Entry(self.root)
        self.entry_intervalo.insert(0, "25")
        self.entry_intervalo.grid(row=5, column=1)

        tk.Label(self.root, text="Tipo de trayectoria:").grid(row=6, column=0)
        self.opcion_trayectoria = tk.StringVar(self.root)
        self.opcion_trayectoria.set("Espiral cuadrada")
        opciones = ["Linea recta","Espiral cuadrada", "Rejilla horizontal"]
        menu = tk.OptionMenu(self.root, self.opcion_trayectoria, *opciones, command=self._actualizar_grafica)
        menu.grid(row=6, column=1)

        self.label_info = tk.Label(self.root, text="Puntos generados: 0    Distancia total: 0.0")
        self.label_info.grid(row=7, column=0, columnspan=2, sticky="w", pady=5)

        tk.Button(self.root, text="Inicializar Gráfica", command=self._actualizar_grafica).grid(row=8, column=0, columnspan=2)
        tk.Button(self.root, text="Editar puntos", command=self._toggle_edicion).grid(row=9, column=0, columnspan=2)
        tk.Button(self.root, text="Ejecutar", command=self._ejecutar).grid(row=10, column=0, columnspan=2)

        self.slider_simulacion = tk.Scale(self.root, from_=0, to=1, orient=tk.HORIZONTAL, label="Paso de simulación",
                                          command=lambda val: self._mover_simulacion(int(val)))
        self.slider_simulacion.grid(row=11, column=0, columnspan=2)

        self.label_posicion = tk.Label(self.root, text="Posición: -")
        self.label_posicion.grid(row=12, column=0, columnspan=2)

        self.fig, self.ax = plt.subplots(figsize=(5, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().grid(row=0, column=2, rowspan=13, padx=10, pady=10)
        self.canvas.draw()

        self.root.protocol("WM_DELETE_WINDOW", self._cerrar_ventana)

    def _generar_zigzag(self, paso):
        # Genera una trayectoria de línea recta desde la esquina inferior izquierda del área hasta el origen (x0, y0)
        x_inicio, y_inicio = self.xmin + self.fs, self.ymin + self.fs
        return [(x_inicio, y_inicio), (self.x0, self.y0)]

    def _generar_espiral(self, paso):
        xmin, xmax, ymin, ymax = self.xmin + self.fs, self.xmax - self.fs, self.ymin + self.fs, self.ymax - self.fs
        ruta = []
        while xmin <= xmax and ymin <= ymax:
            ruta += [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
            xmin += paso
            xmax -= paso
            ymin += paso
            ymax -= paso
        return ruta

    def _generar_rejilla_horizontal(self, paso):
        xmin, xmax, ymin, ymax = self.xmin + self.fs, self.xmax - self.fs, self.ymin + self.fs, self.ymax - self.fs
        ruta = []
        y = ymin
        izquierda = True
        while y <= ymax:
            if izquierda:
                ruta += [(xmin, y), (xmax, y)]
            else:
                ruta += [(xmax, y), (xmin, y)]
            izquierda = not izquierda
            y += paso
        return ruta

    def _puntos_intermedios(self, p1, p2, n):
        x1, y1 = p1
        x2, y2 = p2
        distancia = np.hypot(x2 - x1, y2 - y1)
        if distancia < n:
            return [(round((x1 + x2) / 2, 2), round((y1 + y2) / 2, 2))]
        cantidad = int(distancia // n)
        return [(round(x1 + t * (x2 - x1), 2), round(y1 + t * (y2 - y1), 2))
                for i in range(1, cantidad + 1)
                if (t := (i * n) / distancia) < 1]

    def _actualizar_grafica(self, *_):
        try:
            paso = self.paso_slider.get()
            intervalo = int(self.entry_intervalo.get())
            tipo = self.opcion_trayectoria.get()

            if tipo == "Linea recta":
                self.ruta_actual = self._generar_zigzag(paso)
            elif tipo == "Espiral cuadrada":
                self.ruta_actual = self._generar_espiral(paso)
            elif tipo == "Rejilla horizontal":
                self.ruta_actual = self._generar_rejilla_horizontal(paso)

            self.ruta_actual.insert(0, (self.x0, self.y0))
            self.ruta_actual.append((self.xc, self.yc))

            self.ax.clear()
            self.ax.plot(*zip(*self.ruta_actual), 'k', alpha=0.3)
            self.ax.scatter([self.x0], [self.y0], color='blue', s=60, label='Robot')
            self.ax.scatter([self.xc], [self.yc], color='orange', s=60, label='Central')

            self.ruta_coordenadas = [self.ruta_actual[0]]
            total_puntos = 0
            for i in range(1, len(self.ruta_actual)):
                intermedios = self._puntos_intermedios(self.ruta_actual[i - 1], self.ruta_actual[i], intervalo)
                self.ruta_coordenadas.extend(intermedios)
                total_puntos += len(intermedios)
                if intermedios:
                    self.ax.scatter(*zip(*intermedios), color='red', s=10)

            self.ruta_coordenadas.append(self.ruta_actual[-1])
            distancia_total = sum(np.hypot(x2 - x1, y2 - y1)
                                  for (x1, y1), (x2, y2) in zip(self.ruta_actual[:-1], self.ruta_actual[1:]))
            self.label_info.config(text=f"Puntos generados: {total_puntos}    Distancia total: {distancia_total:.2f}")
            self.slider_simulacion.config(to=max(1, len(self.ruta_coordenadas) - 1))

            self.ax.set_xlim(self.xmin - 5, self.xmax + 5)
            self.ax.set_ylim(self.ymin - 5, self.ymax + 5)
            self.ax.set_aspect('equal')
            self.ax.legend()
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Entrada inválida: {e}")

    def _toggle_edicion(self):
        if not self.ruta_coordenadas:
            messagebox.showinfo("Sin datos", "Primero genera una trayectoria")
            return

        puntos_a_editar = self.ruta_coordenadas[1:-1]  # sin inicio ni fin

        def aplicar_nuevos_puntos(nuevos_puntos):
            self.ruta_coordenadas = [self.ruta_coordenadas[0]] + nuevos_puntos + [self.ruta_coordenadas[-1]]
            # Actualizar la gráfica solo con los nuevos puntos editados
            self.ax.clear()
            self.ax.plot(*zip(*self.ruta_actual), 'k', alpha=0.3)
            self.ax.plot(*zip(*self.ruta_coordenadas), 'k--', alpha=0.2)
            self.ax.scatter([self.x0], [self.y0], color='blue', s=60, label='Robot')
            self.ax.scatter([self.xc], [self.yc], color='orange', s=60, label='Central')
            if len(self.ruta_coordenadas) > 2:
                self.ax.scatter(*zip(*self.ruta_coordenadas[1:-1]), color='red', s=10)
            self.ax.set_xlim(self.xmin - 5, self.xmax + 5)
            self.ax.set_ylim(self.ymin - 5, self.ymax + 5)
            self.ax.set_aspect('equal')
            self.ax.legend()
            self.canvas.draw()
            self.label_info.config(text=f"Puntos generados: {len(self.ruta_coordenadas)-2}    Distancia total: {sum(np.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(self.ruta_coordenadas[:-1], self.ruta_coordenadas[1:])):.2f}")
            self.slider_simulacion.config(to=max(1, len(self.ruta_coordenadas) - 1))

        EditorPuntosTabla(self.root, puntos_a_editar.copy(), aplicar_nuevos_puntos,
                          self.xmin, self.xmax, self.ymin, self.ymax)
        self.canvas.draw()
        self.label_info.config(text=f"Puntos generados: {len(self.ruta_coordenadas)-2}    Distancia total: {sum(np.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(self.ruta_coordenadas[:-1], self.ruta_coordenadas[1:])):.2f}")
        self.slider_simulacion.config(to=max(1, len(self.ruta_coordenadas) - 1))

    def _mover_simulacion(self, indice):
        if not self.ruta_coordenadas or indice >= len(self.ruta_coordenadas):
            return
        x, y = self.ruta_coordenadas[indice]
        self.ax.clear()
        self.ax.plot(*zip(*self.ruta_actual), 'k', alpha=0.3)
        self.ax.plot(*zip(*self.ruta_coordenadas), 'k--', alpha=0.2)
        self.ax.plot(*zip(*self.ruta_coordenadas[:indice + 1]), 'b')
        self.ax.scatter([x], [y], color='red', s=50)
        self.ax.scatter([self.x0], [self.y0], color='blue', s=60, label='Robot')
        self.ax.scatter([self.xc], [self.yc], color='orange', s=60, label='Central')
        self.ax.set_xlim(self.xmin - 5, self.xmax + 5)
        self.ax.set_ylim(self.ymin - 5, self.ymax + 5)
        self.ax.set_aspect('equal')
        self.ax.legend()
        self.canvas.draw()
        self.label_posicion.config(text=f"Posición: ({x:.2f}, {y:.2f})")

    def _ejecutar(self):
        if not self.ruta_coordenadas or not self.entry_qty.get() or not self.entry_time.get():
            messagebox.showinfo("Sin datos", "Hacen falta datos por llenar")
            return
        self.muestrasn = int(self.entry_qty.get())
        self.tiempo = float(self.entry_time.get())
        self.puntos_de_muestreo = self.ruta_coordenadas[1:-1]
        self._cerrar_ventana()

    def _cerrar_ventana(self):
        plt.close('all')
        self.root.destroy()
