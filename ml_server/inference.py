import torch
import numpy as np
from model import LSTMAttn
from preprocess import preprocess, sent2matrix

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

model = LSTMAttn().to(DEVICE)
model.load_state_dict(torch.load("models/model_weights.pth", map_location=DEVICE))
model.eval()

def predict_prob(text: str) -> float:
    tokens = preprocess(text) # preprocess
    mat = sent2matrix(tokens) # embedding
    x = torch.tensor(mat).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        logit = model(x)
        prob = torch.sigmoid(logit).item()
    return prob
