import os
import shutil
import ffmpeg
from rembg import remove
from PIL import Image

def remove_background_from_frame(frame: Image.Image) -> Image.Image:
    """use rembg to remove background from a single frame"""
    frame_rgba = remove(frame)  
    return frame_rgba

def video_to_transparent_gif(mp4_path, gif_path, fps=15):
    """
    single video file convert to transparent gif
    """
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

    if not frames:
        print("No frames extracted, skip:", mp4_path)
        return

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
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(".mp4"):
            continue

        mp4_path = os.path.join(input_dir, fname)
        gif_name = os.path.splitext(fname)[0] + ".gif"
        gif_path = os.path.join(input_dir, gif_name)

        video_to_transparent_gif(mp4_path, gif_path, fps=fps)

if __name__ == "__main__":
    INPUT_DIR = "./doggy_gif"
    batch_convert_videos(INPUT_DIR, fps=15)
