"""
WP Publisher: WordPress REST API 자동 발행
Application Password 인증 방식
"""
import base64
import requests
import re


def publish_to_wordpress(title, content, meta_description, wp_url, wp_user, wp_pass, categories=None):
    """
    WordPress REST API로 글 발행.
    반환: 발행된 글 URL
    """
    # 인증 헤더
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }
    
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    # 카테고리 ID 매핑 (없으면 생성)
    category_ids = []
    if categories:
        for cat_name in categories:
            cat_id = _get_or_create_category(wp_url, headers, cat_name)
            if cat_id:
                category_ids.append(cat_id)
    
    # 슬러그 생성 (영문 키워드 기반)
    slug = re.sub(r'[^a-z0-9\s-]', '', title.lower())
    slug = re.sub(r'[\s]+', '-', slug)[:60].strip('-')
    
    # 발행 데이터
    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "slug": slug if slug else None,
        "categories": category_ids if category_ids else None,
        "meta": {},
    }
    
    # Yoast SEO 메타 (플러그인 설치 시)
    if meta_description:
        data["meta"]["_yoast_wpseo_metadesc"] = meta_description[:155]
    
    # None 값 제거
    data = {k: v for k, v in data.items() if v is not None}
    
    # 발행 요청
    r = requests.post(api_url, headers=headers, json=data, timeout=30)
    r.raise_for_status()
    
    result = r.json()
    post_url = result.get("link", f"{wp_url}/?p={result.get('id', '')}")
    
    return post_url


def _get_or_create_category(wp_url, headers, cat_name):
    """카테고리 ID 조회. 없으면 생성."""
    api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/categories"
    
    try:
        # 기존 카테고리 검색
        r = requests.get(api_url, headers=headers, params={"search": cat_name}, timeout=10)
        r.raise_for_status()
        cats = r.json()
        
        for cat in cats:
            if cat["name"].lower() == cat_name.lower():
                return cat["id"]
        
        # 없으면 생성
        r = requests.post(api_url, headers=headers, json={"name": cat_name}, timeout=10)
        if r.status_code in (200, 201):
            return r.json()["id"]
    except Exception as e:
        print(f"  [Category] {cat_name} 처리 실패: {e}")
    
    return None
