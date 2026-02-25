import torch
import numpy as np
import re
from pathlib import Path

from model import LSTMAttn
from preprocess import preprocess, sent2matrix

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

MODEL_DIR = Path("models")
model = None
current_model_path = None


def find_latest_model():
    # Accept both model_v#.pth and model_V#.pth, fallback to model_weights.pth
    patterns = ["model_v*.pth", "model_V*.pth"]
    files = []
    for pat in patterns:
        files.extend(MODEL_DIR.glob(pat))
    if not files:
        fallback = MODEL_DIR / "model_weights.pth"
        if fallback.exists():
            return fallback
        raise FileNotFoundError("No model weights found in models/")

    def version_key(p):
        m = re.search(r"model[_vV](\d+)\.pth", p.name)
        return int(m.group(1)) if m else -1

    return max(files, key=version_key)


def load_model():
    global model, current_model_path

    latest_path = find_latest_model()

    if model is not None and latest_path == current_model_path:
        print(f"[ML] Loading current model: {latest_path}")
        return

    print(f"[ML] Loading new model: {latest_path}")

    new_model = LSTMAttn().to(DEVICE)
    state = torch.load(latest_path, map_location=DEVICE)
    new_model.load_state_dict(state)
    new_model.eval()

    model = new_model
    current_model_path = latest_path


def predict_prob(text: str) -> float:
    load_model()

    tokens = preprocess(text)
    mat = sent2matrix(tokens)

    x = torch.from_numpy(np.array(mat)).float().unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logit = model(x)
        prob = torch.sigmoid(logit).item()

    return prob
