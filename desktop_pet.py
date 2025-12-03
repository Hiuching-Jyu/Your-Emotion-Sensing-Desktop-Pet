import pyautogui
import random
import tkinter as tk
import threading
import time
from PIL import Image, ImageTk
from real_time import start_emotion_stream

# 1. Initialization
impath = ".//doggy_gif//"
current_emotion_label = "Neutral"
current_pet_emotion = "Neutral"

EMOTION_MAP = {
    "Happy": "Happiness",
    "Sad": "Sadness",
    "Angry": "Anger",
    "Surprise": "Surprise",
    "Neutral": "Neutral",
    "Fear": "Surprise",
    "Disgust": "Sadness",
}

# ============================
# 2. Tkinter window setup
# ============================
window = tk.Tk()
window.overrideredirect(True)       # remove window decorations
window.wm_attributes('-transparentcolor', 'black')  # set black as transparent color
window.wm_attributes('-topmost', True)      # keep window on top
window.config(bg='black')

label = tk.Label(window, bd=0, bg='black')
label.pack()

# 3. Helper function: GIF frame cycling

def gif_work(cycle, frames, event_number, first_num, last_num):
    """Cycle through frames and switch to next event when one animation ends"""
    print("[desktop_pet] gif_work is running")
    if cycle < len(frames) - 1:
        cycle += 1
    else:
        cycle = 0
        event_number = random.randrange(first_num, last_num + 1, 1)
    return cycle, event_number


def load_gif_scaled(path, scale=1.0):
    print(f"[desktop_pet] Loading scaled GIF from {path}, scale={scale}")
    frames = []

    img = Image.open(path)

    try:
        while True:
            frame = img.copy().convert("RGBA")

            w, h = frame.size
            frame = frame.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

            frames.append(ImageTk.PhotoImage(frame))

            img.seek(img.tell() + 1)

    except EOFError:
        pass

    return frames


# ============================
# 4. Load emotion animations
# ============================
scale = 0.5
happy_frames    = load_gif_scaled(impath + "happy_doggy.gif", scale)
sad_frames      = load_gif_scaled(impath + "sad_doggy.gif", scale)
angry_frames    = load_gif_scaled(impath + "angry_doggy.gif", scale)
surprise_frames = load_gif_scaled(impath + "surprise_doggy.gif", scale)

neutral_frames1 = load_gif_scaled(impath + "neutral_doggy1.gif", scale)
neutral_frames = neutral_frames1

ANIMATIONS = {
    "Happiness": happy_frames,
    "Sadness":   sad_frames,
    "Anger":     angry_frames,
    "Surprise":  surprise_frames,
    "Neutral":   neutral_frames,
}

# ============================
# 5. Emotion feedback (speech bubble)
# ============================
emotion_responses = {
    "Happiness": "Yay! I'm so happy with you! 😺",
    "Sadness":   "Aww... Don't worry, I'm here for you 💕",
    "Anger":     "Take a deep breath... You’ve got this 💪",
    "Surprise":  "Whoa! That was unexpected! 😸",
    "Neutral":   "Hmm... A calm day feels nice 💤"
}

def show_speech_bubble(emotion):
    """Show a floating speech bubble near the dog"""
    print(f"[desktop_pet] Showing speech bubble for emotion: {emotion}")
    response = emotion_responses.get(emotion, "I'm here with you!")

    bubble = tk.Toplevel(window)
    bubble.overrideredirect(True)
    bubble.config(bg="#fefae0", padx=10, pady=5)
    bubble.wm_attributes('-topmost', True)

    label_bubble = tk.Label(
        bubble,
        text=response,
        font=("Comic Sans MS", 11, "bold"),
        bg="#fefae0",
        fg="#3a3a3a",
        wraplength=200,
        justify="left"
    )
    label_bubble.pack()

    pet_x = window.winfo_x()
    pet_y = window.winfo_y()
    bubble.geometry(f"+{pet_x + 250}+{pet_y + 50}")

    bubble.after(3000, bubble.destroy)


def on_emotion_from_camera(label, conf, probs):
    """
    摄像头识别出新情绪时会回调到这里。
    label: "Happy" / "Sad" / "Angry" / ...
    """
    print("[desktop_pet] on_emotion_from_camera is called")
    print(f"[Callback] Detected {label} (conf={conf:.2f})")
    global current_emotion_label, current_pet_emotion
    current_emotion_label = label
    current_pet_emotion = EMOTION_MAP.get(label, "Neutral")
    print(f"[Callback] Detected {label} (conf={conf:.2f}), pet emotion = {current_pet_emotion}")


def apply_emotion_to_pet():
    """
    每隔一段时间，根据当前情绪弹出一次气泡
    """
    print(f"Emotion detected: {current_emotion_label}")
    print(f"Mapped to pet emotion: {current_pet_emotion}")
    show_speech_bubble(current_pet_emotion)

    window.after(4000, apply_emotion_to_pet)  # 4 秒弹一次，你可以改


# ============================
# 6. Main animation loop
# ============================
def update(cycle=0):
    """
    根据 current_pet_emotion 播放对应 gif 帧
    """
    print("[desktop_pet] update is running")
    global label

    frames = ANIMATIONS.get(current_pet_emotion, neutral_frames)
    if not frames:
        window.after(100, update, 0)
        return

    frame = frames[cycle % len(frames)]
    label.configure(image=frame)

    # 下一帧
    next_cycle = (cycle + 1) % len(frames)
    window.after(100, update, next_cycle)   # 每 100ms 播放一帧，可微调速度


# ============================
# 7. Start emotion stream thread
# ============================
threading.Thread(
    target=start_emotion_stream,
    kwargs={
        "callback": on_emotion_from_camera,
        "show_window": False   # do not show the camera window
    },
    daemon=True
).start()


# main loop
window.after(2000, apply_emotion_to_pet)
window.after(2000, update, 0)
window.mainloop()
