"""
Desktop Pet Control Panel
------------------------------------------------
This module provides a web-based control interface for launching and managing
the emotion-responsive desktop pet. The system uses Streamlit for UI rendering
and Python multiprocessing to run the Tkinter-based pet animation in a separate
process. Shared state is synchronized through a multiprocessing Manager, 
allowing live updates of pet type, scale, and screen position.

Functionality:
- Start and stop the desktop pet as an independent process
- Select pet type and real-time adjust display scale and window position
- Preview available pets via embedded animations
- Maintain shared state for runtime parameter synchronization

Authors: Xiaoqing Zhu, Yizhou Zhang, Hsin Wang
University of Pennsylvania
Date: December 2025
"""
import streamlit as st
from multiprocessing import Process, Manager

pet_process = None
shared_state = None

# ---------------------------
# 1. Launch pet process
# ---------------------------
def launch_pet(state):
    import call_desktop_pet
    call_desktop_pet.run_pet(state)

# ---------------------------
# 2. Streamlit Web UI
# ---------------------------
def main():
    global pet_process, shared_state

    st.title("🐶 Desktop Pet Controller")
    st.write("Your desktop pet controlling panel.")

    # 2.1 Init shared state
    if shared_state is None:
        manager = Manager()
        shared_state = manager.dict({
            "running": False,
            "pet_type": "westie",
            "mode": "face",
            "scale": 1.1,
            "x": 400,
            "y": 1000,
        })

    # 2.2 Start / Stop buttons
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

    # ---------------------------
    # 2.3 Pet preview
    # ---------------------------
    st.subheader("Preview Pets")

    cols = st.columns(3)

    with cols[0]:
        st.markdown("### Westie")
        st.image("./westie_gif/preview_westie.gif", use_container_width=True)

    with cols[1]:
        st.markdown("### Tom")
        st.image("./tom_gif/preview_tom.gif", use_container_width=True)

    with cols[2]:
        st.markdown("### Panda")
        st.image("./panda_gif/preview_panda.gif", use_container_width=True)

    st.divider()

    # 2.4 Pet settings
    pet = st.selectbox("Choose Pet", ["westie", "tom", "panda"])
    shared_state["pet_type"] = pet

    # 2.5 Scale control
    scale = st.slider("Pet Scale", 0.2, 2.0, shared_state["scale"], 0.1)
    shared_state["scale"] = scale

    # 2.6 Position controls
    x = st.slider("X Position", 0, 2000, shared_state["x"])
    y = st.slider("Y Position", 0, 1200, shared_state["y"])
    shared_state["x"] = x
    shared_state["y"] = y


if __name__ == "__main__":
    main()
