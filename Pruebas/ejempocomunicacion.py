
import tkinter as tk
from tkinter import scrolledtext
import serial
import threading
import time

# Configuración del puerto serial
SERIAL_PORT = 'COM8'  # Cambia esto según tu sistema
BAUD_RATE = 115200

ser = serial.Serial()
ser.port = SERIAL_PORT
ser.baudrate = BAUD_RATE
ser.timeout = 1

def conectar_serial():
    if not ser.is_open:
        ser.open()
        log.insert(tk.END, "Conectado al puerto serial\n")
        threading.Thread(target=leer_serial, daemon=True).start()

def enviar_mensaje():
    if ser.is_open:
        mensaje = entrada.get()
        if mensaje:
            ser.write((mensaje + '\n').encode())
            log.insert(tk.END, f"Tú: {mensaje}\n")
            entrada.delete(0, tk.END)

def leer_serial():
    while ser.is_open:
        try:
            line = ser.readline().decode().strip()
            if line:
                # Verifica si el mensaje es un mensaje recibido por LoRa
                if line.startswith("+RCV="):
                    datos = line.replace("+RCV=", "").split(",")
                    if len(datos) >= 5:
                        address = int(datos[0])
                        longitud = int(datos[1])
                        contenido = datos[2]
                        rssi = int(datos[3])
                        snr = int(datos[4])

                        mensaje_descompuesto = (
                            f"Mensaje LoRa recibido:\n"
                            f"  ➤ Dirección: {address}\n"
                            f"  ➤ Longitud: {longitud} bytes\n"
                            f"  ➤ Contenido: {contenido}\n"
                            f"  ➤ RSSI: {rssi} dBm\n"
                            f"  ➤ SNR: {snr}\n"
                        )
                        log.insert(tk.END, mensaje_descompuesto + "\n")
                    else:
                        log.insert(tk.END, f"ESP32 (formato inválido): {line}\n")
                else:
                    log.insert(tk.END, f"ESP32: {line}\n")

                log.see(tk.END)

        except Exception as e:
            # Puedes imprimir el error si quieres depurar
            # print(f"Error al leer serial: {e}")
            pass

        time.sleep(0.1)

# Interfaz gráfica
ventana = tk.Tk()
ventana.title("Interfaz ESP32 - LoRa")

entrada = tk.Entry(ventana, width=50)
entrada.grid(row=0, column=0, padx=5, pady=5)

boton_enviar = tk.Button(ventana, text="Enviar", command=enviar_mensaje)
boton_enviar.grid(row=0, column=1, padx=5, pady=5)

log = scrolledtext.ScrolledText(ventana, width=60, height=20)
log.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

boton_conectar = tk.Button(ventana, text="Conectar Serial", command=conectar_serial)
boton_conectar.grid(row=2, column=0, columnspan=2, pady=5)

ventana.mainloop()
