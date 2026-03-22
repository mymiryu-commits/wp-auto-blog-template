"""
WP Auto-Blog v2: Main Orchestrator
핵심 변경:
- 이미지 삽입을 품질 검증 전에 실행 (점수 정확도 향상)
- 품질 기준 70점 (첫 실행 안정성)
- 재생성 시 60점으로 완화
- TENANT_ID 환경변수로 유저별 유니크 보장
"""
import os, sys, json, traceback
from datetime import datetime
from ai_writer import generate_post
from image_fetcher import insert_images
from quality_checker import check_quality
from duplicate_guard import is_duplicate, save_hash
from wp_publisher import publish_to_wordpress
from sheet_manager import get_next_keyword, update_keyword_status
from keyword_generator import auto_generate_keyword

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def main():
    log("=== WP Auto-Blog Publisher v3 시작 ===")
    wp_url = os.getenv("WP_URL")
    wp_user = os.getenv("WP_USER")
    wp_pass = os.getenv("WP_APP_PASSWORD")
    if not all([wp_url, wp_user, wp_pass]):
        log("[ERROR] WP_URL, WP_USER, WP_APP_PASSWORD 필요")
        sys.exit(1)

    tenant_id = os.getenv("TENANT_ID", f"t-{os.getenv('WP_URL','default')[-8:]}")
    log(f"  Tenant: {tenant_id}")

    # 1. 키워드 (CSV 우선 → 없으면 자동 생성)
    log("[1/6] 키워드 가져오기...")
    kw = get_next_keyword()
    
    auto_mode = False
    if not kw:
        log("  CSV 키워드 없음 → 자동 생성 모드 진입")
        auto_kw = auto_generate_keyword()
        if not auto_kw:
            log("[SKIP] 키워드 생성도 실패")
            return
        kw = {
            "keyword": auto_kw["keyword"],
            "niche": auto_kw.get("niche", "AI도구"),
            "prompt_type": auto_kw.get("prompt_type", "review"),
            "language": auto_kw.get("language", "ko"),
            "affiliate_link": "",
            "ai_model": "auto",
            "row_index": -1,
        }
        auto_mode = True
        log(f"  [AUTO] 소스: {auto_kw.get('source', 'unknown')}")
    
    keyword = kw["keyword"]; niche = kw.get("niche","general")
    prompt_type = kw.get("prompt_type","review"); language = kw.get("language","ko")
    affiliate = kw.get("affiliate_link",""); ai_model = kw.get("ai_model","auto")
    row_idx = kw.get("row_index",0)
    log(f"  키워드: {keyword} | 니치: {niche} | 언어: {language}")

    # 2. AI 글 생성
    log("[2/6] AI 글 생성...")
    result = None
    for attempt in range(3):
        try:
            result = generate_post(keyword, niche, prompt_type, language, affiliate, tenant_id, ai_model)
            log(f"  모델: {result['model_used']} | 제목: {result['title'][:50]}")
            log(f"  글자수: {len(result['content'])}자 | Temp: {result['temperature']}")
            break
        except Exception as e:
            log(f"  [RETRY {attempt+1}] {e}")
            if attempt == 2:
                log("[FAIL] AI 생성 최종 실패")
                update_keyword_status(row_idx, "failed", error=str(e))
                return

    title, content, meta = result["title"], result["content"], result["meta_description"]

    # 3. 이미지 삽입 (품질 검증 전에!)
    log("[3/6] 이미지 삽입...")
    content, img_count = insert_images(content, keyword, niche)
    log(f"  이미지 {img_count}장 삽입")

    # 4. 중복 검사
    log("[4/6] 중복 검사...")
    if is_duplicate(title, content):
        log("[SKIP] 중복 감지")
        update_keyword_status(row_idx, "duplicate")
        return
    log("  중복 아님")

    # 5. 품질 검증
    log("[5/6] 품질 검증...")
    q = check_quality(title, content, meta, keyword)
    log(f"  점수: {q['score']}/100")
    for i in q.get("issues",[]): log(f"  - {i}")

    threshold = 70
    if q["score"] < threshold:
        log(f"  품질 미달 ({q['score']}<{threshold}). 재생성 시도...")
        try:
            result = generate_post(keyword, niche, prompt_type, language, affiliate, tenant_id, ai_model)
            title, content, meta = result["title"], result["content"], result["meta_description"]
            content, img_count = insert_images(content, keyword, niche)
            q = check_quality(title, content, meta, keyword)
            log(f"  재검증: {q['score']}/100")
        except: pass
        if q["score"] < 60:
            log(f"[FAIL] 품질 미달 최종 ({q['score']}점)")
            update_keyword_status(row_idx, "failed", error=f"quality:{q['score']}")
            return

    # 6. 발행
    log("[6/6] WordPress 발행...")
    try:
        url = publish_to_wordpress(title, content, meta, wp_url, wp_user, wp_pass, [niche])
        log(f"  발행 완료: {url}")
    except Exception as e:
        log(f"[FAIL] 발행 실패: {e}")
        update_keyword_status(row_idx, "failed", error=str(e))
        return

    save_hash(title, content)
    update_keyword_status(row_idx, "published", url=url, quality_score=q["score"],
                          word_count=q["details"].get("word_count",0), ai_model=result["model_used"])
    log(f"=== 완료 | {title} | {q['score']}점 | {result['model_used']} | 이미지 {img_count}장 ===")

if __name__ == "__main__":
    try: main()
    except Exception as e:
        print(f"[CRITICAL] {e}"); traceback.print_exc(); sys.exit(1)
