"""
Emotion-Responsive Desktop Pet
------------------------------
This module implements a desktop pet that animates, emotes, and displays 
speech bubbles based on real-time facial emotion recognition. The system 
integrates GIF-based animation, Tkinter UI rendering, and threaded emotion 
stream processing.

Authors: Xiaoqing Zhu, Yizhou Zhang, Hsin Wang
University of Pennsylvania
Date: December 2025

"""

import random
import tkinter as tk
import time
import threading
from PIL import Image, ImageTk
from real_time import start_emotion_stream

# ============================
# 0. Preset dog messages
# ============================
DOG_MESSAGES = [
    "Hey, puppy, you look great today! ",
    "What did you have for lunch?",
    "Wish I could go for a walk right now!",
]

current_mode = "face"
dog_loop_thread = None
stop_dog_loop = True
window = None
label = None


def dog_message_loop():
    global stop_dog_loop, window
    idx = 0

    while not stop_dog_loop:
        msg = DOG_MESSAGES[idx]

        # create speech bubble in main thread
        if window is not None:
            window.after(
                0,
                lambda m=msg: show_speech_bubble("Puppy", custom_text=m)
            )

        idx = (idx + 1) % len(DOG_MESSAGES)

        # divide wait time into small chunks to allow quick exit
        for _ in range(40):  # 40 * 0.1s = 4 秒
            if stop_dog_loop:
                break
            time.sleep(0.1)


def switch_to_dog_mode():
    global current_mode, dog_loop_thread, stop_dog_loop

    print("[desktop_pet] Switch to DOG MODE")
    current_mode = "dog"
    stop_dog_loop = False

    if dog_loop_thread is None or not dog_loop_thread.is_alive():
        dog_loop_thread = threading.Thread(target=dog_message_loop, daemon=True)
        dog_loop_thread.start()


def switch_to_face_mode():
    global current_mode, stop_dog_loop

    print("[desktop_pet] Switch to FACE MODE")
    current_mode = "face"
    stop_dog_loop = True


# ============================
# 1. Main function to start the desktop pet
# ============================
def start_pet(shared_state):
    global state, window, label, scale
    global ANIMATIONS, neutral_frames
    state = shared_state
    pet_type = state.get("pet_type", "westie")

    # ============================
    # 1.1 Determine GIF path
    # ============================
    if pet_type == "westie":
        gif_path = "./westie_gif/"
    elif pet_type == "tom":
        gif_path = "./tom_gif/"       
    elif pet_type == "panda":
        gif_path = "./panda_gif/"
    else:
        gif_path = "./westie_gif/"     


    # ============================
    # 1.2 Tkinter window setup
    # ============================
    window = tk.Tk()
    window.overrideredirect(True)       # remove window decorations
    window.wm_attributes('-transparentcolor', 'black')  # set black as transparent color
    window.wm_attributes('-topmost', True)      # keep window on top
    window.config(bg='black')
    window.bind("1", lambda e: switch_to_dog_mode())
    window.bind("2", lambda e: switch_to_face_mode())

    # ============================
    # 1.3 Make window draggable
    # ============================
    def start_move(event):
        window.x_offset = event.x
        window.y_offset = event.y

    def on_move(event):
        x = event.x_root - window.x_offset
        y = event.y_root - window.y_offset
        window.geometry(f"+{x}+{y}")
    
    # ============================
    # 1.4 Create label to hold GIF
    # ============================
    window.bind("<Button-1>", start_move)
    window.bind("<B1-Motion>", on_move)
    label = tk.Label(window, bd=0, bg='black')
    label.pack()

    # ============================
    # 1.5 Load emotion animations
    # ============================
    scale = float(state.get("scale", 1.0))
    if pet_type == "tom":
        scale *= 0.4
    if pet_type == "panda":
        scale *= 0.5
    happy_frames    = load_gif_scaled(gif_path + f"happy_{pet_type}.gif", scale)
    sad_frames      = load_gif_scaled(gif_path + f"sad_{pet_type}.gif", scale)
    angry_frames    = load_gif_scaled(gif_path + f"angry_{pet_type}.gif", scale)
    surprise_frames = load_gif_scaled(gif_path + f"surprise_{pet_type}.gif", scale)
    neutral_frames  = load_gif_scaled(gif_path + f"neutral_{pet_type}.gif", scale)
    ANIMATIONS = {
        "Happiness": happy_frames,
        "Sadness":   sad_frames,
        "Anger":     angry_frames,
        "Surprise":  surprise_frames,
        "Neutral":   neutral_frames,
    }
    # ============================
    # 1.6 Start emotion stream thread
    # ============================
    threading.Thread(
        target=start_emotion_stream,
        kwargs={
            "callback": on_emotion_from_camera,
            "show_window": True,
            "frame_holder": state,        # save frames
            "state": state                # save state
        },
        daemon=True
    ).start()

    # ============================
    # 1.7 Start applying emotion to pet and animation loop
    # ============================
    window.after(2000, apply_emotion_to_pet)
    window.after(2000, update, 0)
    window.mainloop()


# ============================
# 2.  Initialization
# ============================
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
# 3. Helper function: GIF frame cycling
# ============================
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
# 4. Emotion feedback (speech bubble)
# ============================
emotion_responses = {
    "Happiness": "Yay! I'm so happy with you! 😺",
    "Sadness":   "Aww... Don't worry, I'm here for you 💕",
    "Anger":     "Take a deep breath... You’ve got this 💪",
    "Surprise":  "Whoa! That was unexpected! 😸",
    "Neutral":   "Hmm... A calm day feels nice 💤"
}

bubble_window = None   

def _create_round_rect(self, x1, y1, x2, y2, r=20, **kwargs):
    points = [
        x1+r, y1,
        x2-r, y1,
        x2, y1,
        x2, y1+r,
        x2, y2-r,
        x2, y2,
        x2-r, y2,
        x1+r, y2,
        x1, y2,
        x1, y2-r,
        x1, y1+r,
        x1, y1,
    ]
    return self.create_polygon(points, smooth=True, **kwargs)

# Using canvas extension to create rounded rectangle
tk.Canvas.create_round_rect = _create_round_rect

# ============================
# 5. Show speech bubble
# ============================
# ========================================
# 4. Unified speech bubble (Puppy included)
# ========================================
def show_speech_bubble(emotion: str, custom_text=None):
    global bubble_window, window, label

    # ========== Unified text ==========
    if custom_text is not None:
        response = custom_text
    else:
        response = emotion_responses.get(emotion, "I'm here with you!")

    # ========== Emoji ==========
    emoji_map = {
        "Happiness": "😺",
        "Sadness": "😢",
        "Anger": "😡",
        "Surprise": "😮",
        "Neutral": "😐",
        "Puppy": "🐶"   # Puppy behaves just like a new emotion category
    }
    emoji = emoji_map.get(emotion, "😐")

    # Remove previous bubble
    if bubble_window is not None:
        try:
            bubble_window.destroy()
        except:
            pass
    bubble_window = None

    # Create bubble window
    bubble = tk.Toplevel(window)
    bubble.withdraw()
    bubble.overrideredirect(True)
    bubble.attributes("-topmost", True)
    bubble.config(bg="black")

    outer = tk.Frame(bubble, bd=0, padx=2, pady=2)
    outer.pack()

    card = tk.Frame(outer, bg="white", bd=0, padx=10, pady=6)
    card.pack()

    # Unified header
    header_text = f"Detected emotion:\n {emoji}  {emotion}"

    header = tk.Label(card, text=header_text, font=("Segoe UI", 9, "bold"),
                      bg="white", fg="#7A7A7A", anchor="w")
    header.pack(fill="x")

    divider = tk.Frame(card, bg="#E0E0E0", height=1)
    divider.pack(fill="x", pady=(4, 4))

    text_label = tk.Label(
        card, text=response, font=("Segoe UI", 11, "bold"),
        bg="white", fg="#030303", justify="left", wraplength=260
    )
    text_label.pack()

    bubble.update_idletasks()

    # Position bubble relative to pet
    pet_x = window.winfo_x()
    pet_y = window.winfo_y()
    pet_w = label.winfo_width() or 200
    pet_h = label.winfo_height() or 200

    bw = bubble.winfo_width()
    bh = bubble.winfo_height()

    final_x = pet_x + pet_w - 5
    final_y = pet_y + pet_h - bh + 5

    final_x = max(10, final_x)
    final_y = max(10, final_y)

    bubble.geometry(f"{bw}x{bh}+{final_x}+{final_y}")
    bubble.deiconify()
    bubble_window = bubble

    bubble.after(3000, bubble.destroy)


# ========================================
# ============================
# 6. Get emotion callback
# ============================
def on_emotion_from_camera(label, conf, probs):
    """
    callback from real_time.py when an emotion is detected
    """
    # print("[desktop_pet] on_emotion_from_camera is called")
    # print(f"[Callback] Detected {label} (conf={conf:.2f})")
    global current_emotion_label, current_pet_emotion
    current_emotion_label = label
    current_pet_emotion = EMOTION_MAP.get(label, "Neutral")
    # print(f"[Callback] Detected {label} (conf={conf:.2f}), pet emotion = {current_pet_emotion}")

# ============================
# 7. Apply emotion to pet
# ============================
def apply_emotion_to_pet():
    """
    pop up speech bubble based on current emotion
    """
    global current_pet_emotion

    if current_mode != "face":
        window.after(4000, apply_emotion_to_pet)
        return

    show_speech_bubble(current_pet_emotion)
    window.after(4000, apply_emotion_to_pet)


# ============================
# 8. Main animation loop
# ============================
def update(cycle=0):
    """
    play the GIF animation based on current emotion
    """
    global ANIMATIONS, neutral_frames, current_pet_emotion
    print("[desktop_pet] update is running")
    global label

    frames = ANIMATIONS.get(current_pet_emotion, neutral_frames)
    if not frames:
        window.after(100, update, 0)
        return

    frame = frames[cycle % len(frames)]
    label.configure(image=frame)
    label.config(bg='black')

    # next cycle
    next_cycle = (cycle + 1) % len(frames)
    window.after(100, update, next_cycle)   # 200ms per frame



