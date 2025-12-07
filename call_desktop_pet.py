"""
Desktop Pet Runtime Bridge
--------------------------
This module serves as the process-level bridge between the controller UI and
the Tkinter-based desktop pet engine. It launches the pet runtime, forwards
shared state updates, and continuously synchronizes window position and scale
through a background thread.

Authors: Xiaoqing Zhu, Yizhou Zhang, Hsin Wang
University of Pennsylvania
Date: December 2025
"""

import time
import threading


# ============================
# 1. Run Desktop Pet
# ============================
def run_pet(state):

    print("[call_desktop_pet] Starting pet...")

    import desktop_pet
    desktop_pet.start_pet(state)

    # Turn on a thread to sync position and scale from shared state
    def sync_state():
        while True:
            try:
                # extract position and scale
                x = state["x"]
                y = state["y"]
                scale = state["scale"]

                # update position
                desktop_pet.window.geometry(f"+{x}+{y}")

                # update scale
                desktop_pet.scale = scale

            except Exception as e:
                print("[call_desktop_pet] Sync error:", e)

            time.sleep(0.2)  # sync every 200ms

    threading.Thread(target=sync_state, daemon=True).start()