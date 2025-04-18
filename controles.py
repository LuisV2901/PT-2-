# Archivo: interfaz_control.py

import tkinter as tk
from PIL import Image, ImageTk

def crear_interfaz():
    # Crear la ventana principal
    root = tk.Tk()
    root.title("Interfaz de Control")

    # Crear un marco para los botones
    frame = tk.Frame(root)
    frame.pack(pady=20)

    # Cargar imágenes
    img_adelante = ImageTk.PhotoImage(Image.open("C:/Users/H563422/OneDrive - Honeywell/GitHub/TT-2/adelante.png"))
    img_atras = ImageTk.PhotoImage(Image.open("C:/Users/H563422/OneDrive - Honeywell/GitHub/TT-2/atras.png"))
    img_giro_derecha = ImageTk.PhotoImage(Image.open("C:/Users/H563422/OneDrive - Honeywell/GitHub/TT-2/derecha.png"))
    img_giro_izquierda = ImageTk.PhotoImage(Image.open("C:/Users/H563422/OneDrive - Honeywell/GitHub/TT-2/izquierda.png"))
    img_alto = ImageTk.PhotoImage(Image.open("C:/Users/H563422/OneDrive - Honeywell/GitHub/TT-2/parar.png"))

    # Definir comandos de los botones
    def adelante_press(event):
        print("Adelante presionado")

    def adelante_release(event):
        print("Adelante soltado")

    def atras_press(event):
        print("Atrás presionado")

    def atras_release(event):
        print("Atrás soltado")

    def giro_derecha_press(event):
        print("Giro a la derecha presionado")

    def giro_derecha_release(event):
        print("Giro a la derecha soltado")

    def giro_izquierda_press(event):
        print("Giro a la izquierda presionado")

    def giro_izquierda_release(event):
        print("Giro a la izquierda soltado")

    def alto_press(event):
        print("Alto presionado")

    def alto_release(event):
        print("Alto soltado")

    # Crear botones con imágenes y colocarlos en forma de cruz
    btn_adelante = tk.Button(frame, image=img_adelante)
    btn_adelante.grid(row=0, column=1)
    btn_adelante.bind("<ButtonPress>", adelante_press)
    btn_adelante.bind("<ButtonRelease>", adelante_release)

    btn_giro_izquierda = tk.Button(frame, image=img_giro_izquierda)
    btn_giro_izquierda.grid(row=1, column=0)
    btn_giro_izquierda.bind("<ButtonPress>", giro_izquierda_press)
    btn_giro_izquierda.bind("<ButtonRelease>", giro_izquierda_release)

    btn_alto = tk.Button(frame, image=img_alto)
    btn_alto.grid(row=1, column=1)
    btn_alto.bind("<ButtonPress>", alto_press)
    btn_alto.bind("<ButtonRelease>", alto_release)

    btn_giro_derecha = tk.Button(frame, image=img_giro_derecha)
    btn_giro_derecha.grid(row=1, column=2)
    btn_giro_derecha.bind("<ButtonPress>", giro_derecha_press)
    btn_giro_derecha.bind("<ButtonRelease>", giro_derecha_release)

    btn_atras = tk.Button(frame, image=img_atras)
    btn_atras.grid(row=2, column=1)
    btn_atras.bind("<ButtonPress>", atras_press)
    btn_atras.bind("<ButtonRelease>", atras_release)

    # Ejecutar la aplicación
    root.mainloop()

