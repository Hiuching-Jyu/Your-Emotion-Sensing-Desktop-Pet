import ttkbootstrap as tb
from ttkbootstrap.constants import *
from multiprocessing import Process, Manager
import tkinter as tk
from PIL import Image, ImageTk
import call_desktop_pet

import sys, os

# ============================
# 0. Resource path for PyInstaller
# ============================
def resource_path(relative_path):
    
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ============================
# 1. Launch pet process
# ============================
def launch_pet(state):
    call_desktop_pet.run_pet(state)


# ============================
# 2. Desktop Pet Controller UI
# ============================
class DesktopPetUI(tb.Window):
    def __init__(self):
        super().__init__(title="Desktop Pet Controller", themename="flatly")  

        self.geometry("520x650")
        self.shared_state = Manager().dict({
            "running": False,
            "pet_type": "westie",
            "scale": 1.0,
            "x": 400,
            "y": 800,
        })
        self.pet_process = None

        self._build_ui()

    def _build_ui(self):

        title = tb.Label(self, text="Desktop Pet Controller",
                         font=("Segoe UI", 18, "bold"))
        title.pack(pady=15)

        # ---- Start / Stop ----
        button_frame = tb.Frame(self)
        button_frame.pack(pady=5)

        start_btn = tb.Button(button_frame, text="▶ Start Pet",
                              bootstyle=SUCCESS, command=self.start_pet)
        stop_btn = tb.Button(button_frame, text="⏹ Stop Pet",
                             bootstyle=DANGER, command=self.stop_pet)

        start_btn.grid(row=0, column=0, padx=10)
        stop_btn.grid(row=0, column=1, padx=10)

        tb.Separator(self).pack(fill="x", pady=10)

        # ---- Preview ----
        tb.Label(self, text="Preview Pets", font=("Segoe UI", 14, "bold")).pack()

        preview_frame = tb.Frame(self)
        preview_frame.pack(pady=10)

        # ---- Load preview images ----
        preview_size = (160, 120)

        self.preview_westie = ImageTk.PhotoImage(
            Image.open(resource_path("./westie_gif/preview_westie.gif")).resize(preview_size)
        )
        self.preview_tom = ImageTk.PhotoImage(
            Image.open(resource_path("./tom_gif/preview_tom.gif")).resize(preview_size)
        )


        self._create_preview(preview_frame, "Westie", self.preview_westie, 0)
        self._create_preview(preview_frame, "Tom", self.preview_tom, 1)

        tb.Separator(self).pack(fill="x", pady=10)

        # ---- Choose Pet ----
        tb.Label(self, text="Choose Your Pet:", font=("Segoe UI", 11)).pack()
        self.pet_var = tb.StringVar(value="westie")

        pet_selector = tb.Combobox(self, textvariable=self.pet_var,
                                   values=["westie", "tom"], bootstyle=LIGHT)
        pet_selector.pack(pady=5)

        # ---- Scale ----
        tb.Label(self, text="Scale:").pack()
        self.scale_var = tk.DoubleVar(value=1.0)
        tb.Scale(self, from_=0.2, to=2.0, variable=self.scale_var,
                 bootstyle=INFO).pack(fill="x", padx=40)

        # ---- X ----
        tb.Label(self, text="X Position:").pack()
        self.x_var = tk.IntVar(value=400)
        tb.Scale(self, from_=0, to=2000, variable=self.x_var,
                 bootstyle=PRIMARY).pack(fill="x", padx=40)

        # ---- Y ----
        tb.Label(self, text="Y Position:").pack()
        self.y_var = tk.IntVar(value=800)
        tb.Scale(self, from_=0, to=1200, variable=self.y_var,
                 bootstyle=SECONDARY).pack(fill="x", padx=40)

    # -------------------------------------------------
    # Preview block
    # -------------------------------------------------
    def _create_preview(self, parent, name, image, col):
        frame = tb.Frame(parent, padding=10)
        frame.grid(row=0, column=col, padx=20)

        tb.Label(frame, text=name, font=("Segoe UI", 12, "bold")).pack()
        tb.Label(frame, image=image).pack()

    # -------------------------------------------------
    # Start / Stop
    # -------------------------------------------------
    def start_pet(self):
        if self.pet_process and self.pet_process.is_alive():
            return

        self.shared_state["running"] = True
        self.shared_state["pet_type"] = self.pet_var.get()
        self.shared_state["scale"] = self.scale_var.get()
        self.shared_state["x"] = self.x_var.get()
        self.shared_state["y"] = self.y_var.get()

        self.pet_process = Process(target=launch_pet, args=(self.shared_state,))
        self.pet_process.start()

    def stop_pet(self):
        if self.pet_process and self.pet_process.is_alive():
            self.shared_state["running"] = False
            self.pet_process.terminate()
            self.pet_process = None


# -------------------------------------------------
# Main
# -------------------------------------------------
if __name__ == "__main__":
    app = DesktopPetUI()
    app.mainloop()
