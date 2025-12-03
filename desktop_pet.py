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
impath = ".//pet_gif//"
current_emotion_label = "Neutral"

EMOTION_MAP = {
    "Happy": "Happiness",
    "Sad": "Sadness",
    "Angry": "Anger",
    "Surprise": "Surprise",
    "Neutral": "Neutral",
    "Fear": "Surprise",
    "Disgust": "Sadness",
}

# 2. Helper function: GIF frame cycling

def gif_work(cycle, frames, event_number, first_num, last_num):
    """Cycle through frames and switch to next event when one animation ends"""
    if cycle < len(frames) - 1:
        cycle += 1
    else:
        cycle = 0
        event_number = random.randrange(first_num, last_num + 1, 1)
    return cycle, event_number

# 3. Main update logic
def update(cycle, check, event_number, x):
    """Update current animation frame"""
    global label

    # idle
    if check == 0:
        frame = idle[cycle]
        cycle, event_number = gif_work(cycle, idle, event_number, 1, 9)

    # from idle state to sleep state
    elif check == 1:
        frame = idle_to_sleep[cycle]
        cycle, event_number = gif_work(cycle, idle_to_sleep, event_number, 10, 10)

    # sleep
    elif check == 2:
        frame = sleep[cycle]
        cycle, event_number = gif_work(cycle, sleep, event_number, 10, 15)

    # from sleep state to idle state
    elif check == 3:
        frame = sleep_to_idle[cycle]
        cycle, event_number = gif_work(cycle, sleep_to_idle, event_number, 1, 1)

    # walk toward left
    elif check == 4:
        frame = walk_positive[cycle]
        cycle, event_number = gif_work(cycle, walk_positive, event_number, 1, 9)
        x -= 3

    # walk toward right
    elif check == 5:
        frame = walk_negative[cycle]
        cycle, event_number = gif_work(cycle, walk_negative, event_number, 1, 9)
        x += 3

    window.geometry('300x300+600+400') # set window size and position
    label.configure(image=frame)

    window.after(100, event, cycle, check, event_number, x)     # update every 100 ms, to decide next event

# 4. Event transition control
def event(cycle, check, event_number, x):
    """Handle transitions between animations"""
    if event_number in idle_num:
        check = 0
        window.after(400, update, cycle, check, event_number, x)

    elif event_number == 5:
        check = 1
        window.after(100, update, cycle, check, event_number, x)

    elif event_number in walk_left:
        check = 4
        window.after(100, update, cycle, check, event_number, x)

    elif event_number in walk_right:
        check = 5
        window.after(100, update, cycle, check, event_number, x)

    elif event_number in sleep_num:
        check = 2
        window.after(1000, update, cycle, check, event_number, x)

    elif event_number == 14:
        check = 3
        window.after(100, update, cycle, check, event_number, x)

# 5. Tkinter window setup
window = tk.Tk()
window.overrideredirect(True)       # remove window decorations
window.wm_attributes('-transparentcolor', 'black')  # set black as transparent color
window.wm_attributes('-topmost', True)      # keep window on top
window.config(bg='black')

label = tk.Label(window, bd=0, bg='black')
label.pack()

# 6. Load GIF sequences for different animations as frame lists
idle = [tk.PhotoImage(file=impath + 'idle.gif', format='gif -index %i' % i) for i in range(5)]
idle_to_sleep = [tk.PhotoImage(file=impath + 'idle_to_sleep.gif', format='gif -index %i' % i) for i in range(8)]
sleep = [tk.PhotoImage(file=impath + 'sleep.gif', format='gif -index %i' % i) for i in range(3)]
sleep_to_idle = [tk.PhotoImage(file=impath + 'sleep_to_idle.gif', format='gif -index %i' % i) for i in range(8)]
walk_positive = [tk.PhotoImage(file=impath + 'walk_left.gif', format='gif -index %i' % i) for i in range(8)]
walk_negative = [tk.PhotoImage(file=impath + 'walk_right.gif', format='gif -index %i' % i) for i in range(8)]

# 7. Emotion feedback system (Floating Speech Bubble)
emotion_responses = {
    "Happiness": "Yay! I'm so happy with you! 😺",
    "Sadness": "Aww... Don't worry, I'm here for you 💕",
    "Anger": "Take a deep breath... You’ve got this 💪",
    "Surprise": "Whoa! That was unexpected! 😸",
    "Neutral": "Hmm... A calm day feels nice 💤"
}

def show_speech_bubble(emotion):
    """Show a floating speech bubble near the cat"""
    response = emotion_responses.get(emotion, "I'm here with you!")

    # create bubble window
    bubble = tk.Toplevel(window)
    bubble.overrideredirect(True)
    bubble.config(bg="#fefae0", padx=10, pady=5)
    bubble.wm_attributes('-topmost', True)

    # add label to bubble
    label_bubble = tk.Label(
        bubble,
        text=response,
        font=("Comic Sans MS", 11, "bold"),
        bg="#fefae0",
        fg="#3a3a3a",
        wraplength=160,
        justify="left"
    )
    label_bubble.pack()

    # obtain cat position
    cat_x = window.winfo_x()
    cat_y = window.winfo_y()

    # bubble appears offset from cat
    bubble.geometry(f"+{cat_x + 250}+{cat_y + 50}")

    # close bubble after 3 seconds
    bubble.after(3000, bubble.destroy)

def on_emotion_from_camera(label, conf, probs):
    global current_emotion_label
    current_emotion_label = label
    print(f"[Callback] Detected {label} (conf={conf:.2f})")

def apply_emotion_to_pet():
    """
    Callback to apply detected emotion to the desktop pet every few seconds
    """
    # turn the label into pet emotion
    print(f"Emotion detected: {current_emotion_label}")
    pet_emotion = EMOTION_MAP.get(current_emotion_label, "neutral")
    print(f"Mapped to pet emotion: {pet_emotion}")
    # pop up speech bubble
    show_speech_bubble(pet_emotion)

    # schedule next emotion application
    window.after(2000, apply_emotion_to_pet)

threading.Thread(
    target=start_emotion_stream,
    kwargs={
        "callback": on_emotion_from_camera,
        "show_window": False   # do not show the camera window
    },
    daemon=True
).start()

# 0. Start loop
window.after(2000, apply_emotion_to_pet) # start emotion feedback loop after 2 seconds
window.after(2000, update, cycle, check, event_number, x)
window.mainloop()