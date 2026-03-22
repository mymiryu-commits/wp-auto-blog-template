"""
Duplicate Guard: 3단계 중복 방지
1) 제목 SHA256 해시 비교
2) 키워드 중복 (sheet_manager에서 처리)
3) 최근 20편과 단어 집합 유사도 비교
"""
import os
import json
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "published_hashes.json")


def _load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"hashes": [], "recent_words": []}


def _save_db(db):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def is_duplicate(title, content):
    """
    중복 여부 판단.
    True = 중복 (발행하면 안 됨)
    False = 유니크 (발행 가능)
    """
    db = _load_db()
    
    # 1단계: 제목 해시 비교
    title_hash = hashlib.sha256(title.strip().lower().encode()).hexdigest()[:16]
    if title_hash in db.get("hashes", []):
        return True
    
    # 3단계: 최근 20편과 단어 유사도 (Jaccard similarity)
    content_words = set(content.lower().split())
    if len(content_words) < 10:
        return False  # 너무 짧으면 비교 의미 없음
    
    for prev_words_list in db.get("recent_words", [])[-20:]:
        prev_words = set(prev_words_list)
        if not prev_words:
            continue
        intersection = len(content_words & prev_words)
        union = len(content_words | prev_words)
        similarity = intersection / max(union, 1)
        if similarity > 0.6:
            return True
    
    return False


def save_hash(title, content):
    """발행 성공 후 해시 DB에 저장"""
    db = _load_db()
    
    # 제목 해시 추가
    title_hash = hashlib.sha256(title.strip().lower().encode()).hexdigest()[:16]
    if "hashes" not in db:
        db["hashes"] = []
    db["hashes"].append(title_hash)
    
    # 최근 단어 집합 저장 (최대 50개 유지)
    content_words = list(set(content.lower().split()))[:200]  # 단어 200개까지만
    if "recent_words" not in db:
        db["recent_words"] = []
    db["recent_words"].append(content_words)
    
    # 최대 50편 유지
    if len(db["recent_words"]) > 50:
        db["recent_words"] = db["recent_words"][-50:]
    if len(db["hashes"]) > 500:
        db["hashes"] = db["hashes"][-500:]
    
    _save_db(db)
