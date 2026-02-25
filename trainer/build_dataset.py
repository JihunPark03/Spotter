# trainer/build_dataset.py

import torch
from torch.utils.data import DataLoader, TensorDataset

from ml_server.preprocess import preprocess, sent2matrix

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def build_dataset(texts, labels):

    xs = []
    ys = []

    for t, l in zip(texts, labels):
        if not isinstance(t, str):
            continue

        t = t.strip()

        if not t:
            continue
        toks = preprocess(t)
        mat = sent2matrix(toks)
        xs.append(mat)
        ys.append([l])

    x_tensor = torch.tensor(xs, dtype=torch.float32)
    y_tensor = torch.tensor(ys, dtype=torch.float32)

    ds = TensorDataset(x_tensor, y_tensor)

    return DataLoader(ds, batch_size=32, shuffle=True)
