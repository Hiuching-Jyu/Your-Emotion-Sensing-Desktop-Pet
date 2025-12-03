# ❤️ Your Emotion-Sensing Desktop Pet  
*A real-time emotion-aware virtual companion powered by deep learning.*

## 🐾 Project Overview

Your Emotion-Sensing Desktop Pet is an interactive virtual companion that reacts to your facial expressions in real time.  
Using a deep-learning emotion recognition model and an animated Tkinter desktop pet, the pet changes its behavior and displays speech bubbles based on your detected emotions.

This project combines:

- Real-time webcam emotion detection  
- Tkinter-based animated desktop pet  
- Emotion-driven reactions  
- Floating speech bubbles that respond to your mood  

> ⚠️ The emotion classification model is currently being updated to improve accuracy and expand supported emotion categories.

---

## ✨ Features

### 🎥 Real-Time Emotion Recognition
- Detects facial emotion continuously via webcam.
- Outputs label, confidence score, and full probability vector.
- Supports emotions such as **Happy, Sad, Angry, Neutral, Surprise**, etc.

### 🐶 Animated Desktop Pet
- A cute floating pet that stays on top of your desktop.
- Includes idle, sleep, and walking animations.
- Moves and animates independently of the emotion system.

### 💬 Emotion-Based Reactions
- Every few seconds, the pet reacts to your detected emotion.
- Displays a floating speech bubble (e.g., comforting you when sad, celebrating when happy).

### 🔄 Continuous Background Threads
- Emotion detection runs in a background thread.
- UI animations remain smooth and responsive.

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Hiuching-Jyu/Your-Emotion-Sensing-Desktop-Pet.git
cd Your-Emotion-Sensing-Desktop-Pet
