import re, numpy as np, fasttext
from konlpy.tag import Okt

PAD_LEN = 800
EMB_DIM = 300

okt = Okt()
ft = fasttext.load_model("cc.ko.300.bin")
HASHTAG_RE = re.compile(r"#\S+")

STOPWORDS = [...]  # 네가 만든 그대로

def preprocess(text: str):
    text = HASHTAG_RE.sub("", text)
    toks = okt.morphs(text)
    return [t for t in toks if t.isalpha() and t not in STOPWORDS]

def sent2matrix(tokens):
    vecs = [ft.get_word_vector(t) for t in tokens]
    if len(vecs) < PAD_LEN:
        vecs += [np.zeros(EMB_DIM)] * (PAD_LEN - len(vecs))
    else:
        vecs = vecs[:PAD_LEN]
    return np.array(vecs, dtype=np.float32)
