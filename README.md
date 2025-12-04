# ❤️ Your Emotion-Sensing Desktop Pet  
*A real-time emotion-aware virtual companion powered by deep learning.*

---

## 🐾 Overview

Your Emotion-Sensing Desktop Pet is an intelligent virtual companion that reacts to your facial expressions in real time.  
It combines **deep-learning emotion recognition**, **Tkinter animated pets**, and **speech bubble feedback** to create a personalized desktop experience.

The system supports **two control interfaces**:

1. **Streamlit Web Control Panel** (browser UI)  
2. **Tkinter + ttkbootstrap Desktop Controller UI** (standalone UI application)

You may also choose to **display or hide the camera window**, and **customize the camera preview size**.

[insert image — system architecture diagram]

---

## ✨ Features

### 🎥 Real-Time Emotion Recognition
- Uses webcam input to detect emotions continuously.
- Based on **EfficientNet-B0 + dual-head mouth model**.
- Supports 7-class FER: `Happy, Sad, Angry, Neutral, Surprise, Disgust, Fear`.
- Includes EMA smoothing + mouth-enhanced signal fusion.
- Camera window **can be enabled or disabled** using `show_window=True/False`.

### 🐶 Animated Desktop Pet
- Desktop-floating Tkinter window using transparent background.
- Supports drag-to-move, auto-topmost display.
- Multiple pets available (`westie`, `tom`).
- Each pet includes 5 emotion animations:
  - `happy_*.gif`
  - `sad_*.gif`
  - `angry_*.gif`
  - `surprise_*.gif`
  - `neutral_*.gif`

[insert image — pet example GIF]

### 💬 Emotion-Based Speech Bubbles
- Speech bubble appears near the pet every few seconds.
- The bubble includes:
  - Detected emotion label + emoji
  - Pet reaction text ("I'm here with you!", etc.)

[insert image — speech bubble example]

### 🖥 Two Controller Options  
You can choose either:

#### **1. Streamlit Control Panel**
- Launch/stop pet process
- Adjust:
  - Pet type  
  - Scale  
  - Window position  
- Preview icons included  
- Camera feed can be displayed inside Streamlit as well

[insert image — Streamlit UI screenshot]

#### **2. Tkinter / ttkbootstrap Desktop Controller**
- Native standalone UI  
- PyInstaller packaging supported  
- Allows local control without a browser  
- Includes pet previews and live parameters

[insert image — Tkinter UI screenshot]

---

## 🔧 System Architecture

```
Streamlit / Tkinter Controller 
            │
            ▼
 Multiprocessing Manager (shared state)
            │
            ├── Desktop Pet Process (Tkinter GIF engine)
            │         - Reads pet_type / scale / position
            │         - Displays animations
            │         - Shows speech bubble
            │
            └── Emotion Detection Thread (Camera)
                      - Runs model inference
                      - Sends emotion label back via callback
```

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/Hiuching-Jyu/Your-Emotion-Sensing-Desktop-Pet.git
cd Your-Emotion-Sensing-Desktop-Pet
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Usage Options

---

# Option A — **Run with Streamlit Control Panel**

Start the web-based controller:

```bash
streamlit run app.py
```

This gives you:

- Start / Stop pet  
- Choose pet type  
- Adjust scale & position  
- Enable/disable camera preview  
- Real-time emotion feed in UI  

[insert image — Streamlit dashboard]

---

# Option B — **Run with Tkinter / ttkbootstrap Desktop UI**

```bash
python tkinter_controller.py
```

This UI provides:

- A modern look (ttkbootstrap theme)
- Gif previews
- Independent process launching
- Pet settings sliders

[insert image — Tkinter controller]


---

## 🎥 Camera Window Customization

You can control size & visibility inside **real_time.py → start_emotion_stream()**.

### **Hide camera window entirely**
```python
start_emotion_stream(callback=..., show_window=False)
```

### **Show camera window with custom size**
Add this before `imshow`:

```python
cv2.namedWindow("FER-7cls", cv2.WINDOW_NORMAL)
cv2.resizeWindow("FER-7cls", 480, 300)   # Custom size
```

---

## 🧠 Emotion Model

Model: `FER7WithMouth (EfficientNet-B0 backbone)`  
Features:
- Dual-head (full face + mouth)
- EMA smoothing
- Mouth-weighted fusion
- Fear merged into Surprise (your rule)

[insert image — model architecture]

---

## 🐾 Desktop Pet Engine (Tkinter)

Features:
- Transparent background  
- Always-on-top  
- Drag to move  
- Automatic scaling  
- Independent animation thread  
- Emotion bubble every few seconds  

To modify pet GIFs, replace files in:

```
westie_gif/
tom_gif/
```

---

## 🤝 Authors

**Xiaoqing Zhu**, **Yizhou Zhang**, **Hsin Wang**  
University of Pennsylvania  
Date: **December 2025**

---

## 📜 License

MIT License — see `LICENSE` file.

---

## ⭐ Acknowledgements

- EfficientNet-B0 — PyTorch  
- MediaPipe face detection  
- Tkinter + ttkbootstrap UI framework  

---

# 💡 Future Work

- Add fine-grained emotion categories  
- Multi-pet ecosystem  
- LLM-powered chat bubble (Doubao integration)  
- Voice emotion recognition  
- Custom user-defined animations  

---

