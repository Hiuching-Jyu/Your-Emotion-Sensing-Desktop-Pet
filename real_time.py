import cv2
import numpy as np
import torch
from torch import nn
from torchvision.models import efficientnet_b0
import time

# =========================
# 0. Configurations
# =========================
MODEL_PATH = "affectnet_model.pth"


emotion_labels = [
    "Angry",      # 0
    "Disgust",    # 1
    "Fear",       # 2
    "Happy",      # 3
    "Neutral",    # 4
    "Sad",        # 5
    "Surprise"    # 6
]

device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

# ===============================================
# 1. Define the model architecture same as training
# ===============================================
class FER7WithMouth(nn.Module):
    """
    EfficientNet-B0 backbone + dual heads (full face + mouth)
    """
    def __init__(self, backbone, num_classes=7):
        super().__init__()
        self.backbone = backbone  #

        # Main head: full face
        self.head_main = nn.Sequential(
            nn.Linear(1280, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )

        # Secondary head: mouth only
        self.head_mouth = nn.Sequential(
            nn.Linear(1280, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )

    def forward(self, x_full, x_mouth):
        feat_full = self.backbone(x_full)    # [B, 1280]
        feat_mouth = self.backbone(x_mouth)  # [B, 1280]

        logits_main = self.head_main(feat_full)
        logits_mouth = self.head_mouth(feat_mouth)
        return logits_main, logits_mouth

    def forward_main(self, x_full):
        feat_full = self.backbone(x_full)
        return self.head_main(feat_full)


# construct backbone
base = efficientnet_b0(weights=None)
base.classifier = nn.Identity()

# construct full model
model = FER7WithMouth(base, num_classes=7).to(device)

# load weights
state = torch.load(MODEL_PATH, map_location=device)
model.load_state_dict(state, strict=True)
model.eval()
print("Loaded model from", MODEL_PATH)


# =========================
# 2. Preprocessing functions
# =========================
IMG_SIZE = 224

mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def preprocess_full(face_bgr):
    """
    Full face preprocessing: BGR -> RGB -> [0,1] -> normalize -> CHW torch float32
    """
    face = cv2.resize(face_bgr, (IMG_SIZE, IMG_SIZE))
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    face = face.astype(np.float32) / 255.0
    face = (face - mean) / std
    face = np.transpose(face, (2, 0, 1))  # HWC -> CHW
    tensor = torch.from_numpy(face).unsqueeze(0)  # [1,3,H,W]
    return tensor.float()   


def crop_mouth_np(face_bgr):
    """
    Simple mouth ROI: take the lower half of the face, similar to training's lower 45%
    face_bgr: np.ndarray [H,W,3]
    """
    h, w, _ = face_bgr.shape
    top = int(0.55 * h)  # define top boundary
    mouth = face_bgr[top:h, :, :]
    if mouth.size == 0:
        # if face is too small, fallback to full face
        mouth = face_bgr
    return mouth


def preprocess_mouth(face_bgr):
    """
    mouth processing: crop mouth -> BGR -> RGB -> [0,1] -> normalize -> CHW torch float32
    """
    mouth = crop_mouth_np(face_bgr)
    mouth = cv2.resize(mouth, (IMG_SIZE, IMG_SIZE))
    mouth = cv2.cvtColor(mouth, cv2.COLOR_BGR2RGB)
    mouth = mouth.astype(np.float32) / 255.0
    mouth = (mouth - mean) / std
    mouth = np.transpose(mouth, (2, 0, 1))
    tensor = torch.from_numpy(mouth).unsqueeze(0)
    return tensor.float()


# =========================
# 3. Face detector class
# =========================
class FaceDetector:
    def __init__(self, min_conf=0.6):
        try:
            import mediapipe as mp
            self.mode = "mediapipe"
            self.mp = mp
            self.detector = mp.solutions.face_detection.FaceDetection(
                model_selection=1,
                min_detection_confidence=min_conf
            )
            print("Using MediaPipe face detector")
        except Exception as e:
            print("MediaPipe not available, fallback to Haar cascade. Error:", e)
            self.mode = "haar"
            self.detector = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

    def detect(self, frame):
        H, W = frame.shape[:2]
        boxes = []

        if self.mode == "mediapipe":
            res = self.detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if res.detections:
                for det in res.detections:
                    r = det.location_data.relative_bounding_box
                    x1 = int(r.xmin * W)
                    y1 = int(r.ymin * H)
                    x2 = int((r.xmin + r.width) * W)
                    y2 = int((r.ymin + r.height) * H)
                    boxes.append((x1, y1, x2 - x1, y2 - y1))
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector.detectMultiScale(gray, 1.1, 5)
            for (x, y, w, h) in faces:
                boxes.append((x, y, w, h))

        return boxes


# =========================
# 4. Real-time inference loop (face + mouth)
# =========================
def start_emotion_stream(callback=None, show_window=True, frame_holder=None, state=None):
    print("[real_time] Starting emotion detection stream...")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open camera")
        return

    cap.set(3, 1280)
    cap.set(4, 720)
    detector = FaceDetector()

    ema_probs = None
    ema_alpha = 0.7
    MOUTH_ALPHA = 0.5
    prev_time = time.time()
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        boxes = detector.detect(frame)
        label_text = "No face"
        emotion_label = None
        conf = 0.0

        if len(boxes) > 0:
            # take the largest face
            areas = [w * h for (x, y, w, h) in boxes]
            idx = int(np.argmax(areas))
            x, y, w, h = boxes[idx]

            pad = int(0.15 * max(w, h))
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(frame.shape[1], x + w + pad)
            y2 = min(frame.shape[0], y + h + pad)

            face = frame[y1:y2, x1:x2]

            if face.size > 0:
                full_t = preprocess_full(face).to(device)
                mouth_t = preprocess_mouth(face).to(device)

                with torch.no_grad():
                    logits_main, logits_mouth = model(full_t, mouth_t)
                    logits = logits_main + MOUTH_ALPHA * logits_mouth
                    probs = torch.softmax(logits, dim=1)[0].cpu().numpy().astype(np.float32)

                # ---- smoothing ----
                if ema_probs is None:
                    ema_probs = probs
                else:
                    ema_probs = ema_alpha * ema_probs + (1 - ema_alpha) * probs

                # merge Fear into Surprise (your original logic)
                ema_probs[6] += ema_probs[2]
                ema_probs[2] = 0

                cls = int(np.argmax(ema_probs))
                conf = float(ema_probs[cls])
                emotion_label = emotion_labels[cls]

                label_text = f"{emotion_label} {conf*100:.1f}%"

                # ---- callback for desktop pet ----
                if callback is not None:
                    callback(emotion_label, conf, ema_probs.copy())

                # ---- write to shared_state (for Streamlit UI) ----
                if state is not None:
                    state["detected_emotion"] = emotion_label
        else:
            # 没检测到脸，也告诉 state
            if state is not None:
                state["detected_emotion"] = "No face"

        # ---- send frame to Streamlit ----
        if frame_holder is not None:
            frame_holder["frame"] = frame.copy()

        # FPS calculation
        now = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / (now - prev_time))
        prev_time = now

        if show_window:
            cv2.putText(frame, label_text, (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.putText(frame, f"FPS: {fps:.1f}", (20,40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,255), 2)

            cv2.imshow("FER-7cls", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            cv2.waitKey(1)

    cap.release()
    cv2.destroyAllWindows()


print("Starting emotion detection stream...")
