from rembg import remove
from PIL import Image
import numpy as np
import cv2
import os
import shutil
import ffmpeg

def remove_background_from_frame(frame: Image.Image) -> Image.Image:
    """use rembg to remove background & enhance alpha mask"""
    
    # Step 1: Original Output
    out = remove(frame)
    out_np = np.array(out)

    # Retrieve the alpha channel
    alpha = out_np[:, :, 3]

    # Step 2: Strengthen alpha to make it more solid
    # Binarization: Preventing edge transparency
    _, alpha_bin = cv2.threshold(alpha, 127, 255, cv2.THRESH_BINARY)
    # Step 2.5: Slightly expand to fill in edge burrs.
    kernel_edge = np.ones((3, 3), np.uint8)
    alpha_dilated = cv2.dilate(alpha_bin, kernel_edge, iterations=1)

    # Then proceed with the following steps using the dilated alpha.
    alpha = alpha_dilated
    # Step 3: Morphological Operations: Hole Filling & Noise Removal
    kernel = np.ones((6, 6), np.uint8)

    # Fill small holes
    alpha_closed = cv2.morphologyEx(alpha , cv2.MORPH_CLOSE, kernel)

    # Remove the small specks
    alpha_opened = cv2.morphologyEx(alpha_closed, cv2.MORPH_OPEN, kernel)
    solid_alpha = np.where(alpha_opened > 0, 255, 0).astype(np.uint8)
    # Step 4: Replace it with the enhanced alpha.
    out_np[:, :, 3] = solid_alpha

    # Return the enhanced RGBA
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

        # turn transparent pixels to index 0
        rgba[rgba[:, :, 3] == 0] = [255, 255, 255, 0]

        processed_frames.append(
            Image.fromarray(rgba).convert("P", palette=Image.ADAPTIVE, colors=128)
        )


    if not frames:
        print("No frames extracted, skip:", mp4_path)
        return
    
    # convert frames to 'P' mode with adaptive palette for transparency
    frames = processed_frames

    # force same palette for all frames
    palette = frames[0].getpalette()
    frames[0].putpalette(palette)

    # set transparency index
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
        emotion = fname.replace("", "_panda").replace(".mp4", "")
        gif_name = f"{emotion}_panda.gif"
        gif_path = os.path.join(input_dir, gif_name)

        video_to_transparent_gif(mp4_path, gif_path, fps=fps)


if __name__ == "__main__":
    INPUT_DIR = "./panda_gif"
    # batch_convert_videos(INPUT_DIR, fps=15)
    video_to_transparent_gif(
        mp4_path="./panda_gif/preview_panda.mp4",gif_path="./panda_gif/preview_panda.gif", fps=15)
