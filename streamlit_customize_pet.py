import streamlit as st
import subprocess
import json
import os

st.set_page_config(page_title="Desktop Pet Launcher", page_icon="🐶")

st.title("🐾 桌宠启动器 Desktop Pet Launcher")

# === 1. 选择宠物类型 ===
pet_type = st.selectbox(
    "选择宠物类型",
    options=["west_dog", "cat_orange", "cat_black", "dog_corgi"],
    index=0
)

# === 2. 选择宠物位置 ===
position = st.selectbox(
    "选择宠物位置",
    options=["左下", "右下", "左上", "右上", "自定义"],
)

custom_x = custom_y = None
if position == "自定义":
    custom_x = st.number_input("X 坐标 (px)", value=200)
    custom_y = st.number_input("Y 坐标 (px)", value=300)

# === 3. 选择宠物大小 (缩放倍数) ===
scale = st.slider("宠物大小（缩放倍数）", 0.3, 3.0, 1.0, 0.1)

# === 4. 选择情绪检测是否开启 ===
enable_emotion = st.checkbox("开启摄像头情绪检测", value=True)

# === 5. 写入配置文件 ===
config = {
    "pet_type": pet_type,
    "position": position,
    "custom_x": custom_x,
    "custom_y": custom_y,
    "scale": scale,
    "emotion": enable_emotion,
}

if st.button("🚀 启动桌宠"):
    with open("pet_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    # 启动 Tkinter 桌宠脚本
    subprocess.Popen(["python", "desktop_pet.py"])

    st.success("桌宠已启动！请在桌面查看 🐾")
