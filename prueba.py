import tkinter as tk
import time

# Crear la ventana principal
root = tk.Tk()
root.geometry("400x300")
root.title("Aplicación Principal")

# Crear la ventana de carga
splash = tk.Toplevel()
splash.geometry("300x200")
splash.title("Cargando...")

# Etiqueta en la ventana de carga
label = tk.Label(splash, text="Cargando, por favor espere...", font=("Helvetica", 16))
label.pack(expand=True)

# Función para cerrar la ventana de carga y mostrar la ventana principal
def close_splash():
    splash.destroy()
    root.deiconify()

# Ocultar la ventana principal mientras se muestra la ventana de carga
root.withdraw()

# Simular un tiempo de carga
root.after(3000, close_splash)  # 3000 milisegundos = 3 segundos

# Iniciar el bucle principal de Tkinter
root.mainloop()
