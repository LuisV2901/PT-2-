from Pruebas.cutpgm import seleccionar_y_recortar_mapa
import yaml
from PIL import Image
import matplotlib.pyplot as plt
import tkinter as tk

ruta_yaml = seleccionar_y_recortar_mapa()
print(f"Ruta del YAML: {ruta_yaml}")
xmin = float(f"{ruta_yaml['xmin']:.2f}")
xmax = float(f"{ruta_yaml['xmax']:.2f}")
ymin = float(f"{ruta_yaml['ymin']:.2f}")
ymax = float(f"{ruta_yaml['ymax']:.2f}")
print(f"Coordenadas del recorte: ({xmin}, {ymin}) a ({xmax}, {ymax})")
x_px = ruta_yaml['x_m']
y_px = ruta_yaml['y_m']
print(f"Coordenadas en píxeles: ({x_px}, {y_px})")