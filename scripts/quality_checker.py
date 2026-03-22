"""
Quality Checker: AdSense 승인 기준 자동 채점 (100점 만점)
80점 이상: 발행 / 미만: 재생성
"""
import re


def check_quality(title, content, meta_description, keyword):
    """
    글 품질 검증. 100점 만점.
    반환: {"score": int, "issues": [str], "details": {}}
    """
    score = 0
    issues = []
    details = {}

    # 1. 글자수 (20점)
    # HTML 태그 제거 후 순수 텍스트 길이
    plain_text = re.sub(r'<[^>]+>', '', content)
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    word_count = len(plain_text)
    details["word_count"] = word_count
    
    if word_count >= 2000:
        score += 20
    elif word_count >= 1500:
        score += 15
    elif word_count >= 1000:
        score += 8
        issues.append(f"글자수 부족: {word_count}자 (권장 1,500자+)")
    else:
        score += 0
        issues.append(f"글자수 심각 부족: {word_count}자 (최소 1,500자)")

    # 2. H2 소제목 수 (15점)
    h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
    details["h2_count"] = h2_count
    
    if h2_count >= 4:
        score += 15
    elif h2_count >= 3:
        score += 10
    elif h2_count >= 2:
        score += 5
        issues.append(f"H2 소제목 부족: {h2_count}개 (권장 4개+)")
    else:
        issues.append(f"H2 소제목 심각 부족: {h2_count}개 (최소 3개)")

    # 3. 이미지 슬롯/이미지 태그 (15점)
    img_count = len(re.findall(r'<img\s', content, re.IGNORECASE))
    slot_count = len(re.findall(r'\[IMAGE_SLOT_\d\]', content))
    total_images = img_count + slot_count  # 슬롯은 나중에 교체됨
    details["image_count"] = img_count
    details["slot_count"] = slot_count
    
    if img_count >= 2:
        score += 15
    elif img_count >= 1 or slot_count >= 2:
        score += 10
    elif slot_count >= 1:
        score += 5
        issues.append("이미지 부족: 슬롯만 있음 (실제 이미지 삽입 필요)")
    else:
        issues.append("이미지 없음 (AdSense 승인에 필수)")

    # 4. 메타 디스크립션 (10점)
    details["meta_length"] = len(meta_description) if meta_description else 0
    
    if meta_description and 50 <= len(meta_description) <= 155:
        score += 10
    elif meta_description and len(meta_description) > 0:
        score += 5
        issues.append(f"메타디스크립션 길이 조정 필요: {len(meta_description)}자")
    else:
        issues.append("메타디스크립션 없음")

    # 5. 키워드 밀도 (10점)
    keyword_lower = keyword.lower()
    text_lower = plain_text.lower()
    kw_count = text_lower.count(keyword_lower)
    kw_density = (kw_count * len(keyword_lower) / max(len(text_lower), 1)) * 100
    details["keyword_density"] = round(kw_density, 2)
    details["keyword_count"] = kw_count
    
    if 0.5 <= kw_density <= 3.0:
        score += 10
    elif kw_density > 0:
        score += 5
        if kw_density > 3.0:
            issues.append(f"키워드 과다: {kw_density:.1f}% (3% 이하 권장)")
        else:
            issues.append(f"키워드 부족: {kw_density:.1f}% (0.5% 이상 권장)")
    else:
        issues.append("키워드가 본문에 없음")

    # 6. 내부 링크 가능성 (10점) - <a> 태그 존재 여부
    link_count = len(re.findall(r'<a\s+href=', content, re.IGNORECASE))
    details["link_count"] = link_count
    
    if link_count >= 2:
        score += 10
    elif link_count >= 1:
        score += 7
    else:
        score += 3  # 내부 링크는 발행 후 추가 가능
        issues.append("링크 없음 (발행 후 내부 링크 추가 권장)")

    # 7. 제목 품질 (10점)
    details["title_length"] = len(title)
    
    if title and 10 <= len(title) <= 60:
        score += 10
    elif title and len(title) > 0:
        score += 5
        if len(title) > 60:
            issues.append(f"제목 너무 김: {len(title)}자 (60자 이하 권장)")
    else:
        issues.append("제목 없음")

    # 8. HTML 구조 정상 (5점)
    has_p = bool(re.search(r'<p[^>]*>', content, re.IGNORECASE))
    has_list = bool(re.search(r'<[uo]l[^>]*>', content, re.IGNORECASE))
    details["has_paragraphs"] = has_p
    details["has_lists"] = has_list
    
    if has_p:
        score += 3
    else:
        issues.append("<p> 태그 없음")
    if has_list:
        score += 2

    # 9. 테이블 또는 비교표 (5점 보너스)
    has_table = bool(re.search(r'<table[^>]*>', content, re.IGNORECASE))
    if has_table:
        score += 5
    details["has_table"] = has_table

    return {
        "score": min(score, 100),
        "issues": issues,
        "details": details,
    }
