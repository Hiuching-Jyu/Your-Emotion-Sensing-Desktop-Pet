import tkinter as tk
from tkinter import ttk
from multiprocessing import Manager
import call_desktop_pet
from PIL import Image, ImageTk
import os

# 预览 GIF 文件路径
PET_OPTIONS = {
    "westie": "./westie_gif/happy_westie.gif",
    "tom": "./tom_gif/happy_tom.gif"
}


class PetSelector(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Choose Your Pet")
        self.geometry("420x350")
        self.resizable(False, False)

        ttk.Label(self, text="Choose Your Desktop Pet", font=("Segoe UI", 13, "bold")).pack(pady=10)

        self.pet_type = tk.StringVar(value="westie")

        frame = ttk.Frame(self)
        frame.pack(pady=10)

        # 两个预览按钮（Westie / Tom）
        self.create_pet_button(frame, "westie", 0)
        self.create_pet_button(frame, "tom", 1)

        start_btn = ttk.Button(self, text="Start Pet!", command=self.launch_pet)
        start_btn.pack(pady=15)

    def create_pet_button(self, parent, name, col):
        gif_path = PET_OPTIONS[name]
        frames = []

        img = Image.open(gif_path)
        try:
            while True:
                frame = ImageTk.PhotoImage(img.copy().resize((150, 150)))
                frames.append(frame)
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        gif_label = tk.Label(parent)
        gif_label.grid(row=0, column=col, padx=15)

        # 点击 GIF 选中宠物
        gif_label.bind("<Button-1>", lambda e, n=name: self.pet_type.set(n))

        def play_gif(frame_id=0):
            gif_label.config(image=frames[frame_id])
            self.after(120, play_gif, (frame_id + 1) % len(frames))

        play_gif()

        ttk.Radiobutton(
            parent,
            text=name.capitalize(),
            variable=self.pet_type,
            value=name
        ).grid(row=1, column=col, pady=5)

    def launch_pet(self):
        """启动桌宠进程"""
        manager = Manager()
        shared_state = manager.dict({
            "running": True,
            "pet_type": self.pet_type.get(),
            "scale": 1.0,
            "x": 400,
            "y": 900,
        })

        self.destroy()

        call_desktop_pet.run_pet(shared_state)




if __name__ == "__main__":
    PetSelector().mainloop()
