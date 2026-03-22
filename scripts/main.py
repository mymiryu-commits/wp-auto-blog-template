"""
WP Auto-Blog: Main Orchestrator
GitHub Actions에서 실행되는 메인 스크립트.
키워드 가져오기 → AI 글 생성 → 품질 검증 → 이미지 삽입 → WP 발행
"""
import os
import sys
import json
import time
import traceback
from datetime import datetime

from ai_writer import generate_post
from image_fetcher import insert_images
from quality_checker import check_quality
from duplicate_guard import is_duplicate, save_hash
from wp_publisher import publish_to_wordpress
from sheet_manager import get_next_keyword, update_keyword_status

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def main():
    log("=== WP Auto-Blog Publisher 시작 ===")

    # 환경변수 확인
    wp_url = os.getenv("WP_URL")
    wp_user = os.getenv("WP_USER")
    wp_pass = os.getenv("WP_APP_PASSWORD")
    
    if not all([wp_url, wp_user, wp_pass]):
        log("[ERROR] WP_URL, WP_USER, WP_APP_PASSWORD 환경변수 필요")
        sys.exit(1)

    # Supabase에서 설정 가져오기 (또는 환경변수 폴백)
    tenant_id = os.getenv("TENANT_ID", "default")
    
    # 1. 키워드 가져오기
    log("[1/7] 키워드 가져오기...")
    keyword_data = get_next_keyword()
    if not keyword_data:
        log("[SKIP] 대기 중인 키워드가 없습니다.")
        return

    keyword = keyword_data["keyword"]
    niche = keyword_data.get("niche", "general")
    prompt_type = keyword_data.get("prompt_type", "review")
    ai_model = keyword_data.get("ai_model", "auto")
    language = keyword_data.get("language", "ko")
    affiliate_link = keyword_data.get("affiliate_link", "")
    row_index = keyword_data.get("row_index", 0)
    
    log(f"  키워드: {keyword}")
    log(f"  니치: {niche} | 유형: {prompt_type} | 언어: {language}")

    # 2. AI 글 생성 (멀티 AI 로테이션)
    log("[2/7] AI 글 생성...")
    max_retries = 2
    title, content, meta_desc, used_model = None, None, None, None
    
    for attempt in range(max_retries + 1):
        try:
            result = generate_post(
                keyword=keyword,
                niche=niche,
                prompt_type=prompt_type,
                language=language,
                affiliate_link=affiliate_link,
                tenant_id=tenant_id,
                preferred_model=ai_model,
            )
            title = result["title"]
            content = result["content"]
            meta_desc = result["meta_description"]
            used_model = result["model_used"]
            log(f"  AI 모델: {used_model}")
            log(f"  제목: {title}")
            log(f"  글자수: {len(content)}자")
            break
        except Exception as e:
            log(f"  [RETRY {attempt+1}] AI 생성 실패: {e}")
            if attempt == max_retries:
                log("[FAIL] AI 글 생성 최종 실패")
                update_keyword_status(row_index, "failed", error=str(e))
                return

    # 3. 중복 검사
    log("[3/7] 중복 검사...")
    if is_duplicate(title, content):
        log("[SKIP] 중복 콘텐츠 감지. 다음 키워드로 넘어갑니다.")
        update_keyword_status(row_index, "duplicate")
        return
    log("  중복 아님 (통과)")

    # 4. 품질 검증
    log("[4/7] 품질 검증...")
    quality = check_quality(title, content, meta_desc, keyword)
    log(f"  품질 점수: {quality['score']}/100")
    
    if quality["score"] < 80:
        log(f"  [WARN] 품질 미달 ({quality['score']}점). 재생성 시도...")
        # 재생성 1회 시도
        try:
            result = generate_post(
                keyword=keyword, niche=niche, prompt_type=prompt_type,
                language=language, affiliate_link=affiliate_link,
                tenant_id=tenant_id, preferred_model=ai_model,
            )
            title, content, meta_desc = result["title"], result["content"], result["meta_description"]
            quality = check_quality(title, content, meta_desc, keyword)
            log(f"  재검증 점수: {quality['score']}/100")
        except Exception:
            pass
        
        if quality["score"] < 80:
            log("[FAIL] 품질 미달 최종 실패")
            update_keyword_status(row_index, "failed", error=f"quality:{quality['score']}")
            return

    for issue in quality.get("issues", []):
        log(f"  - {issue}")

    # 5. 이미지 삽입
    log("[5/7] 이미지 삽입...")
    content_with_images, image_count = insert_images(content, keyword, niche)
    log(f"  삽입된 이미지: {image_count}장")

    # 6. WordPress 발행
    log("[6/7] WordPress 발행...")
    try:
        post_url = publish_to_wordpress(
            title=title,
            content=content_with_images,
            meta_description=meta_desc,
            wp_url=wp_url,
            wp_user=wp_user,
            wp_pass=wp_pass,
            categories=[niche],
        )
        log(f"  발행 완료: {post_url}")
    except Exception as e:
        log(f"[FAIL] WordPress 발행 실패: {e}")
        update_keyword_status(row_index, "failed", error=str(e))
        return

    # 7. 상태 업데이트
    log("[7/7] 상태 업데이트...")
    save_hash(title, content)
    update_keyword_status(
        row_index, "published",
        url=post_url,
        quality_score=quality["score"],
        word_count=len(content),
        ai_model=used_model,
    )
    
    log("=== 발행 완료 ===")
    log(f"  제목: {title}")
    log(f"  URL: {post_url}")
    log(f"  품질: {quality['score']}점 | AI: {used_model} | 이미지: {image_count}장")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[CRITICAL] 예상치 못한 오류: {e}")
        traceback.print_exc()
        sys.exit(1)
