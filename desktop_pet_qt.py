import os
import sys
import json
import threading

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
)
from PySide6.QtGui import QMovie, QFont
from PySide6.QtCore import Qt, QTimer, QPoint, QSize

from real_time import start_emotion_stream

print("[desktop_pet] desktop_pet.py (PySide6 version) is running")

# ============================
# 1. Global config / mapping
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

emotion_responses = {
    "Happiness": "Yay! I'm so happy with you! 😺",
    "Sadness":   "Aww... Don't worry, I'm here for you 💕",
    "Anger":     "Take a deep breath... You’ve got this 💪",
    "Surprise":  "Whoa! That was unexpected! 😸",
    "Neutral":   "Hmm... A calm day feels nice 💤"
}

# GIF 路径
IMPATH = os.path.join(os.path.dirname(__file__), "doggy_gif")

ANIMATION_FILES = {
    "Happiness": "happy_doggy.gif",
    "Sadness":   "sad_doggy.gif",
    "Anger":     "angry_doggy.gif",
    "Surprise":  "surprise_doggy.gif",
    "Neutral":   "neutral_doggy1.gif",
}


def load_config():
    """
    Read configuration from pet_config.json (if present)
    Currently only uses scale and emotion toggle; positioning is primarily achieved by dragging.
    """
    cfg = {
        "scale": 0.5,      # Default Zoom
        "emotion": True,   # Camera enabled by default
    }
    path = os.path.join(os.path.dirname(__file__), "pet_config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if data.get("scale") is not None:
                    cfg["scale"] = float(data["scale"])
                if data.get("emotion") is not None:
                    cfg["emotion"] = bool(data["emotion"])
        except Exception as e:
            print("[desktop_pet] Failed to load pet_config.json:", e)
    return cfg


# ============================
# 2. Main Window Class: Transparent + Draggable
# ============================

class DesktopPet(QWidget):
    def __init__(self, scale=0.5, enable_emotion=True):
        super().__init__()

        self.scale = scale
        self.enable_emotion = enable_emotion

        # Current pet expression (corresponding to the ANIMATION_FILES key)
        self.current_pet_emotion = "Neutral"
        self.active_emotion = None   # Currently playing animated emoji

        # Drag and drop
        self.drag_position: QPoint | None = None

        # Current bubble (top-level window), used for tracking movement
        self.current_bubble: QLabel | None = None

        # Window: Borderless + Always on Top + Transparent Background
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # Borderless
            Qt.WindowStaysOnTopHint | # Ontop
            Qt.Tool                   # Not displayed in the Dock / Taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Animated Tag (Shows a Dog)
        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.label.setStyleSheet("background: transparent; border: none;")

        # Emoticon Text Label (Larger, More Prominent)
        self.emotion_label_widget = QLabel("Neutral", self)
        self.emotion_label_widget.setStyleSheet(
            """
            QLabel {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 14px;
                font-weight: bold;
            }
            """
        )
        self.emotion_label_widget.move(10, 10)
        self.emotion_label_widget.show()

        # Preload all corresponding QMovie files for all emojis
        self.movies = {}
        self.load_movies()

        # Initially use Neutral animation
        self.set_emotion("Neutral")

        # Periodically check for facial expression changes (using variables shared with the camera thread)
        self.emotion_poll_timer = QTimer(self)
        self.emotion_poll_timer.timeout.connect(self.poll_emotion_state)
        self.emotion_poll_timer.start(200)

        # Scheduled Pop-up Bubble
        self.bubble_timer = QTimer(self)
        self.bubble_timer.timeout.connect(self.apply_emotion_to_pet)
        self.bubble_timer.setInterval(4000)
        QTimer.singleShot(2000, self.bubble_timer.start)  # Loop begins in 2 seconds

        # Initial position, which can be dragged afterward
        self.move(120, 600)

    # ---------- Loading Animation ----------
    def load_movies(self):
        # Uniformly scale dimensions based on the scale value, such as a baseline of 500px
        base_size = 500
        target_size = int(base_size * self.scale)
        target_qsize = QSize(target_size, target_size)

        for emo, filename in ANIMATION_FILES.items():
            path = os.path.join(IMPATH, filename)
            if not os.path.exists(path):
                print(f"[desktop_pet] WARNING: GIF not found for {emo}: {path}")
                continue

            movie = QMovie(path)
            movie.setScaledSize(target_qsize)
            self.movies[emo] = movie

    def set_emotion(self, pet_emotion: str):
        """Switch the pet's current animation (only call on the UI thread)"""
        if pet_emotion not in self.movies:
            pet_emotion = "Neutral"

        if pet_emotion == self.active_emotion:
            return

        movie = self.movies.get(pet_emotion)
        if movie is None:
            return

        print(f"[desktop_pet] Switching emotion animation to: {pet_emotion}")
        self.active_emotion = pet_emotion
        self.label.setMovie(movie)
        movie.start()
        self.label.adjustSize()
        self.resize(self.label.sizeHint())

    # ---------- Sharing State with the Camera Thread ----------
    def on_emotion_from_camera(self, label_text, conf, probs):
        """
        Called back in the thread by real_time.start_emotion_stream.
Note: This only updates Python variables and does not directly manipulate the Qt GUI.
        """
        print("[desktop_pet] on_emotion_from_camera is called")
        print(f"[Callback] Detected {label_text} (conf={conf:.2f})")

        global current_emotion_label, current_pet_emotion
        current_emotion_label = label_text
        pet_emotion = EMOTION_MAP.get(label_text, "Neutral")
        current_pet_emotion = pet_emotion

        # Keep one copy on the instance (polled by the UI thread)
        self.current_pet_emotion = pet_emotion

    def poll_emotion_state(self):
        """
        The UI thread checks for changes in pet_emotion every 200ms. If it has changed, it switches the animation
        and simultaneously updates the text label in the top-left corner.
        """
        if self.current_pet_emotion != self.active_emotion:
            self.set_emotion(self.current_pet_emotion)

        # Update text labels
        self.emotion_label_widget.setText(current_emotion_label)

    # Calculate bubble position (follow dog)
    def _position_bubble(self, bubble: QLabel):
        pet_geo = self.frameGeometry()
        bubble_width = bubble.width()
        bubble_height = bubble.height()

        x = pet_geo.center().x() - bubble_width // 2      # Horizontally centered above the dog
        y = pet_geo.top() - bubble_height - 20            # 20px above the top

        # Prevent it from flying completely off the screen (just a simple safeguard)
        if y < 0:
            y = pet_geo.top() + 10

        bubble.move(x, y)

    # Bubbles
    def show_speech_bubble(self, emotion: str):
        print(f"[desktop_pet] Showing speech bubble for emotion: {emotion}")
        response = emotion_responses.get(emotion, "I'm here with you!")

        # If bubbles are already present, turn it off first.
        if self.current_bubble is not None:
            self.current_bubble.close()
            self.current_bubble = None

        # ======== Outer Yellow Frame (Container Window) ========
        bubble_container = QLabel()
        bubble_container.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        bubble_container.setAttribute(Qt.WA_TranslucentBackground, True)

        # Outer Frame: Light Yellow, Rounded Corners, Cartoon Border
        bubble_container.setStyleSheet(
            """
            QLabel {
                background-color: #FFE9A7;          /* Outer frame light yellow */
                border: 3px solid #E0A437;          /* Deep yellow outline */
                border-radius: 20px;                /* Large Radius */
            }
            """
        )

        # ======== Inner Text Box ========
        text_label = QLabel(response, bubble_container)
        text_label.setWordWrap(True)
        text_label.setFont(QFont("Comic Sans MS", 13, QFont.Bold))
        text_label.setStyleSheet(
            """
            QLabel {
                background-color: white;             /* Inner white frame */
                color: black;                        /* Black text */
                border-radius: 12px;                 /* Rounded corners */
                padding: 10px 16px;                  /* Text padding */
            }
            """
        )

        # Resize (first let the internal text auto-layout)
        text_label.adjustSize()

        # Reserve padding for text within the outer frame.
        padding = 12
        bubble_container.resize(
            text_label.width() + padding * 2,
            text_label.height() + padding * 2
        )
        text_label.move(padding, padding)

        # ======== Place the bubble above the pet's head ========
        self._position_bubble(bubble_container)

        bubble_container.show()
        self.current_bubble = bubble_container

        # Automatically closes in 3 seconds
        def close_if_same():
            if self.current_bubble is bubble_container:
                bubble_container.close()
                self.current_bubble = None

        QTimer.singleShot(3000, close_if_same)

    def apply_emotion_to_pet(self):
        """
        Every so often, a bubble pops up based on your current mood.
        """
        print(f"Emotion detected: {current_emotion_label}")
        print(f"Mapped to pet emotion: {current_pet_emotion}")
        self.show_speech_bubble(self.current_pet_emotion)

    # Mouse Events: Implementing Drag & Drop
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        event.accept()

    # ---------- moveEvent: Make the bubble follow the dog's movement ----------
    def moveEvent(self, event):
        super().moveEvent(event)
        if self.current_bubble is not None:
            # Rearrange the bubbles according to the new pet positions.
            self._position_bubble(self.current_bubble)


# ============================
# 3. Startup Function
# ============================

def main():
    cfg = load_config()
    scale = cfg["scale"]
    enable_emotion = cfg["emotion"]

    app = QApplication(sys.argv)

    pet = DesktopPet(scale=scale, enable_emotion=enable_emotion)

    # Launch the camera emotion detection thread
    if enable_emotion:
        th = threading.Thread(
            target=start_emotion_stream,
            kwargs={
                "callback": pet.on_emotion_from_camera,
                "show_window": False,
            },
            daemon=True
        )
        th.start()
        print("[desktop_pet] Emotion stream thread started.")

    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
