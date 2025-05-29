import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def iniciar_interfaz_trayectorias(xmin, xmax, ymin, ymax, x0, y0, xc, yc,fs):
    modo_edicion = False
    ruta_actual = []
    coordenadas = []
    ruta_coordenadas = []
    Qty = 0
    t = 0

    def ejecutar():
        nonlocal Qty, t
        if not ruta_coordenadas or not entry_qty.get() or not entry_time.get():
            messagebox.showinfo("Sin datos", "Hacen falta datos por llenar")
            return
        texto = "\n".join([f"({x:.2f}, {y:.2f})" for x, y in ruta_coordenadas])
        messagebox.showinfo("Puntos generados", f"Total: {len(ruta_coordenadas)} puntos\n\n{texto}")
        Qty = entry_qty.get()
        t = entry_time.get()
        root.destroy()
        plt.close('all')
    
    def puntos():
        return ruta_coordenadas[1:-1]
    
    def obtener_parametros():
        return Qty, t

    def generar_zigzag(xmin, xmax, ymin, ymax, paso):
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

    def generar_espiral(xmin, xmax, ymin, ymax, paso):
        ruta = []
        while xmin <= xmax and ymin <= ymax:
            ruta += [(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)]
            xmin += paso
            xmax -= paso
            ymin += paso
            ymax -= paso
        return ruta

    def generar_rejilla_horizontal(xmin, xmax, ymin, ymax, paso):
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

    def puntos_intermedios(p1, p2, n):
        x1, y1 = p1
        x2, y2 = p2
        distancia = np.hypot(x2 - x1, y2 - y1)
        if distancia < n:
            xm = (x1 + x2) / 2
            ym = (y1 + y2) / 2
            return [(float(xm), float(ym))]
        cantidad = int(distancia // n)
        return [(float(x1 + t * (x2 - x1)), float(y1 + t * (y2 - y1)))
            for i in range(1, cantidad + 1)
            if (t := (i * n) / distancia) < 1]

    def actualizar_grafica(*args):
        nonlocal ruta_actual
        nonlocal coordenadas
        nonlocal ruta_coordenadas
        try:
            xmin_val = xmin
            xmax_val = xmax
            ymin_val = ymin
            ymax_val = ymax
            paso = paso_slider.get()
            intervalo = int(entry_intervalo.get())

            tipo = opcion_trayectoria.get()

            if tipo == "Zigzag rectangular":
                ruta_actual = generar_zigzag(xmin_val+fs, xmax_val-fs, ymin_val+fs, ymax_val-fs, paso)
            elif tipo == "Espiral cuadrada":
                ruta_actual = generar_espiral(xmin_val+fs, xmax_val-fs, ymin_val+fs, ymax_val-fs, paso)
            elif tipo == "Rejilla horizontal":
                ruta_actual = generar_rejilla_horizontal(xmin_val+fs, xmax_val-fs, ymin_val+fs, ymax_val-fs, paso)


            ruta_actual.insert(0, (x0, y0))
            ruta_actual.append((xc, yc))
            xs, ys = zip(*ruta_actual)
            ax.clear()
            ax.plot(xs, ys, 'k', alpha=0.3)
            ax.scatter([x0], [y0], color='blue', s=60, label='Inicio')
            ax.scatter([xc], [yc], color='orange', s=60, label='Central')

            total_puntos = 0
            coordenadas = []

            for i in range(2, len(ruta_actual)-1):
                puntos = puntos_intermedios(ruta_actual[i - 1], ruta_actual[i], intervalo)
                if puntos:
                    xp, yp = zip(*[(round(x, 2), round(y, 2)) for x, y in puntos])
                    ax.scatter(xp, yp, color='red', s=10)
                    coordenadas.append((xp, yp))
                    total_puntos += len(puntos)
            
            ruta_coordenadas = []
            ruta_coordenadas.insert(0, (x0, y0))
            for par in coordenadas:
                for x, y in zip(par[0], par[1]):
                    ruta_coordenadas.append((x, y))
            ruta_coordenadas.append((xc, yc))
                    
            ax.set_xlim(xmin_val - 5, xmax_val + 5)
            ax.set_ylim(ymin_val - 5, ymax_val + 5)
            ax.set_aspect('equal')
            ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2)
            canvas.draw()

            distancia_total = sum(np.hypot(ruta_actual[i][0] - ruta_actual[i - 1][0], ruta_actual[i][1] - ruta_actual[i - 1][1]) for i in range(1, len(ruta_actual)))
            label_info.config(text=f"Puntos generados: {total_puntos}    Distancia total: {distancia_total:.2f}")

            slider_simulacion.config(to=max(1, len(ruta_coordenadas) - 1))

        except Exception as e:
            messagebox.showerror("Error", f"Entrada inválida: {e}")

    def mover_simulacion(indice):

        if not ruta_coordenadas or indice >= len(ruta_coordenadas):
            return
        ax.clear()
        xs, ys = zip(*ruta_actual)
            
        ax.plot(xs, ys, 'k', alpha=0.3)
        xs_total, ys_total = zip(*ruta_coordenadas)
        ax.plot(xs_total, ys_total, 'k--', alpha=0.2)

        xs_sim = [p[0] for p in ruta_coordenadas[:indice + 1]]
        ys_sim = [p[1] for p in ruta_coordenadas[:indice + 1]]
        ax.plot(xs_sim, ys_sim, 'b')

        x, y = ruta_coordenadas[indice]
        ax.scatter([x], [y], color='red', s=50)

        ax.scatter([x0], [y0], color='blue', s=60, label='Inicio')
        ax.scatter([xc], [yc], color='orange', s=60, label='Central')
        ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2)

        label_posicion.config(text=f"Posición: ({x:.2f}, {y:.2f})")

        ax.set_xlim(int(xmin) - 5, int(xmax) + 5)
        ax.set_ylim(int(ymin) - 5, int(ymax) + 5)
        ax.set_aspect('equal')
        ax.legend()
        canvas.draw()

    def toggle_edicion():
        nonlocal modo_edicion
        modo_edicion = not modo_edicion
        boton_editar.config(text="Salir edición" if modo_edicion else "Editar puntos")
    
    def on_closing():
        plt.close('all')
        root.destroy()
    root = tk.Tk()
    root.title("Trayectorias sobre Plano")


    tk.Label(root, text="Cantidad de mediciones por punto (N):").grid(row=2, column=0, pady=5)
    entry_qty = tk.Entry(root)
    entry_qty.grid(row=2, column=1)

    tk.Label(root, text="Tiempo entre mediciones (t):").grid(row=3, column=0, pady=5)
    entry_time = tk.Entry(root)
    entry_time.grid(row=3, column=1)


    tk.Label(root, text="Paso (P):").grid(row=4, column=0, pady=5)
    paso_slider = tk.Scale(root, from_=1, to=50, orient=tk.HORIZONTAL, command=actualizar_grafica)
    paso_slider.grid(row=4, column=1)

    tk.Label(root, text="Distancia entre puntos(m):").grid(row=5, column=0, pady=5)
    entry_intervalo = tk.Entry(root)
    entry_intervalo.insert(0, "25")
    entry_intervalo.grid(row=5, column=1)

    tk.Label(root, text="Tipo de trayectoria:").grid(row=6, column=0)
    opcion_trayectoria = tk.StringVar(root)
    opcion_trayectoria.set("Zigzag rectangular")
    menu = tk.OptionMenu(root, opcion_trayectoria, "Zigzag rectangular", "Espiral cuadrada", "Rejilla horizontal", command=actualizar_grafica)
    menu.grid(row=6, column=1)

    tk.Button(root, text="Inicializar Gráfica", command=actualizar_grafica).grid(row=8, column=0, columnspan=2, pady=5)

    label_info = tk.Label(root, text="Puntos generados: 0    Distancia total: 0.0", anchor="w", justify="left")
    label_info.grid(row=7, column=0, columnspan=2, sticky="w", pady=5)

    boton_editar = tk.Button(root, text="Editar puntos", command=toggle_edicion)
    boton_editar.grid(row=9, column=0, columnspan=2, pady=5)

    tk.Button(root, text="Ejecutar", command=ejecutar).grid(row=10, column=0, columnspan=2, pady=5)

    slider_simulacion = tk.Scale(root, from_=0, to=1, orient=tk.HORIZONTAL, label="Paso de simulación", command=lambda val: mover_simulacion(int(val)))
    slider_simulacion.grid(row=11, column=0, columnspan=2, pady=5)

    label_posicion = tk.Label(root, text="Posición: -")
    label_posicion.grid(row=12, column=0, columnspan=2)

    fig, ax = plt.subplots(figsize=(5, 5))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().grid(row=0, column=2, rowspan=13, padx=10, pady=10)
    canvas.draw()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

    return {
        "obtener_puntos": puntos,
        "obtener_parametros": obtener_parametros
    }
