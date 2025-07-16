import serial
import threading
import time

def leer_serial(ser):
    while True:
        try:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"\n< {data}")
        except serial.SerialException:
            print("Conexión perdida.")
            break
        except KeyboardInterrupt:
            break

def terminal_serial():
    print("=== Terminal Serial estilo Arduino ===")
    puerto = input("Puerto COM (ej. COM3 o /dev/ttyUSB0): ")
    baudios = input("Baudrate (ej. 9600): ")

    try:
        ser = serial.Serial(puerto, int(baudios), timeout=1)
        print(f"Conectado a {puerto} a {baudios} baudios.\nPresiona Ctrl+C para salir.")
    except Exception as e:
        print(f"No se pudo abrir el puerto: {e}")
        return

    hilo_lectura = threading.Thread(target=leer_serial, args=(ser,), daemon=True)
    hilo_lectura.start()

    try:
        while True:
            mensaje = input("> ")
            ser.write((mensaje + '\n').encode())
    except KeyboardInterrupt:
        print("\nSaliendo...")
    finally:
        ser.close()

if __name__ == "__main__":
    terminal_serial()
