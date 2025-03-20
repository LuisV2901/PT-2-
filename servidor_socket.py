import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

# Función para manejar la conexión del cliente
def handle_client(client_socket, text_area):
    with client_socket:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            text_area.insert(tk.END, f"Recibido: {data.decode()}\n")
            text_area.yview(tk.END)

# Función para enviar mensajes al cliente desde el servidor
def send_message_to_client(client_socket, text_area, message_entry):
    message = message_entry.get()
    if message:
        client_socket.sendall(message.encode())
        text_area.insert(tk.END, f"Servidor envió: {message}\n")
        text_area.yview(tk.END)
        message_entry.delete(0, tk.END)

# Función para aceptar conexiones de clientes
def start_server(text_area, message_entry):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 65432))
    server_socket.listen()
    print("Esperando conexión...")
    client_socket, addr = server_socket.accept()
    print(f"Conectado a {addr}")
    
    # Iniciar un hilo para manejar la comunicación con el cliente
    threading.Thread(target=handle_client, args=(client_socket, text_area), daemon=True).start()

    # Enviar mensajes cuando el servidor lo decida
    send_button = tk.Button(root, text="Enviar mensaje al cliente",command=lambda: send_message_to_client(client_socket, text_area, message_entry))
    send_button.grid(row=2, column=0, padx=10, pady=10)

# Configuración de la interfaz
def create_server_ui():
    global root
    root = tk.Tk()
    root.title("Servidor")

    # Área de texto para mostrar los mensajes
    text_area = scrolledtext.ScrolledText(root, width=40, height=10)
    text_area.grid(row=0, column=0, padx=10, pady=10)

    # Entrada de texto para el mensaje
    message_entry = tk.Entry(root, width=30)
    message_entry.grid(row=1, column=0, padx=10, pady=10)

    # Iniciar servidor en un hilo para no bloquear la interfaz
    threading.Thread(target=start_server, args=(text_area, message_entry), daemon=True).start()

    # Botón para finalizar el servidor
    def stop_server():
        root.quit()

    stop_button = tk.Button(root, text="Finalizar Comunicación", command=stop_server)
    stop_button.grid(row=3, column=0, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_server_ui()
