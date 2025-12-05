from rembg import remove
from PIL import Image
import numpy as np
import cv2
import os
import shutil
import ffmpeg

def remove_background_from_frame(frame: Image.Image) -> Image.Image:
    """use rembg to remove background & enhance alpha mask"""
    
    # step 1: 原始输出
    out = remove(frame)
    out_np = np.array(out)

    # 取 alpha 通道
    alpha = out_np[:, :, 3]

    # step 2: 强化 alpha，让它更 solid
    # 二值化：防止边缘半透明
    _, alpha_bin = cv2.threshold(alpha, 127, 255, cv2.THRESH_BINARY)
    # step 2.5: 轻微膨胀，填补边缘毛刺
    kernel_edge = np.ones((3, 3), np.uint8)
    alpha_dilated = cv2.dilate(alpha_bin, kernel_edge, iterations=1)

    # 再用 dilated 的 alpha 走下面流程
    alpha = alpha_dilated
    # step 3: 形态学操作：填洞 & 去噪点
    kernel = np.ones((6, 6), np.uint8)

    # 填补小孔洞
    alpha_closed = cv2.morphologyEx(alpha , cv2.MORPH_CLOSE, kernel)

    # 去掉小碎点
    alpha_opened = cv2.morphologyEx(alpha_closed, cv2.MORPH_OPEN, kernel)
    solid_alpha = np.where(alpha_opened > 0, 255, 0).astype(np.uint8)
    # step 4: 用增强后的 alpha 替换回去
    out_np[:, :, 3] = solid_alpha

    # 返回增强后的 RGBA
    return Image.fromarray(out_np)

def video_to_transparent_gif(mp4_path, gif_path, fps=15):
    """
    single video file convert to transparent gif
    """
    print(f"\nConverting video to transparent GIF:\n  Input: {mp4_path}\n  Output: {gif_path}")
    
    temp_frames_dir = "temp_frames"

    # create temp dir for frames
    if os.path.exists(temp_frames_dir):
        shutil.rmtree(temp_frames_dir)
    os.makedirs(temp_frames_dir, exist_ok=True)

    print(f"Extracting frames from: {mp4_path}")
    (
        ffmpeg
        .input(mp4_path)
        .filter('fps', fps)
        .output(f"{temp_frames_dir}/frame_%04d.png")
        .run(overwrite_output=True)
    )

    print("Removing background for each frame...")
    
    frames = []
    for file in sorted(os.listdir(temp_frames_dir)):
        if not file.lower().endswith(".png"):
            continue
        img_path = os.path.join(temp_frames_dir, file)
        frame = Image.open(img_path).convert("RGBA")
        frame_no_bg = remove_background_from_frame(frame)
        frames.append(frame_no_bg)
    
    processed_frames = []
    for f in frames:
        rgba = np.array(f)

        # 把透明区域强制变成纯白（避免黑色背景）
        rgba[rgba[:, :, 3] == 0] = [255, 255, 255, 0]

        processed_frames.append(
            Image.fromarray(rgba).convert("P", palette=Image.ADAPTIVE, colors=128)
        )


    if not frames:
        print("No frames extracted, skip:", mp4_path)
        return
    
    # convert frames to 'P' mode with adaptive palette for transparency
    frames = processed_frames

    # 强制 index 0 为透明像素
    palette = frames[0].getpalette()
    frames[0].putpalette(palette)

    # 设置 GIF 中 index 0 为透明
    frames[0].info['transparency'] = 0
    print(f"Saving transparent GIF to: {gif_path}")
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=int(1000 / fps),  # duration per frame in ms
        loop=0,
        transparency=0,
        disposal=2,
    )

    # delete temp frames
    shutil.rmtree(temp_frames_dir)
    print("Done.\n")

def batch_convert_videos(input_dir, fps=15):
    """
    transfer the mp4 videos in input_dir to transparent gifs
    """
    print(f"Batch converting videos in directory: {input_dir}")
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(".mp4"):
            continue

        mp4_path = os.path.join(input_dir, fname)
        emotion = fname.replace("", "_tom").replace(".mp4", "")
        gif_name = f"{emotion}_tom.gif"
        gif_path = os.path.join(input_dir, gif_name)

        video_to_transparent_gif(mp4_path, gif_path, fps=fps)


if __name__ == "__main__":
    INPUT_DIR = "./tom_gif"
    batch_convert_videos(INPUT_DIR, fps=15)
