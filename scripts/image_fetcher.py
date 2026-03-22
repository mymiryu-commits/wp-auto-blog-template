"""
Image Fetcher: Unsplash/Pexels API로 이미지 자동 삽입
[IMAGE_SLOT_N] 마커를 실제 <img> 태그로 교체
"""
import os
import re
import requests


def _search_unsplash(query, per_page=3):
    key = os.getenv("UNSPLASH_KEY")
    if not key:
        return []
    try:
        r = requests.get("https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {key}"},
            timeout=15)
        r.raise_for_status()
        results = []
        for photo in r.json().get("results", []):
            results.append({
                "url": photo["urls"]["regular"],
                "alt": photo.get("alt_description", query),
                "credit": photo["user"]["name"],
                "source": "Unsplash",
            })
        return results
    except Exception as e:
        print(f"  [Unsplash] 검색 실패: {e}")
        return []


def _search_pexels(query, per_page=3):
    key = os.getenv("PEXELS_KEY")
    if not key:
        return []
    try:
        r = requests.get("https://api.pexels.com/v1/search",
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
            headers={"Authorization": key},
            timeout=15)
        r.raise_for_status()
        results = []
        for photo in r.json().get("photos", []):
            results.append({
                "url": photo["src"]["large"],
                "alt": photo.get("alt", query),
                "credit": photo["photographer"],
                "source": "Pexels",
            })
        return results
    except Exception as e:
        print(f"  [Pexels] 검색 실패: {e}")
        return []


def _build_img_html(img, keyword):
    """이미지 HTML 생성 (SEO alt 텍스트 포함)"""
    alt = img["alt"] if img["alt"] else keyword
    # alt 텍스트 정리
    alt = re.sub(r'[<>"\'&]', '', str(alt))[:120]
    return (
        f'<figure style="text-align:center;margin:20px 0;">'
        f'<img src="{img["url"]}" alt="{alt}" '
        f'style="max-width:100%;height:auto;border-radius:8px;" loading="lazy" />'
        f'<figcaption style="font-size:12px;color:#888;margin-top:5px;">'
        f'Photo by {img["credit"]} / {img["source"]}'
        f'</figcaption></figure>'
    )


def insert_images(content, keyword, niche):
    """
    [IMAGE_SLOT_1]~[IMAGE_SLOT_3] 마커를 실제 이미지로 교체.
    Unsplash 우선, 실패 시 Pexels 폴백.
    반환: (수정된 content, 삽입된 이미지 수)
    """
    # 검색 쿼리 구성 (키워드 + 니치 조합)
    search_query = f"{keyword} {niche}".strip()
    
    # 이미지 검색 (Unsplash 우선)
    images = _search_unsplash(search_query)
    if len(images) < 3:
        pexels_images = _search_pexels(search_query, per_page=3 - len(images))
        images.extend(pexels_images)
    
    # 이미지가 부족하면 니치로만 재검색
    if len(images) < 2:
        fallback = _search_unsplash(niche, per_page=3)
        images.extend(fallback)
    
    # [IMAGE_SLOT_N] 교체
    inserted = 0
    for i in range(1, 4):
        marker = f"[IMAGE_SLOT_{i}]"
        if marker in content and i - 1 < len(images):
            img_html = _build_img_html(images[i - 1], keyword)
            content = content.replace(marker, img_html, 1)
            inserted += 1
        elif marker in content:
            # 이미지가 부족하면 마커 제거
            content = content.replace(marker, "")
    
    # 마커가 없는데 이미지가 있으면 H2 뒤에 자동 삽입
    if inserted == 0 and images:
        h2_positions = [m.end() for m in re.finditer(r'</h2>', content)]
        for idx, pos in enumerate(h2_positions[:3]):
            if idx < len(images):
                img_html = _build_img_html(images[idx], keyword)
                content = content[:pos] + "\n" + img_html + "\n" + content[pos:]
                inserted += 1
                # 위치 보정 (삽입으로 인한 오프셋)
                offset = len(img_html) + 2
                h2_positions = [p + offset if p > pos else p for p in h2_positions]
    
    return content, inserted
