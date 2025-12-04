# call_desktop_pet.py
import multiprocessing
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