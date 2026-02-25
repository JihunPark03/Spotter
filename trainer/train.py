# trainer/train.py
import os
import glob
import requests
import psycopg
import torch
from dotenv import load_dotenv
load_dotenv()

# ==============================
# CONFIG
# ==============================

DB_URL = os.getenv("DATABASE_URL")

if DB_URL.startswith("postgresql+psycopg://"):
    DB_URL = DB_URL.replace("postgresql+psycopg://", "postgresql://")

if DB_URL is None:
    raise RuntimeError("DATABASE_URL not set")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_DIR = os.path.join(BASE_DIR, "ml_server", "models")

ML_SERVER_RELOAD_URL = os.getenv(
    "ML_SERVER_RELOAD_URL",
    "http://localhost:8001/reload-model"
)

THRESHOLD = 5   # 최소 학습 데이터 수
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ==============================
# IMPORT YOUR MODEL + DATASET
# ==============================

from ml_server.model import LSTMAttn   # ml-server/model.py 동일하게 import
from trainer.build_dataset import build_dataset

# ==============================
# UTIL
# ==============================

def get_latest_model_path():
    files = sorted(glob.glob(f"{MODEL_DIR}/model_v*.pth"))
    if not files:
        raise RuntimeError("No model found")
    return files[-1]

def get_next_version():
    files = sorted(glob.glob(f"{MODEL_DIR}/model_v*.pth"))
    if not files:
        return "model_v1.pth"
    last = files[-1]
    num = int(last.split("_v")[-1].split(".")[0])
    return f"model_v{num+1}.pth"

# ==============================
# DB CHECK
# ==============================

def fetch_new_feedback():

    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT text, is_ad
        FROM feedback
        WHERE used_for_training = false
        AND verified = true
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows

# ==============================
# MARK DATA AS USED
# ==============================

def mark_feedback_used():

    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()

    cur.execute("""
        UPDATE feedback
        SET used_for_training = true
        WHERE used_for_training = false
        AND verified = true
    """)

    conn.commit()
    cur.close()
    conn.close()

# ==============================
# TRAIN LOGIC
# ==============================

def train():

    print("Checking DB for new feedback...")

    rows = fetch_new_feedback()

    if len(rows) < THRESHOLD:
        print(f"Skip training. Only {len(rows)} samples.")
        return

    print(f"Training with {len(rows)} new samples")

    texts = [r[0] for r in rows]
    labels = [r[1] for r in rows]

    dataset = build_dataset(texts, labels)

    # ===== Load Latest Model =====
    latest_model = get_latest_model_path()

    print("Loading model:", latest_model)

    model = LSTMAttn().to(DEVICE)
    model.load_state_dict(torch.load(latest_model, map_location=DEVICE))
    model.train() # change the model to training mode

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    # ===== Fine Tune =====
    for epoch in range(2):   # Production에서는 보통 짧게
        for x, y in dataset:

            x = x.to(DEVICE)
            y = y.to(DEVICE)

            logit = model(x) # 모델의 추측값인데 아직 sigmoid layer을 안 거친거
            # logit의 출력 형태는 [#x]
            logit = logit.view(-1, 1) 
            loss = loss_fn(logit, y)

            optimizer.zero_grad() # optimzer 초기화
            loss.backward() # 모든 레이어의 weight과 bias의 기울기를 저장
            optimizer.step() # weight과 bias를 업데이트

    # ===== Save New Model =====
    next_model = get_next_version()
    save_path = f"{MODEL_DIR}/{next_model}"

    torch.save(model.state_dict(), save_path)

    print("Saved new model:", save_path)

    # ===== Mark Feedback Used =====
    mark_feedback_used()

    # ===== Reload ML Server =====
    try:
        requests.post(ML_SERVER_RELOAD_URL)
        print("ML server reloaded")
    except Exception as e:
        print("Reload failed:", e)


# ==============================
# ENTRY
# ==============================

if __name__ == "__main__":
    train()
