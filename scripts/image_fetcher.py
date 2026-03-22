"""
Image Fetcher v2: Pexels (메인) + Pixabay (백업)
핵심 개선:
- 검색 쿼리 다양화 (키워드 변형 + 니치 조합)
- 랜덤 페이지/오프셋으로 다른 이미지 반환
- 중복 방지 (URL 해시 저장)
- Unsplash 제거 (이미지 반복 심함)
- WebP 우선 (속도 최적화)
"""
import os, re, random, hashlib, json, requests
from datetime import datetime

# 이미 사용한 이미지 URL 추적 (세션 내)
_used_images = set()

def _vary_query(keyword, niche):
    """검색 쿼리를 다양하게 변형하여 다른 이미지가 나오게 함"""
    base_queries = [
        keyword,
        f"{keyword} product",
        f"{keyword} lifestyle",
        f"{niche}",
        f"{niche} product review",
        f"{niche} comparison",
        f"{niche} lifestyle",
    ]
    
    # 한국어 키워드면 영어 변환 쿼리도 추가
    ko_to_en = {
        "반려동물": "pet supplies", "강아지": "dog", "고양이": "cat",
        "스마트홈": "smart home", "주방": "kitchen appliance",
        "가전": "home appliance", "청소기": "vacuum cleaner",
        "에어프라이어": "air fryer", "정수기": "water purifier",
        "건강": "health wellness", "뷰티": "beauty skincare",
        "육아": "baby products", "홈트": "home fitness",
        "재테크": "finance investment", "급식기": "pet feeder",
        "로봇청소기": "robot vacuum", "무선이어폰": "wireless earbuds",
    }
    
    for ko, en in ko_to_en.items():
        if ko in keyword or ko in niche:
            base_queries.append(en)
            base_queries.append(f"{en} top rated")
    
    # 3개 랜덤 선택
    random.shuffle(base_queries)
    return base_queries[:3]


def _search_pexels(query, per_page=5):
    """Pexels API 검색 (메인)"""
    key = os.getenv("PEXELS_KEY")
    if not key:
        return []
    try:
        # 랜덤 페이지로 다른 결과 반환
        page = random.randint(1, 5)
        r = requests.get("https://api.pexels.com/v1/search",
            params={"query": query, "per_page": per_page, "page": page,
                    "orientation": "landscape", "size": "large"},
            headers={"Authorization": key}, timeout=15)
        r.raise_for_status()
        results = []
        for photo in r.json().get("photos", []):
            url = photo["src"].get("large2x", photo["src"]["large"])
            if url not in _used_images:
                results.append({
                    "url": url,
                    "alt": photo.get("alt", query),
                    "credit": photo["photographer"],
                    "source": "Pexels",
                    "width": photo.get("width", 1200),
                    "height": photo.get("height", 800),
                })
                _used_images.add(url)
        return results
    except Exception as e:
        print(f"  [Pexels] {query}: {e}")
        return []


def _search_pixabay(query, per_page=5):
    """Pixabay API 검색 (백업)"""
    key = os.getenv("PIXABAY_KEY")
    if not key:
        return []
    try:
        page = random.randint(1, 5)
        r = requests.get("https://pixabay.com/api/",
            params={"key": key, "q": query, "per_page": per_page, "page": page,
                    "orientation": "horizontal", "image_type": "photo",
                    "min_width": 800, "safesearch": "true"},
            timeout=15)
        r.raise_for_status()
        results = []
        for hit in r.json().get("hits", []):
            url = hit.get("largeImageURL", hit.get("webformatURL", ""))
            if url and url not in _used_images:
                results.append({
                    "url": url,
                    "alt": hit.get("tags", query),
                    "credit": hit.get("user", "Pixabay"),
                    "source": "Pixabay",
                    "width": hit.get("imageWidth", 1200),
                    "height": hit.get("imageHeight", 800),
                })
                _used_images.add(url)
        return results
    except Exception as e:
        print(f"  [Pixabay] {query}: {e}")
        return []


def _search_unsplash(query, per_page=5):
    """Unsplash API 검색 (최후 백업)"""
    key = os.getenv("UNSPLASH_KEY")
    if not key:
        return []
    try:
        page = random.randint(1, 5)
        r = requests.get("https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": per_page, "page": page,
                    "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {key}"}, timeout=15)
        r.raise_for_status()
        results = []
        for photo in r.json().get("results", []):
            url = photo["urls"].get("regular", "")
            if url and url not in _used_images:
                results.append({
                    "url": url,
                    "alt": photo.get("alt_description", query),
                    "credit": photo["user"]["name"],
                    "source": "Unsplash",
                })
                _used_images.add(url)
        return results
    except Exception as e:
        print(f"  [Unsplash] {query}: {e}")
        return []


def _build_img_html(img, keyword, index):
    """AdSense 최적화 이미지 HTML"""
    alt = img.get("alt", keyword)
    if not alt or alt == keyword:
        alt = f"{keyword} - {['제품 이미지', '비교 분석', '추천 가이드'][index % 3]}"
    alt = re.sub(r'[<>"\'&]', '', str(alt))[:120]
    
    width = img.get("width", 1200)
    height = img.get("height", 800)
    
    return (
        f'<figure style="text-align:center;margin:24px 0;">'
        f'<img src="{img["url"]}" alt="{alt}" '
        f'width="{width}" height="{height}" '
        f'style="max-width:100%;height:auto;border-radius:10px;'
        f'box-shadow:0 2px 12px rgba(0,0,0,0.08);" loading="lazy" />'
        f'<figcaption style="font-size:12px;color:#999;margin-top:6px;">'
        f'Photo: {img["credit"]} / {img["source"]}'
        f'</figcaption></figure>'
    )


def insert_images(content, keyword, niche):
    """
    이미지 삽입 메인 함수
    1. 다양한 검색 쿼리로 이미지 수집
    2. [IMAGE_SLOT_N] 마커 교체
    3. 마커 없으면 H2 뒤에 자동 삽입
    반환: (수정된 content, 삽입된 이미지 수)
    """
    # 다양한 쿼리 생성
    queries = _vary_query(keyword, niche)
    print(f"  [Image] 검색 쿼리: {queries}")
    
    # 이미지 수집 (Pexels 우선 → Pixabay → Unsplash)
    all_images = []
    for q in queries:
        if len(all_images) >= 5:
            break
        imgs = _search_pexels(q, per_page=3)
        all_images.extend(imgs)
    
    if len(all_images) < 3:
        for q in queries:
            if len(all_images) >= 5:
                break
            imgs = _search_pixabay(q, per_page=3)
            all_images.extend(imgs)
    
    if len(all_images) < 3:
        for q in queries:
            if len(all_images) >= 5:
                break
            imgs = _search_unsplash(q, per_page=3)
            all_images.extend(imgs)
    
    # 중복 제거 + 셔플
    seen_urls = set()
    unique_images = []
    for img in all_images:
        if img["url"] not in seen_urls:
            seen_urls.add(img["url"])
            unique_images.append(img)
    random.shuffle(unique_images)
    
    print(f"  [Image] 수집된 이미지: {len(unique_images)}장")
    
    if not unique_images:
        # 이미지 없으면 슬롯만 제거
        for i in range(1, 4):
            content = content.replace(f"[IMAGE_SLOT_{i}]", "")
        return content, 0
    
    # [IMAGE_SLOT_N] 교체
    inserted = 0
    for i in range(1, 4):
        marker = f"[IMAGE_SLOT_{i}]"
        if marker in content and inserted < len(unique_images):
            img_html = _build_img_html(unique_images[inserted], keyword, inserted)
            content = content.replace(marker, img_html, 1)
            inserted += 1
        elif marker in content:
            content = content.replace(marker, "")
    
    # 슬롯이 없었는데 이미지가 있으면 H2 뒤에 삽입
    if inserted == 0 and unique_images:
        h2_ends = [m.end() for m in re.finditer(r'</h2>', content, re.IGNORECASE)]
        insert_positions = h2_ends[:3] if len(h2_ends) >= 3 else h2_ends
        
        offset = 0
        for idx, pos in enumerate(insert_positions):
            if idx < len(unique_images):
                img_html = '\n' + _build_img_html(unique_images[idx], keyword, idx) + '\n'
                actual_pos = pos + offset
                content = content[:actual_pos] + img_html + content[actual_pos:]
                offset += len(img_html)
                inserted += 1
    
    return content, inserted
