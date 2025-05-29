import tkinter as tk

class LoadingWindow:
    def __init__(self, parent, cks, num):
        self.parent = parent
        self.cks = cks
        self.num = num
        self.max_count = cks*num
        self.current_count = 0

        self.top = tk.Toplevel(parent)
        self.top.title("Progreso por evento")
        width, height = 300, 150
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.top.geometry(f"{width}x{height}+{x}+{y}")
        self.top.resizable(False, False)
        self.top.transient(parent)

        self.label = tk.Label(self.top, text=f"0% completado de {self.max_count} mediciones\nCheckpoint 0 de {self.cks}\nMedición 0 de {self.num}", font=("Arial", 12))
        self.label.pack(pady=10)

        self.canvas = tk.Canvas(self.top, width=200, height=20, bg="white", bd=1, relief="sunken")
        self.canvas.pack(pady=10)
        self.progress_rect = self.canvas.create_rectangle(0, 0, 0, 20, fill="green")

        self.close_button = tk.Button(self.top, text="Cerrar", command=self.top.destroy)
        self.close_button.pack(pady=10)
        self.close_button.config(state="disabled")  # Desactivado hasta que se complete

    def increment_progress(self, ck, num):
        if self.current_count < self.max_count:
            self.current_count += 1
            print(f"C:{self.current_count} MAX:{self.max_count}")
            percent = (self.current_count / self.max_count) * 100
            self.label.config(text=f"{int(percent)}% completado de {self.max_count} mediciones\nCheckpoint {ck} de {self.cks}\nMedición {num} de {self.num}", font=("Arial", 12))
            self.canvas.coords(self.progress_rect, 0, 0, 2 * percent, 20)

        if self.current_count >= self.max_count:
            self.label.config(text="100% completado\n¡Proceso finalizado!")
            self.close_button.config(state="normal")
