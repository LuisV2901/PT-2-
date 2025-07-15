import yaml
from PIL import Image
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
import os
import numpy as np

# === SELECCIONAR ARCHIVO YAML ===
root = tk.Tk()
root.withdraw()

ruta_yaml = filedialog.askopenfilename(
    title="Selecciona el archivo YAML del mapa",
    filetypes=[("YAML files", "*.yaml *.yml")]
)

if not ruta_yaml:
    print("No se seleccionó ningún archivo YAML.")
    exit()

# === CARGAR YAML ===
with open(ruta_yaml, 'r') as f:
    config = yaml.safe_load(f)

imagen_relativa = config["image"]
resolution = config["resolution"]
origin = config["origin"]

# Ruta absoluta al .pgm
directorio_yaml = os.path.dirname(ruta_yaml)
ruta_imagen = os.path.join(directorio_yaml, imagen_relativa)

# === CARGAR IMAGEN ===
imagen = Image.open(ruta_imagen)
ancho, alto = imagen.size

# === ORIGEN A PIXELES ===
x_m, y_m = origin[0], origin[1]

print(f"Origen en metros: ({x_m}, {y_m})")
x_px = int(-x_m / resolution)
y_px = int(alto - (-y_m / resolution))

print(f"Origen en píxeles: ({x_px}, {y_px})")

# === LISTAS DE PUNTOS ===
puntos_pixeles = []
puntos_mundo = []
puntos_plot = []  # referencias a los puntos dibujados (Line2D)

# === FUNCIÓN DE CLIC ===
def onclick(event):
    if not event.inaxes:
        return

    x_click = int(event.xdata)
    y_click = int(event.ydata)

    # BOTÓN IZQUIERDO: agregar punto
    if event.button == 1:
        puntos_pixeles.append((x_click, y_click))

        x_world = x_click * resolution + origin[0]
        y_world = (alto - y_click) * resolution + origin[1]
        puntos_mundo.append((x_world, y_world))

        punto = ax.plot(x_click, y_click, 'bo')[0]
        puntos_plot.append(punto)

        print(f"➕ Punto agregado en píxeles: ({x_click}, {y_click}) -> metros: ({x_world:.2f}, {y_world:.2f})")

    # BOTÓN DERECHO: eliminar punto más cercano
    elif event.button == 3 and puntos_pixeles:
        # Calcular distancias a todos los puntos guardados
        distancias = [np.hypot(px - x_click, py - y_click) for px, py in puntos_pixeles]
        idx_min = int(np.argmin(distancias))

        if distancias[idx_min] < 15:  # tolerancia en píxeles
            # Eliminar datos
            eliminado_pix = puntos_pixeles.pop(idx_min)
            eliminado_mundo = puntos_mundo.pop(idx_min)
            punto_plot = puntos_plot.pop(idx_min)
            punto_plot.remove()

            print(f"❌ Punto eliminado: ({eliminado_pix}) -> ({eliminado_mundo[0]:.2f}, {eliminado_mundo[1]:.2f})")
        else:
            print("⚠️ No hay puntos suficientemente cerca para eliminar.")

    plt.draw()

# === MOSTRAR IMAGEN ===
fig, ax = plt.subplots()
ax.imshow(imagen, cmap='gray')
ax.scatter([x_px], [y_px], color='red', s=60, label="Origin")
ax.set_title("Clic izquierdo: agregar punto | Clic derecho: eliminar punto cercano")
ax.legend()
plt.axis('off')

# Conectar evento
fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()

# === RESULTADOS ===
print("\n📌 Puntos finales (en píxeles):")
print(puntos_pixeles)

print("\n🌍 Puntos finales (en metros):")
for p in puntos_mundo:
    print(f"{p[0]:.2f}, {p[1]:.2f}")
