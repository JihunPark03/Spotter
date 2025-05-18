# ──────────────────────────────────────────────────────────────
# cosine_db.py   ★ CHANGED ★
# ──────────────────────────────────────────────────────────────
"""
1. PostgreSQL RDS 에서 (prob_ad < 0.5) & shop_type 필터로 리뷰 로드
2. 각 리뷰에 대해 Gemini 로 4-feature 추출
3. Google 'text-multilingual-embedding-002' 모델로 feature 임베딩
4. 사용자 feature 와의 cosine 유사도 평균 → 상위 k개 업소 추천
5. 결과 포맷: [{"가게": …, "이유": …, "리뷰": …}, …]
"""
from __future__ import annotations
import os, logging, json
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Sequence

import numpy as np
import psycopg
import google.generativeai as genai
from dotenv import load_dotenv

# ──────────────── 0) 설정 ────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("GOOGLE_API_KEY 환경변수가 없습니다!")

# ──────────────── 1) DB ────────────────
def _get_conn() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        autocommit=True,
    )

def _fetch_reviews(shop_type: str) -> List[Dict]:
    SQL = """
    SELECT id,
           review,
           restaurant  AS shop_name,
           prob_ad
      FROM reviews
     WHERE shop_type = %s
       AND prob_ad  < 0.5;
    """
    with _get_conn() as conn, conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(SQL, (shop_type,))
        rows = cur.fetchall()
    logger.info(f"Fetched {len(rows)} reviews for type='{shop_type}'")
    return rows

# ──────────────── 2) Prompt 로드 ────────────────
def _load_prompt() -> str:
    try:
        with open("gemini_prompt.txt", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("gemini_prompt.txt not found – fallback prompt 사용")
        return (
            "You are an extractor that outputs exactly four '-키: 값' lines "
            "(must include location)."
        )
_EXTRACT_PROMPT = _load_prompt()

# ──────────────── 3) Core 로직 ────────────────
def recommend_shops(
    shop_type: str,
    user_features: Dict[str, str],
    top_k: int = 3,
) -> List[Dict[str, Any]]:     # ★ 반환 타입 변경 ★
    reviews = _fetch_reviews(shop_type)
    if not reviews:
        return []

    # 사용자 feature 임베딩
    user_vecs = {k: _embed_text(v) for k, v in user_features.items()}

    review_scores: List[Tuple[str, float, Dict[str, str], str]] = []
    for rev in reviews:
        try:
            feats = _extract_features(rev["review"])
            rev_vecs = {k: _embed_text(v) for k, v in feats.items() if k in user_vecs}
            sims = [
                _cos(user_vecs[k], rev_vecs[k])
                for k in rev_vecs.keys()
            ]
            if sims:
                score = float(np.mean(sims))
                review_scores.append((
                    rev["shop_name"] or "NO_NAME",
                    score,
                    feats,
                    rev["review"],
                ))
        except Exception as e:
            logger.debug(f"skip review(id={rev['id']}): {e}")

    # 업소별 집계
    shop_scores, shop_reviews = defaultdict(list), defaultdict(list)
    for shop, sc, feats, origin in review_scores:
        shop_scores[shop].append(sc)
        shop_reviews[shop].append((origin, feats))

    agg = {shop: float(np.mean(scs)) for shop, scs in shop_scores.items()}
    top = sorted(agg.items(), key=lambda x: x[1], reverse=True)[:top_k]

    # Gemini 로 간단한 추천 이유 생성 & 결과 구조화  ★ NEW ★
    results: List[Dict[str, Any]] = []
    for shop, sc in top:
        reason = _make_reason(shop, user_features, shop_reviews[shop][:5])
        # 대표 리뷰는 첫 번째 리뷰 사용
        rep_review = shop_reviews[shop][0][0] if shop_reviews[shop] else ""
        results.append({
            "가게": shop,
            "이유": reason,
            "리뷰": rep_review,
        })

    return results

# ──────────────── 4) Helper ────────────────
def _extract_features(text: str) -> Dict[str, str]:
    model = genai.GenerativeModel("gemini-2.0-flash")
    rsp = model.generate_content([
        {"role": "user", "parts": [_EXTRACT_PROMPT]},
        {"role": "user", "parts": [text]},
    ])
    return parse_feature_output(rsp.text)

def parse_feature_output(s: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for ln in s.splitlines():
        if ln.startswith("-") and ":" in ln:
            k, v = ln[1:].split(":", 1)
            out[k.strip()] = v.strip()
    return out

def _embed_text(text: str) -> np.ndarray:
    """Google 'text-multilingual-embedding-002' 사용 (768-D)"""
    res = genai.embed_content(
        model="models/text-multilingual-embedding-002",
        content=text,
        task_type="SEMANTIC_SIMILARITY",
    )
    return np.asarray(res["embedding"], dtype=np.float32)

def _cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

_REASON_TMPL = (
    "사용자 선호:\n{prefs}\n\n"
    "위 조건에 따라 '{shop}'(을)를 추천하는 한 문장 근거를 한국어로 설명해줘."
)
def _make_reason(shop: str, prefs: Dict[str, str], examples: Sequence[Tuple[str, Dict]]):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        pref_txt = "\n".join(f"- {k}: {v}" for k, v in prefs.items())
        prompt = _REASON_TMPL.format(prefs=pref_txt, shop=shop)
        return model.generate_content(prompt).text.strip()
    except Exception as e:
        logger.debug(f"reason gen fail: {e}")
        return "설명 생성 실패"

# ──────────────── 5) CLI 테스트 ────────────────
if __name__ == "__main__":
    sample = {"장소": "제주", "위생": "청결한 곳", "맛": "해산물", "가격": "저렴"}
    print(json.dumps(recommend_shops("식당", sample), ensure_ascii=False, indent=2))
