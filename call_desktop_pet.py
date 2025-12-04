# call_desktop_pet.py
import multiprocessing
import time
import threading

def run_pet(state):
    """
    启动桌宠：在这里导入 desktop_pet.py 让它运行
    不能在主进程 import desktop_pet，否则会卡住 Streamlit
    """

    print("[call_desktop_pet] Starting pet...")

    # 因为 desktop_pet.py 是一个完整程序 (Tk + mainloop)，导入后会直接运行
    import desktop_pet
    desktop_pet.start_pet(state)

    # 开启一个线程持续同步位置与大小
    def sync_state():
        while True:
            try:
                # 从共享 state 提取位置与缩放
                x = state["x"]
                y = state["y"]
                scale = state["scale"]

                # 更新 Tkinter 窗口
                desktop_pet.window.geometry(f"+{x}+{y}")

                # 更新缩放（需要你在 desktop_pet 里接收，我已提示修改）
                desktop_pet.scale = scale

            except Exception as e:
                print("[call_desktop_pet] Sync error:", e)

            time.sleep(0.2)  # 每 200ms 同步一次

    threading.Thread(target=sync_state, daemon=True).start()