import tkinter as tk

class LoadingWindow:
    def __init__(self, parent, max_count):
        self.parent = parent
        self.max_count = max_count
        self.current_count = 0

        self.top = tk.Toplevel(parent)
        self.top.title("Progreso por evento")
        width, height = 250, 150
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.top.geometry(f"{width}x{height}+{x}+{y}")
        self.top.resizable(False, False)
        self.top.transient(parent)

        self.label = tk.Label(self.top, text=f"0% completado\n0 de {max_count} eventos", font=("Arial", 12))
        self.label.pack(pady=10)

        self.canvas = tk.Canvas(self.top, width=200, height=20, bg="white", bd=1, relief="sunken")
        self.canvas.pack(pady=10)
        self.progress_rect = self.canvas.create_rectangle(0, 0, 0, 20, fill="green")

        self.close_button = tk.Button(self.top, text="Cerrar", command=self.top.destroy)
        self.close_button.pack(pady=10)
        self.close_button.config(state="disabled")  # Desactivado hasta que se complete

    def increment_progress(self):
        if self.current_count < self.max_count:
            self.current_count += 1
            percent = (self.current_count / self.max_count) * 100
            self.label.config(text=f"{int(percent)}% completado\n{self.current_count} de {self.max_count} eventos")
            self.canvas.coords(self.progress_rect, 0, 0, 2 * percent, 20)

        if self.current_count >= self.max_count:
            self.label.config(text="100% completado\n¡Proceso finalizado!")
            self.close_button.config(state="normal")
