"""
Keyword Generator v1.0: 무한 키워드 자동 생성
3가지 소스를 결합하여 매 실행마다 새로운 키워드를 자동 발굴.

소스 1: Gemini AI — 니치 기반 키워드 생성
소스 2: Google Trends RSS — 실시간 인기 검색어 필터링
소스 3: Reddit/Hacker News — 커뮤니티 트렌드 수집
"""
import os, re, json, random, hashlib, requests
from datetime import datetime

# ===== 니치 설정 =====
NICHE_CONFIGS = {
    "AI도구": {
        "en": "AI Tools",
        "seed_topics": [
            "AI writing tools", "AI image generators", "AI video makers",
            "AI coding assistants", "AI marketing tools", "AI SEO tools",
            "AI chatbots", "AI voice generators", "AI presentation makers",
            "AI email tools", "AI automation", "AI productivity",
            "AI music generators", "AI translation tools", "AI meeting tools",
            "AI design tools", "AI data analysis", "AI customer service",
            "no-code AI builders", "AI content creation",
        ],
        "subreddits": ["artificial", "ChatGPT", "singularity", "MachineLearning"],
        "hn_filter": ["AI", "GPT", "LLM", "Claude", "Gemini", "machine learning", "automation"],
    },
    "스마트홈": {
        "en": "Smart Home",
        "seed_topics": [
            "robot vacuum", "smart doorbell", "smart lock", "home security camera",
            "smart speaker", "smart thermostat", "smart lighting", "air purifier",
        ],
        "subreddits": ["smarthome", "homeautomation"],
        "hn_filter": ["smart home", "IoT", "home automation"],
    },
    "반려동물": {
        "en": "Pet Supplies",
        "seed_topics": [
            "automatic pet feeder", "pet camera", "dog GPS tracker",
            "cat litter robot", "pet water fountain", "dog training tools",
        ],
        "subreddits": ["pets", "dogs", "cats"],
        "hn_filter": ["pet tech", "pet gadget"],
    },
    "생활가전": {
        "en": "Home Appliance",
        "seed_topics": [
            "air fryer", "water purifier", "cordless vacuum", "dehumidifier",
            "electric kettle", "coffee machine", "blender", "rice cooker",
        ],
        "subreddits": ["BuyItForLife", "homeappliances"],
        "hn_filter": [],
    },
}

DEFAULT_NICHE = "AI도구"


def _load_published_titles():
    """이미 발행된 제목 목록 로드 (중복 방지)"""
    titles = set()
    # CSV에서 published 상태 키워드 수집
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "keywords.csv")
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 7 and parts[6].strip() in ("published", "failed"):
                    titles.add(parts[0].strip().lower())
    # 해시 DB에서도 수집
    hash_path = os.path.join(os.path.dirname(__file__), "..", "data", "published_hashes.json")
    if os.path.exists(hash_path):
        try:
            with open(hash_path, "r") as f:
                data = json.load(f)
                for t in data.get("titles", []):
                    titles.add(t.lower())
        except:
            pass
    return titles


# ===== 소스 1: Gemini AI 키워드 생성 =====

def _generate_gemini_keywords(niche_key, language="ko", count=5):
    """Gemini API로 니치 기반 새 키워드 생성"""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("  [KeyGen] GEMINI_API_KEY 없음, 스킵")
        return []

    niche = NICHE_CONFIGS.get(niche_key, NICHE_CONFIGS[DEFAULT_NICHE])
    today = datetime.now().strftime("%Y-%m-%d")
    year = datetime.now().year
    
    # 시드 토픽에서 랜덤 선택
    seed = random.sample(niche["seed_topics"], min(5, len(niche["seed_topics"])))
    seed_str = ", ".join(seed)

    if language == "ko":
        prompt = f"""당신은 SEO 블로그 키워드 전문가입니다.
오늘 날짜: {today}

아래 조건에 맞는 블로그 키워드 {count}개를 생성하세요.

니치: {niche_key} ({niche['en']})
참고 토픽: {seed_str}

조건:
1. 검색량이 높은 롱테일 키워드 (3~6단어)
2. 구매 의도가 있는 키워드 (추천, 비교, 리뷰, 가이드, 방법)
3. {year}년 최신 트렌드 반영
4. 어필리에이트 수익화가 가능한 키워드
5. 서로 중복되지 않는 다양한 주제

출력 형식 (JSON 배열만, 다른 텍스트 없이):
[
  {{"keyword": "키워드", "niche": "세부카테고리", "type": "review|guide|listicle|versus", "lang": "ko"}},
  ...
]"""
    else:
        prompt = f"""You are an SEO blog keyword expert.
Today: {today}

Generate {count} blog keywords for the following niche.

Niche: {niche['en']}
Seed topics: {seed_str}

Requirements:
1. Long-tail keywords (3-6 words) with high search intent
2. Commercial/buying intent (best, review, comparison, guide, how to)
3. Reflect {year} trends
4. Affiliate monetizable keywords
5. Diverse, non-overlapping topics

Output format (JSON array only, no other text):
[
  {{"keyword": "keyword here", "niche": "subcategory", "type": "review|guide|listicle|versus", "lang": "en"}},
  ...
]"""

    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2000}
            },
            timeout=30)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        
        # JSON 추출
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r'```json?\s*\n?', '', text)
            text = re.sub(r'```\s*$', '', text)
        
        keywords = json.loads(text)
        print(f"  [KeyGen:Gemini] {len(keywords)}개 생성")
        return keywords
    except Exception as e:
        print(f"  [KeyGen:Gemini] 실패: {e}")
        return []


# ===== 소스 2: Google Trends RSS =====

def _fetch_google_trends(niche_key, language="ko"):
    """Google Trends 실시간 인기 검색어에서 니치 관련 키워드 필터"""
    try:
        geo = "KR" if language == "ko" else "US"
        url = f"https://trends.google.com/trending/rss?geo={geo}"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        
        if r.status_code != 200:
            print(f"  [KeyGen:Trends] HTTP {r.status_code}")
            return []
        
        # RSS에서 제목 추출
        titles = re.findall(r'<title>(.+?)</title>', r.text)
        titles = [t for t in titles if t != "Daily Search Trends" and len(t) > 3]
        
        niche = NICHE_CONFIGS.get(niche_key, NICHE_CONFIGS[DEFAULT_NICHE])
        filters = niche.get("hn_filter", []) + niche["seed_topics"]
        filter_lower = [f.lower() for f in filters]
        
        # 니치 관련 트렌드만 필터
        relevant = []
        for title in titles:
            title_lower = title.lower()
            for filt in filter_lower:
                if filt.lower() in title_lower:
                    kw_type = "review" if any(w in title_lower for w in ["review", "추천", "비교"]) else "guide"
                    relevant.append({
                        "keyword": title,
                        "niche": niche_key,
                        "type": kw_type,
                        "lang": language,
                        "source": "google_trends"
                    })
                    break
        
        print(f"  [KeyGen:Trends] {len(titles)}개 중 {len(relevant)}개 관련")
        return relevant[:3]
    except Exception as e:
        print(f"  [KeyGen:Trends] 실패: {e}")
        return []


# ===== 소스 3: Reddit + Hacker News =====

def _fetch_reddit_topics(niche_key):
    """Reddit에서 니치 관련 인기 글 제목 수집"""
    niche = NICHE_CONFIGS.get(niche_key, NICHE_CONFIGS[DEFAULT_NICHE])
    subreddits = niche.get("subreddits", [])
    
    if not subreddits:
        return []
    
    keywords = []
    sub = random.choice(subreddits)
    
    try:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=15"
        r = requests.get(url, timeout=15, headers={"User-Agent": "WP-AutoBlog/1.0"})
        
        if r.status_code != 200:
            print(f"  [KeyGen:Reddit] r/{sub} HTTP {r.status_code}")
            return []
        
        posts = r.json().get("data", {}).get("children", [])
        
        for post in posts:
            title = post["data"].get("title", "")
            score = post["data"].get("score", 0)
            
            if score < 50 or len(title) < 15:
                continue
            
            # 제목을 블로그 키워드로 변환
            keywords.append({
                "keyword": title[:80],
                "niche": niche_key,
                "type": "guide",
                "lang": "en",
                "source": "reddit",
                "score": score,
            })
        
        print(f"  [KeyGen:Reddit] r/{sub}에서 {len(keywords)}개 수집")
        return keywords[:3]
    except Exception as e:
        print(f"  [KeyGen:Reddit] 실패: {e}")
        return []


def _fetch_hackernews_topics(niche_key):
    """Hacker News 인기 글에서 AI/테크 관련 키워드 수집"""
    niche = NICHE_CONFIGS.get(niche_key, NICHE_CONFIGS[DEFAULT_NICHE])
    filters = niche.get("hn_filter", [])
    
    if not filters:
        return []
    
    try:
        # HN Top Stories
        r = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty", timeout=10)
        story_ids = r.json()[:30]
        
        keywords = []
        for sid in random.sample(story_ids, min(15, len(story_ids))):
            try:
                sr = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5)
                item = sr.json()
                title = item.get("title", "")
                score = item.get("score", 0)
                
                if score < 30:
                    continue
                
                title_lower = title.lower()
                for filt in filters:
                    if filt.lower() in title_lower:
                        keywords.append({
                            "keyword": title[:80],
                            "niche": niche_key,
                            "type": "review",
                            "lang": "en",
                            "source": "hackernews",
                            "score": score,
                        })
                        break
            except:
                continue
        
        print(f"  [KeyGen:HN] {len(keywords)}개 수집")
        return keywords[:3]
    except Exception as e:
        print(f"  [KeyGen:HN] 실패: {e}")
        return []


# ===== 메인: 3소스 통합 키워드 생성 =====

def auto_generate_keyword(niche_key=None, language=None):
    """
    3가지 소스에서 키워드를 수집하고 최적의 1개를 선택.
    
    우선순위:
    1. Google Trends (실시간 트렌드 = 검색량 높음)
    2. Reddit/HN (커뮤니티 관심 = 참여도 높음)
    3. Gemini AI (무한 생성 = 절대 실패 안 함)
    
    반환: {"keyword": ..., "niche": ..., "prompt_type": ..., "language": ..., "source": ...}
    """
    niche_key = niche_key or os.getenv("AUTO_NICHE", DEFAULT_NICHE)
    language = language or os.getenv("AUTO_LANGUAGE", "ko")
    
    print(f"  [KeyGen] 니치: {niche_key} | 언어: {language}")
    
    published = _load_published_titles()
    all_candidates = []
    
    # 소스 1: Google Trends
    trends = _fetch_google_trends(niche_key, language)
    for t in trends:
        t["priority"] = 1
    all_candidates.extend(trends)
    
    # 소스 2: Reddit + HN
    reddit = _fetch_reddit_topics(niche_key)
    for r in reddit:
        r["priority"] = 2
    all_candidates.extend(reddit)
    
    hn = _fetch_hackernews_topics(niche_key)
    for h in hn:
        h["priority"] = 2
    all_candidates.extend(hn)
    
    # 소스 3: Gemini AI (항상 실행 — 최후 보루)
    gemini = _generate_gemini_keywords(niche_key, language, count=5)
    for g in gemini:
        g["priority"] = 3
        g["source"] = "gemini"
    all_candidates.extend(gemini)
    
    print(f"  [KeyGen] 총 후보: {len(all_candidates)}개")
    
    # 중복 제거 (이미 발행된 것 제외)
    fresh = []
    for c in all_candidates:
        kw = c.get("keyword", "").lower().strip()
        if kw and kw not in published and len(kw) > 5:
            fresh.append(c)
    
    print(f"  [KeyGen] 중복 제거 후: {len(fresh)}개")
    
    if not fresh:
        # 최후의 보루: Gemini에게 완전히 새로운 키워드 요청
        print("  [KeyGen] 모든 소스 소진. Gemini 추가 생성...")
        emergency = _generate_gemini_keywords(niche_key, language, count=10)
        for e in emergency:
            kw = e.get("keyword", "").lower().strip()
            if kw not in published:
                fresh.append(e)
    
    if not fresh:
        print("  [KeyGen] 키워드 생성 실패!")
        return None
    
    # 우선순위 정렬 (1=Trends > 2=Reddit/HN > 3=Gemini)
    fresh.sort(key=lambda x: x.get("priority", 99))
    
    # 첫 번째 = 최적의 키워드
    selected = fresh[0]
    
    result = {
        "keyword": selected["keyword"],
        "niche": selected.get("niche", niche_key),
        "prompt_type": selected.get("type", "review"),
        "language": selected.get("lang", language),
        "source": selected.get("source", "unknown"),
    }
    
    print(f"  [KeyGen] 선택: '{result['keyword']}' (소스: {result['source']})")
    return result
