import os, re, numpy as np, fasttext
from konlpy.tag import Okt

PAD_LEN = 800
EMB_DIM = 300

FT_PATH = os.getenv("FASTTEXT_PATH", "models/cc.ko.300.bin")
HASHTAG_RE = re.compile(r"#\S+")
STOPWORDS = [...]

_ft = None
_okt = None

def get_ft():
    global _ft
    if _ft is None:
        _ft = fasttext.load_model(FT_PATH)
    return _ft

def get_okt():
    global _okt
    if _okt is None:
        _okt = Okt()
    return _okt

def preprocess(text: str):
    text = HASHTAG_RE.sub("", text)
    okt = get_okt()
    toks = okt.morphs(text)
    return [t for t in toks if t.isalpha() and t not in STOPWORDS]

def sent2matrix(tokens):
    ft = get_ft()
    vecs = [ft.get_word_vector(t) for t in tokens[:PAD_LEN]]

    if len(vecs) < PAD_LEN:
        vecs += [np.zeros(EMB_DIM, dtype=np.float32)] * (PAD_LEN - len(vecs))

    return np.asarray(vecs, dtype=np.float32)
