"""
Sheet Manager: 키워드 관리
Supabase DB 우선 → Google Sheets 폴백 → CSV 폴백
환경에 따라 자동 선택
"""
import os
import json
import csv
from datetime import datetime

# ===== Supabase 방식 (권장) =====

def _supabase_get_next():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    tenant = os.getenv("TENANT_ID", "default")
    if not url or not key:
        return None
    
    import requests
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    
    r = requests.get(
        f"{url}/rest/v1/keywords",
        headers=headers,
        params={
            "status": "eq.pending",
            "tenant_id": f"eq.{tenant}",
            "order": "created_at.asc",
            "limit": 1,
        },
        timeout=10,
    )
    if r.status_code == 200 and r.json():
        row = r.json()[0]
        return {
            "keyword": row["keyword"],
            "niche": row.get("niche", "general"),
            "prompt_type": row.get("prompt_type", "review"),
            "ai_model": row.get("ai_model", "auto"),
            "language": row.get("language", "ko"),
            "affiliate_link": row.get("affiliate_link", ""),
            "row_index": row["id"],  # Supabase UUID
        }
    return None


def _supabase_update(row_id, status, **kwargs):
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return False
    
    import requests
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    
    data = {
        "status": status,
        "updated_at": datetime.now().isoformat(),
    }
    if "url" in kwargs:
        data["published_url"] = kwargs["url"]
    if "quality_score" in kwargs:
        data["quality_score"] = kwargs["quality_score"]
    if "word_count" in kwargs:
        data["word_count"] = kwargs["word_count"]
    if "ai_model" in kwargs:
        data["ai_model_used"] = kwargs["ai_model"]
    if "error" in kwargs:
        data["error_message"] = kwargs["error"][:500]
    
    r = requests.patch(
        f"{url}/rest/v1/keywords?id=eq.{row_id}",
        headers=headers,
        json=data,
        timeout=10,
    )
    return r.status_code in (200, 204)


# ===== CSV 폴백 (가장 간단) =====

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "keywords.csv")

def _csv_get_next():
    if not os.path.exists(CSV_PATH):
        return None
    
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    for idx, row in enumerate(rows):
        if row.get("status", "pending").strip().lower() == "pending":
            return {
                "keyword": row["keyword"],
                "niche": row.get("niche", "general"),
                "prompt_type": row.get("prompt_type", "review"),
                "ai_model": row.get("ai_model", "auto"),
                "language": row.get("language", "ko"),
                "affiliate_link": row.get("affiliate_link", ""),
                "row_index": idx,
            }
    return None


def _csv_update(row_index, status, **kwargs):
    if not os.path.exists(CSV_PATH):
        return False
    
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    if row_index < len(rows):
        rows[row_index]["status"] = status
        if "url" in kwargs:
            rows[row_index]["published_url"] = kwargs["url"]
        if "quality_score" in kwargs:
            rows[row_index]["quality_score"] = str(kwargs["quality_score"])
        if "word_count" in kwargs:
            rows[row_index]["word_count"] = str(kwargs["word_count"])
        if "ai_model" in kwargs:
            rows[row_index]["ai_model_used"] = kwargs["ai_model"]
        rows[row_index]["published_date"] = datetime.now().strftime("%Y-%m-%d")
    
    # 필드명 업데이트
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())
    fieldnames = list(all_keys)
    
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return True


# ===== Public API =====

def get_next_keyword():
    """다음 발행할 키워드 가져오기. Supabase > CSV 순서."""
    result = _supabase_get_next()
    if result:
        return result
    return _csv_get_next()


def update_keyword_status(row_index, status, **kwargs):
    """키워드 상태 업데이트."""
    # Supabase UUID면 Supabase, 정수면 CSV
    if isinstance(row_index, str) and len(row_index) > 10:
        return _supabase_update(row_index, status, **kwargs)
    return _csv_update(row_index, status, **kwargs)
