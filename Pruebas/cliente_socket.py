import socket
import threading 
import tkinter as tk
from tkinter import scrolledtext

# Función para enviar el mensaje al servidor
def send_message(text_area, message_entry):
    message = message_entry.get()
    if message:
        client_socket.sendall(message.encode())
        text_area.insert(tk.END, f"Enviado: {message}\n")
        text_area.yview(tk.END)
        message_entry.delete(0, tk.END)

# Función para recibir mensajes del servidor
def receive_messages():
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        text_area.insert(tk.END, f"Servidor: {data.decode()}\n")
        text_area.yview(tk.END)

# Configuración de la interfaz
def create_client_ui():
    global client_socket
    root = tk.Tk()
    root.title("Cliente")

    # Conectar al servidor
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 65432))

    # Área de texto para mostrar los mensajes
    global text_area
    text_area = scrolledtext.ScrolledText(root, width=40, height=10)
    text_area.grid(row=0, column=0, padx=10, pady=10)

    # Entrada de texto para el mensaje
    message_entry = tk.Entry(root, width=30)
    message_entry.grid(row=1, column=0, padx=10, pady=10)

    # Botón para enviar mensaje
    send_button = tk.Button(root, text="Enviar Mensaje", command=lambda: send_message(text_area, message_entry))
    send_button.grid(row=2, column=0, padx=10, pady=10)

    # Botón para finalizar la comunicación
    def stop_communication():
        client_socket.close()
        root.quit()

    stop_button = tk.Button(root, text="Finalizar Comunicación", command=stop_communication)
    stop_button.grid(row=3, column=0, padx=10, pady=10)

    # Iniciar hilo para recibir mensajes
    threading.Thread(target=receive_messages, daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    create_client_ui()
