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
    从 pet_config.json 读取配置（如果存在）
    目前只用到 scale 和 emotion 开关，位置主要靠拖动。
    """
    cfg = {
        "scale": 0.5,      # 默认缩放
        "emotion": True,   # 默认开启摄像头
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
# 2. 主窗口类：透明 + 可拖动
# ============================

class DesktopPet(QWidget):
    def __init__(self, scale=0.5, enable_emotion=True):
        super().__init__()

        self.scale = scale
        self.enable_emotion = enable_emotion

        # 当前宠物表情（对应 ANIMATION_FILES key）
        self.current_pet_emotion = "Neutral"
        self.active_emotion = None   # 当前正在播放的动画表情

        # 拖动相关
        self.drag_position: QPoint | None = None

        # 当前气泡（顶层窗口），用于跟随移动
        self.current_bubble: QLabel | None = None

        # 窗口：无边框 + 置顶 + 透明背景
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint | # 置顶
            Qt.Tool                   # 不在 Dock / 任务栏中显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # 动画标签（显示狗狗）
        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.label.setStyleSheet("background: transparent; border: none;")

        # 表情文字标签（更大一点、更明显）
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

        # 预加载所有表情对应的 QMovie
        self.movies = {}
        self.load_movies()

        # 初始使用 Neutral 动画
        self.set_emotion("Neutral")

        # 定时检查表情是否变化（与摄像头线程共享变量）
        self.emotion_poll_timer = QTimer(self)
        self.emotion_poll_timer.timeout.connect(self.poll_emotion_state)
        self.emotion_poll_timer.start(200)

        # 定时弹出气泡
        self.bubble_timer = QTimer(self)
        self.bubble_timer.timeout.connect(self.apply_emotion_to_pet)
        self.bubble_timer.setInterval(4000)
        QTimer.singleShot(2000, self.bubble_timer.start)  # 2 秒后开始循环

        # 初始位置，之后可以拖动
        self.move(120, 600)

    # ---------- 加载动画 ----------
    def load_movies(self):
        # 根据 scale 统一缩放尺寸，比如基准 500px
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
        """切换宠物当前的动画（只在 UI 线程调用）"""
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

    # ---------- 与摄像头线程共享状态 ----------
    def on_emotion_from_camera(self, label_text, conf, probs):
        """
        被 real_time.start_emotion_stream 在线程中回调。
        注意：这里只更新 Python 变量，不直接操作 Qt GUI。
        """
        print("[desktop_pet] on_emotion_from_camera is called")
        print(f"[Callback] Detected {label_text} (conf={conf:.2f})")

        global current_emotion_label, current_pet_emotion
        current_emotion_label = label_text
        pet_emotion = EMOTION_MAP.get(label_text, "Neutral")
        current_pet_emotion = pet_emotion

        # 在实例上保存一份（由 UI 线程轮询）
        self.current_pet_emotion = pet_emotion

    def poll_emotion_state(self):
        """
        UI 线程每隔 200ms 检查 pet_emotion 是否变化，如果变了就切换动画，
        同时更新左上角的文字标签。
        """
        if self.current_pet_emotion != self.active_emotion:
            self.set_emotion(self.current_pet_emotion)

        # 更新文字标签
        self.emotion_label_widget.setText(current_emotion_label)

    # ---------- 计算气泡位置（跟随狗狗） ----------
    def _position_bubble(self, bubble: QLabel):
        pet_geo = self.frameGeometry()
        bubble_width = bubble.width()
        bubble_height = bubble.height()

        x = pet_geo.center().x() - bubble_width // 2      # 横向居中在狗狗上方
        y = pet_geo.top() - bubble_height - 20            # 在头顶上方 20px

        # 防止完全飞到屏幕外（简单保护一下）
        if y < 0:
            y = pet_geo.top() + 10

        bubble.move(x, y)

    # ---------- 气泡 ----------
    def show_speech_bubble(self, emotion: str):
        print(f"[desktop_pet] Showing speech bubble for emotion: {emotion}")
        response = emotion_responses.get(emotion, "I'm here with you!")

        # 如果已有气泡，先关掉
        if self.current_bubble is not None:
            self.current_bubble.close()
            self.current_bubble = None

        # ======== 外层黄色框（容器窗口）========
        bubble_container = QLabel()
        bubble_container.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        bubble_container.setAttribute(Qt.WA_TranslucentBackground, True)

        # 外框：淡黄色、圆角、卡通边框
        bubble_container.setStyleSheet(
            """
            QLabel {
                background-color: #FFE9A7;          /* 外框淡黄色 */
                border: 3px solid #E0A437;          /* 深黄色描边 */
                border-radius: 20px;                /* 大圆角 */
            }
            """
        )

        # ======== 内层文字框 ========
        text_label = QLabel(response, bubble_container)
        text_label.setWordWrap(True)
        text_label.setFont(QFont("Comic Sans MS", 13, QFont.Bold))
        text_label.setStyleSheet(
            """
            QLabel {
                background-color: white;             /* 内层白色框 */
                color: black;                        /* 黑色文字 */
                border-radius: 12px;                 /* 圆角 */
                padding: 10px 16px;                  /* 文字 padding */
            }
            """
        )

        # 调整大小（先让内部文字自动排版）
        text_label.adjustSize()

        # 在外框内部为文字预留 padding
        padding = 12
        bubble_container.resize(
            text_label.width() + padding * 2,
            text_label.height() + padding * 2
        )
        text_label.move(padding, padding)

        # ======== 把气泡放在狗狗头顶 ========
        self._position_bubble(bubble_container)

        bubble_container.show()
        self.current_bubble = bubble_container

        # ======== 3 秒后自动关闭 ========
        def close_if_same():
            if self.current_bubble is bubble_container:
                bubble_container.close()
                self.current_bubble = None

        QTimer.singleShot(3000, close_if_same)

    def apply_emotion_to_pet(self):
        """
        每隔一段时间，根据当前情绪弹出一次气泡
        """
        print(f"Emotion detected: {current_emotion_label}")
        print(f"Mapped to pet emotion: {current_pet_emotion}")
        self.show_speech_bubble(self.current_pet_emotion)

    # ---------- 鼠标事件：实现拖动 ----------
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

    # ---------- moveEvent：让气泡跟着狗狗一起移动 ----------
    def moveEvent(self, event):
        super().moveEvent(event)
        if self.current_bubble is not None:
            # 重新根据新的宠物位置摆放气泡
            self._position_bubble(self.current_bubble)


# ============================
# 3. 启动函数
# ============================

def main():
    cfg = load_config()
    scale = cfg["scale"]
    enable_emotion = cfg["emotion"]

    app = QApplication(sys.argv)

    pet = DesktopPet(scale=scale, enable_emotion=enable_emotion)

    # 启动摄像头情绪检测线程
    if enable_emotion:
        th = threading.Thread(
            target=start_emotion_stream,
            kwargs={
                "callback": pet.on_emotion_from_camera,
                "show_window": False,   # 如果想看摄像头，把这里改成 True
            },
            daemon=True
        )
        th.start()
        print("[desktop_pet] Emotion stream thread started.")

    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
