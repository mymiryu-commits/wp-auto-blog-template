"""
WP Publisher v2: AdSense 최적화 HTML 스타일링
- 어필리에이트 공개 고지문 자동 삽입
- CTA 박스 스타일링
- 목차(TOC) 자동 생성
- FAQ Schema (JSON-LD) 자동 삽입
- 가독성 향상 CSS 인라인
- AdSense 광고 슬롯 마커
"""
import base64
import requests
import re


# ===== AdSense 최적화 스타일 =====

ADSENSE_STYLE = """
<style>
.wp-auto-content { font-size: 17px; line-height: 1.9; color: #333; max-width: 780px; margin: 0 auto; }
.wp-auto-content h2 { font-size: 24px; font-weight: 700; color: #1a1a2e; margin: 35px 0 15px; padding: 12px 0; border-bottom: 3px solid #4361ee; }
.wp-auto-content h3 { font-size: 20px; font-weight: 600; color: #2d3436; margin: 25px 0 12px; }
.wp-auto-content p { margin: 12px 0; word-break: keep-all; }
.wp-auto-content ul, .wp-auto-content ol { margin: 12px 0; padding-left: 24px; }
.wp-auto-content li { margin: 6px 0; line-height: 1.8; }
.wp-auto-content table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 15px; }
.wp-auto-content th { background: #4361ee; color: #fff; padding: 12px 14px; text-align: left; font-weight: 600; }
.wp-auto-content td { padding: 10px 14px; border-bottom: 1px solid #e9ecef; }
.wp-auto-content tr:nth-child(even) { background: #f8f9fa; }
.wp-auto-content tr:hover { background: #e8f4f8; }
.wp-auto-content img { max-width: 100%; height: auto; border-radius: 10px; margin: 16px 0; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
.wp-auto-content figure { margin: 20px 0; text-align: center; }
.wp-auto-content figcaption { font-size: 12px; color: #999; margin-top: 6px; }
.wp-auto-content strong { color: #1a1a2e; }
.wp-auto-content blockquote { border-left: 4px solid #4361ee; padding: 12px 20px; margin: 20px 0; background: #f0f4ff; border-radius: 0 8px 8px 0; font-style: italic; color: #555; }
.wp-auto-toc { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 12px; padding: 20px 24px; margin: 20px 0; }
.wp-auto-toc h3 { font-size: 16px; margin: 0 0 10px; color: #333; border: none; padding: 0; }
.wp-auto-toc ul { list-style: none; padding: 0; margin: 0; }
.wp-auto-toc li { padding: 4px 0; }
.wp-auto-toc a { color: #4361ee; text-decoration: none; font-size: 15px; }
.wp-auto-toc a:hover { text-decoration: underline; }
.wp-auto-cta { background: linear-gradient(135deg, #f0f4ff, #e8f4f8); border: 2px solid #4361ee; border-radius: 14px; padding: 24px; margin: 24px 0; text-align: center; }
.wp-auto-cta p { font-size: 18px; font-weight: 700; color: #1a1a2e; margin-bottom: 12px; }
.wp-auto-cta a { display: inline-block; background: #4361ee; color: #fff; padding: 14px 36px; border-radius: 10px; text-decoration: none; font-weight: 700; font-size: 16px; transition: background 0.2s; }
.wp-auto-cta a:hover { background: #3a56d4; }
.wp-auto-disclosure { font-size: 12px; color: #999; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 24px; line-height: 1.6; }
.wp-auto-ad-slot { min-height: 90px; margin: 24px 0; text-align: center; clear: both; }
.wp-auto-highlight { background: #fff3cd; padding: 14px 18px; border-radius: 10px; margin: 16px 0; border-left: 4px solid #ffc107; }
.wp-auto-pros-cons { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0; }
.wp-auto-pros { background: #e8f5e9; border-radius: 10px; padding: 16px; }
.wp-auto-cons { background: #ffebee; border-radius: 10px; padding: 16px; }
.wp-auto-pros h4, .wp-auto-cons h4 { margin: 0 0 8px; font-size: 15px; }
@media (max-width: 768px) {
  .wp-auto-content { font-size: 16px; }
  .wp-auto-content h2 { font-size: 21px; }
  .wp-auto-pros-cons { grid-template-columns: 1fr; }
  .wp-auto-content table { font-size: 13px; }
  .wp-auto-content th, .wp-auto-content td { padding: 8px 10px; }
}
</style>
"""

DISCLOSURE_KO = """<div class="wp-auto-disclosure">
이 글에는 제휴 링크가 포함되어 있을 수 있습니다. 링크를 통해 구매하시면 소정의 수수료를 받을 수 있으며, 이는 더 좋은 콘텐츠 제작에 사용됩니다. 구매자에게 추가 비용은 없습니다.
</div>"""

DISCLOSURE_EN = """<div class="wp-auto-disclosure">
This post may contain affiliate links. If you make a purchase through these links, we may earn a small commission at no extra cost to you. This helps us create better content.
</div>"""


def _generate_toc(content, language="ko"):
    """H2 태그에서 목차 자동 생성"""
    h2_matches = re.findall(r'<h2[^>]*>(.*?)</h2>', content, re.IGNORECASE)
    if len(h2_matches) < 3:
        return "", content
    
    toc_title = "목차" if language == "ko" else "Table of Contents"
    toc_items = []
    modified_content = content
    
    for i, h2_text in enumerate(h2_matches):
        clean_text = re.sub(r'<[^>]+>', '', h2_text).strip()
        anchor_id = f"section-{i+1}"
        toc_items.append(f'<li><a href="#{anchor_id}">{clean_text}</a></li>')
        # H2에 id 추가
        old_h2 = f'<h2>{h2_text}</h2>'
        new_h2 = f'<h2 id="{anchor_id}">{h2_text}</h2>'
        modified_content = modified_content.replace(old_h2, new_h2, 1)
        # 속성이 있는 H2도 처리
        pattern = f'<h2([^>]*)>{re.escape(h2_text)}</h2>'
        replacement = f'<h2\\1 id="{anchor_id}">{h2_text}</h2>'
        modified_content = re.sub(pattern, replacement, modified_content, count=1)
    
    toc_html = f"""<div class="wp-auto-toc">
<h3>{toc_title}</h3>
<ul>{''.join(toc_items)}</ul>
</div>"""
    
    return toc_html, modified_content


def _generate_faq_schema(content):
    """FAQ 섹션이 있으면 JSON-LD Schema 자동 생성"""
    # Q&A 패턴 찾기
    qa_patterns = [
        re.findall(r'<strong>(Q[.:]?\s*.+?)</strong>\s*(?:</p>)?\s*(?:<p>)?\s*(.+?)</p>', content, re.DOTALL),
        re.findall(r'<h3>(.*?\?)</h3>\s*<p>(.*?)</p>', content, re.DOTALL),
    ]
    
    qa_pairs = []
    for matches in qa_patterns:
        for q, a in matches:
            q_clean = re.sub(r'<[^>]+>', '', q).strip()
            a_clean = re.sub(r'<[^>]+>', '', a).strip()
            if len(q_clean) > 5 and len(a_clean) > 10:
                qa_pairs.append({"q": q_clean, "a": a_clean})
    
    if not qa_pairs:
        return ""
    
    entities = []
    for qa in qa_pairs[:5]:  # 최대 5개
        entities.append(f'{{"@type":"Question","name":"{qa["q"]}","acceptedAnswer":{{"@type":"Answer","text":"{qa["a"][:300]}"}}}}')
    
    schema = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{",".join(entities)}]}}
</script>"""
    
    return schema


def _style_cta_boxes(content):
    """CTA 관련 텍스트를 스타일 박스로 감싸기"""
    # 링크가 있는 CTA 패턴
    cta_patterns = [
        r'(<a[^>]*href=["\'][^"\']*(?:coupang|amazon|affiliate|partner)[^"\']*["\'][^>]*>.*?</a>)',
        r'(<p[^>]*>.*?(?:지금 확인|최저가|가격 확인|구매하기|Check Price|Buy Now|Get Deal).*?</p>)',
    ]
    
    for pattern in cta_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            if 'wp-auto-cta' not in match:
                styled = f'<div class="wp-auto-cta">{match}</div>'
                content = content.replace(match, styled, 1)
    
    return content


def _add_ad_slots(content):
    """AdSense 광고 슬롯 마커 삽입 (H2 태그 사이에)"""
    ad_marker = '<div class="wp-auto-ad-slot"><!-- AdSense Auto --></div>'
    
    h2_positions = [m.start() for m in re.finditer(r'<h2[^>]*>', content, re.IGNORECASE)]
    
    if len(h2_positions) >= 4:
        # 3번째 H2 앞에 광고 삽입
        pos = h2_positions[2]
        content = content[:pos] + ad_marker + '\n' + content[pos:]
    
    return content


def _optimize_content(content, language="ko"):
    """AdSense 최적화 + 가독성 향상"""
    # 1. 스타일 + 컨테이너
    disclosure = DISCLOSURE_KO if language == "ko" else DISCLOSURE_EN
    
    # 2. 목차 생성
    toc, content = _generate_toc(content, language)
    
    # 3. CTA 스타일링
    content = _style_cta_boxes(content)
    
    # 4. 광고 슬롯
    content = _add_ad_slots(content)
    
    # 5. FAQ Schema
    faq_schema = _generate_faq_schema(content)
    
    # 6. 최종 조합
    final = f"""{ADSENSE_STYLE}
{disclosure}
{toc}
<div class="wp-auto-content">
{content}
</div>
{faq_schema}"""
    
    return final


def publish_to_wordpress(title, content, meta_description, wp_url, wp_user, wp_pass, categories=None, language="ko"):
    """WordPress REST API 발행 (AdSense 최적화 포함)"""
    
    # AdSense 최적화 적용
    optimized_content = _optimize_content(content, language)
    
    # 인증
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }
    
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    # 카테고리
    category_ids = []
    if categories:
        for cat_name in categories:
            cat_id = _get_or_create_category(wp_url, headers, cat_name)
            if cat_id:
                category_ids.append(cat_id)
    
    # 슬러그
    slug = re.sub(r'[^a-z0-9\s-]', '', title.lower())
    slug = re.sub(r'[\s]+', '-', slug)[:60].strip('-')
    
    # 발행 데이터
    data = {
        "title": title,
        "content": optimized_content,
        "status": "publish",
        "slug": slug if slug else None,
        "categories": category_ids if category_ids else None,
        "meta": {},
    }
    
    if meta_description:
        data["meta"]["_yoast_wpseo_metadesc"] = meta_description[:155]
    
    data = {k: v for k, v in data.items() if v is not None}
    
    r = requests.post(api_url, headers=headers, json=data, timeout=30)
    r.raise_for_status()
    
    result = r.json()
    return result.get("link", f"{wp_url}/?p={result.get('id', '')}")


def _get_or_create_category(wp_url, headers, cat_name):
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/categories"
    try:
        r = requests.get(api_url, headers=headers, params={"search": cat_name}, timeout=10)
        r.raise_for_status()
        for cat in r.json():
            if cat["name"].lower() == cat_name.lower():
                return cat["id"]
        r = requests.post(api_url, headers=headers, json={"name": cat_name}, timeout=10)
        if r.status_code in (200, 201):
            return r.json()["id"]
    except Exception as e:
        print(f"  [Category] {cat_name}: {e}")
    return None
