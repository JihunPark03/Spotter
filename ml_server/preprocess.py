import os, re, numpy as np, fasttext
from konlpy.tag import Okt

PAD_LEN = 800
EMB_DIM = 300

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FT_PATH = os.getenv(
    "FASTTEXT_PATH",
    os.path.join(BASE_DIR, "models", "cc.ko.300.bin")
)
HASHTAG_RE = re.compile(r"#\S+")
STOPWORDS = [...]

_ft = None
_okt = None

def preload_assets():
    global _ft, _okt

    if _ft is None:
        print("[ML] Loading FastText...")
        _ft = fasttext.load_model(FT_PATH)

    if _okt is None:
        print("[ML] Initializing Okt...")
        _okt = Okt()


def get_ft():
    return _ft

def get_okt():
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
