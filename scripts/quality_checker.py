"""
Quality Checker v2: 개선된 품질 검증
- 이미지 슬롯도 점수에 포함 (삽입 전이므로)
- HTML 구조 검증 강화
- 최소 기준 완화 (70점 통과, 재생성 후 60점도 통과)
"""
import re

def check_quality(title, content, meta_description, keyword):
    score, issues, details = 0, [], {}

    # 1. 글자수 (25점) - 가장 중요
    plain = re.sub(r'<[^>]+>', '', content)
    plain = re.sub(r'\s+', ' ', plain).strip()
    wc = len(plain)
    details["word_count"] = wc
    if wc >= 2000: score += 25
    elif wc >= 1500: score += 20
    elif wc >= 1000: score += 12; issues.append(f"글자수 부족: {wc}자 (1,500자+ 권장)")
    elif wc >= 500: score += 5; issues.append(f"글자수 부족: {wc}자 (1,500자+ 권장)")
    else: issues.append(f"글자수 심각 부족: {wc}자")

    # 2. H2 소제목 (15점)
    h2 = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
    details["h2_count"] = h2
    if h2 >= 5: score += 15
    elif h2 >= 3: score += 10
    elif h2 >= 2: score += 5; issues.append(f"H2 부족: {h2}개 (5개+ 권장)")
    else: issues.append(f"H2 없음: {h2}개")

    # 3. 이미지 슬롯 OR 이미지 태그 (10점)
    img = len(re.findall(r'<img\s', content, re.IGNORECASE))
    slot = len(re.findall(r'\[IMAGE_SLOT_\d\]', content))
    total = img + slot
    details["image_count"] = img; details["slot_count"] = slot
    if total >= 2: score += 10
    elif total >= 1: score += 7
    else: score += 3; issues.append("이미지/슬롯 없음")

    # 4. 메타 디스크립션 (10점)
    ml = len(meta_description) if meta_description else 0
    details["meta_length"] = ml
    if 30 <= ml <= 160: score += 10
    elif ml > 0: score += 5
    else: issues.append("메타디스크립션 없음")

    # 5. 키워드 존재 (10점)
    kl = keyword.lower()
    tl = plain.lower()
    kc = tl.count(kl)
    details["keyword_count"] = kc
    if kc >= 3: score += 10
    elif kc >= 1: score += 7
    else: score += 0; issues.append("키워드 미포함")

    # 6. 제목 품질 (10점)
    details["title_length"] = len(title)
    if title and 10 <= len(title) <= 80: score += 10
    elif title: score += 5
    else: issues.append("제목 없음")

    # 7. HTML 구조 (10점)
    has_p = bool(re.search(r'<p[^>]*>', content, re.IGNORECASE))
    has_list = bool(re.search(r'<[uo]l[^>]*>', content, re.IGNORECASE))
    has_table = bool(re.search(r'<table[^>]*>', content, re.IGNORECASE))
    details["has_paragraphs"] = has_p; details["has_lists"] = has_list; details["has_table"] = has_table
    if has_p: score += 3
    else: issues.append("<p> 태그 없음")
    if has_list: score += 3
    if has_table: score += 4

    # 8. 링크 (5점)
    lc = len(re.findall(r'<a\s+href=', content, re.IGNORECASE))
    details["link_count"] = lc
    if lc >= 1: score += 5
    else: score += 2

    # 9. 콘텐츠 다양성 보너스 (5점)
    has_strong = bool(re.search(r'<strong>', content, re.IGNORECASE))
    has_em = bool(re.search(r'<em>', content, re.IGNORECASE))
    if has_strong: score += 3
    if has_em: score += 2

    return {"score": min(score, 100), "issues": issues, "details": details}
