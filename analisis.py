import pandas as pd
import re
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
import mplcursors
import tkinter as tk
from tkinter import filedialog

def analizar_csv(archivo=None):
    # Selección de archivo si no se proporciona
    if archivo is None:
        root = tk.Tk()
        root.withdraw()
        archivo = filedialog.askopenfilename(
            title="Selecciona el archivo CSV",
            filetypes=[("CSV files", "*.csv")]
        )
        if not archivo:
            raise ValueError("No se seleccionó ningún archivo.")

    # Leer la primera línea para extraer el Robot ID
    with open(archivo, 'r', encoding="latin1") as f:
        primera_linea = f.readline()
        match = re.search(r"Robot:\s*(\d+)", primera_linea)
        robot_id = match.group(1) if match else "?"

    # Cargar datos del CSV (saltando la primera línea)
    df = pd.read_csv(archivo, encoding="latin1", skiprows=1)

    # Filtrar y renombrar columnas
    df = df[df.columns[:4]]
    df.columns = ["Checkpoint", "Hora", "Sensor", "Valor"]

    # Limpiar columna "Valor"
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor", "Checkpoint"])

    # Extraer coordenadas (x, y) desde la columna "Checkpoint"
    def extraer_coordenadas(cp):
        match = re.search(r"\(([\d\.]+),([\d\.]+)\)", cp)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None

    df["x"], df["y"] = zip(*df["Checkpoint"].map(extraer_coordenadas))
    df = df.dropna(subset=["x", "y"])

    # Calcular estadísticas por punto y sensor
    stats = df.groupby(["x", "y", "Sensor"])["Valor"].agg(["min", "max", "mean"]).reset_index()

    # Agrupar info por coordenada
    datos_por_punto = {}
    for _, row in stats.iterrows():
        coord = (row["x"], row["y"])
        if coord not in datos_por_punto:
            datos_por_punto[coord] = []
        datos_por_punto[coord].append(
            f"{row['Sensor']}\n  Min: {row['min']:.2f}\n  Max: {row['max']:.2f}\n  Prom: {row['mean']:.2f}"
        )

    # Preparar puntos para graficar
    x_vals, y_vals = zip(*datos_por_punto.keys())

    # Crear gráfico
    fig, ax = plt.subplots(figsize=(8, 8))
    scatter = ax.scatter(x_vals, y_vals, c='dodgerblue', s=80)

    # Ajustar límites automáticamente con margen
    margin = 1
    ax.set_xlim(min(x_vals) - margin, max(x_vals) + margin)
    ax.set_ylim(min(y_vals) - margin, max(y_vals) + margin)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(f"Mapa de mediciones - Robot {robot_id}")
    ax.grid(True)

    # Tooltip interactivo
    cursor = mplcursors.cursor(scatter, hover=True)
    @cursor.connect("add")
    def on_add(sel):
        coord = (x_vals[sel.index], y_vals[sel.index])
        info = "\n\n".join(datos_por_punto[coord])
        sel.annotation.set(text=f"Punto: {coord}\n\n{info}", fontsize=8)

    plt.tight_layout()
    plt.show()
