import pyautogui
import random
import tkinter as tk
import threading
import time
from real_time import start_emotion_stream

# 1. Initialization

x = 1400        # initial x position
cycle = 0       # current frame in the GIF sequence
check = 1       # current animation state
idle_num = [1, 2, 3, 4]
sleep_num = [10, 11, 12, 13, 15]
walk_left = [6, 7] 
walk_right = [8, 9]
event_number = random.randrange(1, 3, 1)        # randomly choose initial event
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
    if cycle < len(frames) - 1:
        cycle += 1
    else:
        cycle = 0
        event_number = random.randrange(first_num, last_num + 1, 1)
    return cycle, event_number

def load_gif_frames(path):
    """加载一个 gif 的所有帧，直到读不到为止"""
    frames = []
    idx = 0
    while True:
        try:
            frame = tk.PhotoImage(file=path, format=f"gif -index {idx}")
        except tk.TclError:
            break
        frames.append(frame)
        idx += 1
    return frames
# ============================
# 4. Load emotion animations
# ============================
happy_frames    = load_gif_frames(impath + "happy_doggy.gif")
sad_frames      = load_gif_frames(impath + "sad_doggy.gif")
angry_frames    = load_gif_frames(impath + "angry_doggy.gif")
surprise_frames = load_gif_frames(impath + "surprise_doggy.gif")

# 你有多个 neutral，可以随便选一个，或者以后做随机轮换
neutral_frames1 = load_gif_frames(impath + "neutral_doggy1.gif")
# 先用第一套
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

    cat_x = window.winfo_x()
    cat_y = window.winfo_y()
    bubble.geometry(f"+{cat_x + 250}+{cat_y + 50}")

    bubble.after(3000, bubble.destroy)

def on_emotion_from_camera(label, conf, probs):
    """
    摄像头识别出新情绪时会回调到这里。
    label: "Happy" / "Sad" / "Angry" / ...
    """
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
        "show_window": False
    },
    daemon=True
).start()

# ============================
# 8. Start Tk loop
# ============================
window.after(2000, apply_emotion_to_pet)  # 2 秒后开始气泡循环
window.after(10, update, 0)               # 立刻启动动画循环
window.mainloop()