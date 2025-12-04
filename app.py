import streamlit as st
from multiprocessing import Process, Manager
import time
import os
import threading
from streamlit_js_eval import streamlit_js_eval

# ---- 全局存储桌宠进程 ----
pet_process = None
shared_state = None

# ---------------------------
# 启动桌宠进程
# ---------------------------
def launch_pet(state):
    """
    这里不直接 import desktop_pet，因为 Tkinter 必须在新进程运行。
    我们在桌宠脚本内部读取 shared_state。
    """
    import call_desktop_pet
    call_desktop_pet.run_pet(state)


# ---------------------------
# Streamlit Web UI
# ---------------------------
def main():
    global pet_process, shared_state

    st.title("🐶 Desktop Pet Controller")
    st.write("Your desktop pet controlling panel.")

    # 初始化共享状态
    if shared_state is None:
        manager = Manager()
        shared_state = manager.dict({
            "running": False,
            "pet_type": "westie",
            "scale": 1.1,
            "x": 400,
            "y": 1000,
        })

    # ---- 控制启动/停止 ----
    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶ Start Pet"):
            if pet_process is None or not pet_process.is_alive():
                shared_state["running"] = True
                pet_process = Process(target=launch_pet, args=(shared_state,))
                pet_process.start()
                st.success("Pet started!")

    with col2:
        if st.button("⏹ Stop Pet"):
            if pet_process is not None and pet_process.is_alive():
                shared_state["running"] = False
                pet_process.terminate()
                pet_process = None
                st.warning("Pet stopped.")

    st.divider()

    # ---- 选择宠物 ----
    pet = st.selectbox("Choose Pet", ["westie"])
    shared_state["pet_type"] = pet

    # ---- 缩放 ----
    scale = st.slider("Pet Scale", 0.2, 2.0, shared_state["scale"], 0.1)
    shared_state["scale"] = scale

    # ---- 位置控制 ----
    x = st.slider("X Position", 0, 2000, shared_state["x"])
    y = st.slider("Y Position", 0, 1200, shared_state["y"])
    shared_state["x"] = x
    shared_state["y"] = y



if __name__ == "__main__":
    main()