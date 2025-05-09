
from progress import LoadingWindow
import tkinter as tk
root = tk.Tk()
root.geometry("300x200")
root.title("Controlador de eventos")

loading_window = None


def start_loading():
    global loading_window
    loading_window = LoadingWindow(root, max_count=7)# Puedes cambiar el número aquí


def add_event():
    if loading_window:
        loading_window.increment_progress()

btn_start = tk.Button(root, text="Iniciar progreso", command=start_loading)
btn_start.pack(pady=10)

btn_event = tk.Button(root, text="Agregar evento", command=add_event)
btn_event.pack(pady=10)

root.mainloop()

