import torch
import torch.nn as nn

class LSTMAttn(nn.Module):
    def __init__(self, in_dim=300, hid=32, seq_len=800):
        super().__init__()
        self.lstm = nn.LSTM(in_dim, hid, batch_first=True)
        self.w_attn = nn.Linear(seq_len, seq_len, bias=False)
        self.fc = nn.Linear(hid * seq_len, 1)
        self.flat = nn.Flatten()

    def forward(self, x):
        h, _ = self.lstm(x)
        p = h.permute(0, 2, 1)
        q = self.w_attn(p)
        attn = h * q.permute(0, 2, 1)
        logit = self.fc(self.flat(attn))
        return logit.squeeze(1)
