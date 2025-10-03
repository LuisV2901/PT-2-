import yaml
from PIL import Image
from tkinter import filedialog
import tkinter as tk
import os
import matplotlib.pyplot as plt
def seleccionar_y_recortar_mapa():
    # Ocultar ventana de Tkinter
    root = tk.Tk()
    root.withdraw()

    # Seleccionar archivo .yaml
    ruta_yaml = filedialog.askopenfilename(
        title="Selecciona archivo YAML del mapa",
        filetypes=[("YAML files", "*.yaml *.yml")]
    )

    if not ruta_yaml:
        print("No se seleccionó ningún archivo YAML.")
        return None

    # Leer el archivo .yaml
    with open(ruta_yaml, 'r') as f:
        config = yaml.safe_load(f)

    image_rel_path = config["image"]
    resolution = config["resolution"]
    origin = config["origin"]

    # Obtener ruta absoluta del .pgm
    dir_yaml = os.path.dirname(ruta_yaml)
    ruta_imagen = os.path.join(dir_yaml, image_rel_path)

    # Cargar imagen
    imagen = Image.open(ruta_imagen)
    ancho, alto = imagen.size

    # === ORIGEN A PIXELES ===
    x_m, y_m = origin[0], origin[1]
    x_px = int(-x_m / resolution)
    y_px = int(alto - (-y_m / resolution))

    # Lista para almacenar dos puntos
    puntos = []

    # Recorte de la imagen con los dos puntos
    def recortar_imagen():
        (x1, y1), (x2, y2) = puntos

        # Asegurar que los índices estén en orden correcto
        xmin_pix, xmax_pix = sorted([x1, x2])
        ymin_pix, ymax_pix = sorted([y1, y2])

        # Convertir a metros usando resolución y origen
        xmin = origin[0] + xmin_pix * resolution
        xmax = origin[0] + xmax_pix * resolution
        # En mapas ROS, el eje Y está invertido respecto a la imagen
        ymin = origin[1] + (alto - ymax_pix) * resolution
        ymax = origin[1] + (alto - ymin_pix) * resolution

        datos_recorte = {
            "xmin": xmin,
            "xmax": xmax,
            "ymin": ymin,
            "ymax": ymax,
            "x_m": x_m,
            "y_m": y_m,
        }
        
        # Imprimir coordenadas
        print("=== Dimensiones del mapa ===")
        print(f"xmin: {xmin:.2f} m")
        print(f"xmax: {xmax:.2f} m")
        print(f"ymin: {ymin:.2f} m")
        print(f"ymax: {ymax:.2f} m")
        print(f"Resolución: {resolution} m/píxel")
        print(f"Tamaño imagen: {ancho} x {alto} píxeles")
        print(f"Origen: ({origin[0]:.2f}, {origin[1]:.2f}) m")
        return datos_recorte

    # Función para clics en la imagen
    def on_click(event):
        if event.inaxes and event.button == 1:
            x, y = int(event.xdata), int(event.ydata)
            puntos.append((x, y))
            ax.plot(x, y, 'go')  # punto verde
            plt.draw()

            if len(puntos) == 2:
                plt.close()
                datos = recortar_imagen()
                nonlocal resultado
                resultado = datos

    resultado = None
    # Mostrar imagen y conectar clics
    fig, ax = plt.subplots()
    ax.imshow(imagen, cmap='gray')
    ax.scatter([x_px], [y_px], color='red', s=60, label="Origin")
    ax.set_title("Clic izquierdo: agregar punto | Clic derecho: eliminar punto cercano")
    ax.legend()
    ax.set_title("Haz clic en dos esquinas opuestas para recortar")
    plt.axis('off')
    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.ion()
    fig.show()
    return resultado
