import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

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
        self.fs = fs

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

        self.modo_edicion = False

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
        self.opcion_trayectoria.set("Zigzag rectangular")
        opciones = ["Espiral cuadrada", "Rejilla horizontal"]
        menu = tk.OptionMenu(self.root, self.opcion_trayectoria, *opciones, command=self._actualizar_grafica)
        menu.grid(row=6, column=1)

        self.label_info = tk.Label(self.root, text="Puntos generados: 0    Distancia total: 0.0")
        self.label_info.grid(row=7, column=0, columnspan=2, sticky="w", pady=5)

        tk.Button(self.root, text="Inicializar Gráfica", command=self._actualizar_grafica).grid(row=8, column=0, columnspan=2)
        self.boton_editar = tk.Button(self.root, text="Editar puntos", command=self._toggle_edicion)
        self.boton_editar.grid(row=9, column=0, columnspan=2)

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
        # self.root.mainloop()

    def _generar_zigzag(self, paso):
        xmin, xmax, ymin, ymax = self.xmin + self.fs, self.xmax - self.fs, self.ymin + self.fs, self.ymax - self.fs
        ruta = [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
        x_izq, x_der = xmin + paso, xmax - paso
        y_bot, y_top = ymin + paso, ymax - paso
        direccion = 'up'
        while x_izq < x_der and y_bot < y_top:
            if direccion == 'up':
                ruta += [(x_izq, y_bot), (x_izq, y_top)]
                x_izq += paso
                direccion = 'down'
            else:
                ruta += [(x_der, y_top), (x_der, y_bot)]
                x_der -= paso
                direccion = 'up'
        return ruta

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
            if tipo == "Zigzag rectangular":
                self.ruta_actual = self._generar_zigzag(paso)
            elif tipo == "Espiral cuadrada":
                self.ruta_actual = self._generar_espiral(paso)
            elif tipo == "Rejilla horizontal":
                self.ruta_actual = self._generar_rejilla_horizontal(paso)

            self.ruta_actual.insert(0, (self.x0, self.y0))
            self.ruta_actual.append((self.xc, self.yc))
            xs, ys = zip(*self.ruta_actual)
            self.ax.clear()
            self.ax.plot(xs, ys, 'k', alpha=0.3)
            self.ax.scatter([self.x0], [self.y0], color='blue', s=60, label='Robot')
            self.ax.scatter([self.xc], [self.yc], color='orange', s=60, label='Central')

            self.ruta_coordenadas = [(self.x0, self.y0)]
            total_puntos = 0
            self.ruta_coordenadas.append((self.ruta_actual[0], self.ruta_actual[1]))
            for i in range(2, len(self.ruta_actual) - 1):
                intermedios = self._puntos_intermedios(self.ruta_actual[i - 1], self.ruta_actual[i], intervalo)
                self.ruta_coordenadas.extend(intermedios)
                total_puntos += len(intermedios)
                if intermedios:
                    xp, yp = zip(*intermedios)
                    self.ax.scatter(xp, yp, color='red', s=10)

            self.ruta_coordenadas.append((self.xc, self.yc))
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

    def _mover_simulacion(self, indice):
        if not self.ruta_coordenadas or indice >= len(self.ruta_coordenadas):
            return
        x, y = self.ruta_coordenadas[indice]
        self.ax.clear()
        xs, ys = zip(*self.ruta_actual)
        self.ax.plot(xs, ys, 'k', alpha=0.3)
        xs_total, ys_total = zip(*self.ruta_coordenadas)
        self.ax.plot(xs_total, ys_total, 'k--', alpha=0.2)
        xs_sim = [p[0] for p in self.ruta_coordenadas[:indice + 1]]
        ys_sim = [p[1] for p in self.ruta_coordenadas[:indice + 1]]
        self.ax.plot(xs_sim, ys_sim, 'b')
        self.ax.scatter([x], [y], color='red', s=50)
        self.ax.scatter([self.x0], [self.y0], color='blue', s=60, label='Robot')
        self.ax.scatter([self.xc], [self.yc], color='orange', s=60, label='Central')
        self.ax.set_xlim(self.xmin - 5, self.xmax + 5)
        self.ax.set_ylim(self.ymin - 5, self.ymax + 5)
        self.ax.set_aspect('equal')
        self.ax.legend()
        self.canvas.draw()
        self.label_posicion.config(text=f"Posición: ({x:.2f}, {y:.2f})")

    def _toggle_edicion(self):
        self.modo_edicion = not self.modo_edicion
        self.boton_editar.config(text="Salir edición" if self.modo_edicion else "Editar puntos")

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
