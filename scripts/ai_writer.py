"""
AI Writer: 멀티 AI 로테이션 + 5-Layer Unique Content Algorithm
Grok → Gemini → Claude → GPT 순서로 폴백.
tenant_id + keyword 조합으로 유니크 프롬프트 생성.
"""
import os
import json
import hashlib
import random
import requests
import re

# ===== 5-Layer Uniqueness Engine =====

PERSONAS = [
    {"id": "expert", "ko": "해당 분야 전문가로서 과학적 근거와 데이터를 중시하는 관점으로", "en": "As a field expert who values scientific evidence and data"},
    {"id": "budget", "ko": "가성비를 최우선으로 따지는 실속파 소비자 관점으로", "en": "As a budget-conscious consumer who prioritizes value for money"},
    {"id": "premium", "ko": "품질과 브랜드를 중시하는 프리미엄 소비자 관점으로", "en": "As a premium consumer who values quality and brand reputation"},
    {"id": "beginner", "ko": "처음 구매하는 초보자를 위해 쉽고 친절하게 설명하는 가이드로", "en": "As a beginner-friendly guide explaining things simply and kindly"},
    {"id": "data", "ko": "숫자와 통계, 성분 분석을 꼼꼼히 파헤치는 데이터 분석가로", "en": "As a data analyst who meticulously examines numbers and statistics"},
    {"id": "story", "ko": "실제 사용 경험을 바탕으로 생생한 후기를 전달하는 스토리텔러로", "en": "As a storyteller sharing vivid real-world usage experiences"},
    {"id": "compare", "ko": "여러 제품을 체계적으로 비교 분석하는 비교 전문가로", "en": "As a comparison expert who systematically analyzes multiple products"},
    {"id": "problem", "ko": "흔한 실수와 함정을 미리 알려주는 문제 해결 전문가로", "en": "As a problem-solver who warns about common mistakes and pitfalls"},
    {"id": "trend", "ko": "최신 트렌드와 시장 동향을 분석하는 트렌드 분석가로", "en": "As a trend analyst who examines the latest market developments"},
    {"id": "organic", "ko": "친환경과 자연주의를 추구하는 내추럴리스트 관점으로", "en": "As a naturalist who pursues eco-friendly and organic options"},
]

ANGLES = {
    "review": ["상세 비교 리뷰", "실사용 30일 후기", "블라인드 테스트 결과"],
    "guide": ["초보자 완전 가이드", "전문가 선택 기준", "실수 방지 체크리스트"],
    "listicle": ["TOP 5 추천", "가격대별 추천", "상황별 추천"],
    "versus": ["A vs B 직접 비교", "저가 vs 고가 비교", "국내 vs 해외 비교"],
}

STRUCTURES_KO = [
    "결론을 먼저 제시하고, 상세 분석, 비교표, FAQ, 구매 가이드 순서로 작성",
    "문제를 제기하고, 해결책을 소개하며, 제품별 상세 분석 후 최종 추천",
    "개인 경험 스토리로 시작하여, 발견한 핵심 포인트, 분석, 추천 순으로 전개",
    "체크리스트를 먼저 보여주고, 각 항목을 상세 설명한 뒤 최종 추천",
    "질문 형태로 도입하여, 답변과 근거를 제시하고, 대안과 최종 추천으로 마무리",
]

STRUCTURES_EN = [
    "Start with the verdict, then detailed analysis, comparison table, FAQ, and buying guide",
    "Present the problem, introduce solutions, analyze each product, then give final recommendation",
    "Begin with a personal story, share key discoveries, analyze findings, then recommend",
    "Show a checklist first, explain each criterion in detail, then give top picks",
    "Open with a question, provide answers with evidence, compare alternatives, then conclude",
]

DETAILS_KO = [
    "가격 변동 히스토리와 할인 시기를 언급해줘",
    "실제 사용자 리뷰에서 자주 나오는 불만 사항을 솔직하게 포함해줘",
    "경쟁 제품 대비 잘 알려지지 않은 숨겨진 장점을 강조해줘",
    "계절별 또는 상황별로 다른 사용 팁을 추가해줘",
    "초보자가 가장 많이 하는 질문 3개를 FAQ 형태로 넣어줘",
    "전문가의 조언 형식으로 신뢰감을 높이는 내용을 넣어줘",
    "구체적인 숫자와 통계 데이터를 활용해서 설득력을 높여줘",
    "실패 사례나 후회하는 구매 경험을 먼저 보여준 뒤 올바른 선택법으로 연결해줘",
]

DETAILS_EN = [
    "Mention price history and best times to buy",
    "Honestly include common complaints from real user reviews",
    "Highlight hidden advantages over competitors that most people miss",
    "Add seasonal or situational usage tips",
    "Include a FAQ section with the 3 most common beginner questions",
    "Add expert advice sections to build trust and credibility",
    "Use specific numbers and statistics to strengthen arguments",
    "Show a failed purchase story first, then connect to the right choice",
]


def _seed_random(tenant_id, keyword):
    """tenant_id + keyword 조합으로 재현 가능한 랜덤 시드 생성"""
    seed_str = f"{tenant_id}:{keyword}:{datetime.now().strftime('%Y%m%d')}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    random.seed(seed)


from datetime import datetime

def build_unique_prompt(keyword, niche, prompt_type, language, affiliate_link, tenant_id):
    """5-Layer Uniqueness Engine으로 유니크 프롬프트 생성"""
    _seed_random(tenant_id, keyword)
    
    # Layer 1: Persona
    persona_idx = int(hashlib.md5(tenant_id.encode()).hexdigest()[:4], 16) % len(PERSONAS)
    persona = PERSONAS[persona_idx]
    persona_text = persona["ko"] if language == "ko" else persona["en"]
    
    # Layer 2: Angle
    angles = ANGLES.get(prompt_type, ANGLES["review"])
    angle = random.choice(angles)
    
    # Layer 3: Structure
    structures = STRUCTURES_KO if language == "ko" else STRUCTURES_EN
    structure = random.choice(structures)
    
    # Layer 4: Details
    details = DETAILS_KO if language == "ko" else DETAILS_EN
    selected_details = random.sample(details, k=min(3, len(details)))
    
    # Layer 5: Temperature
    temperature = round(random.uniform(0.6, 0.9), 2)
    
    if language == "ko":
        system = f"{persona_text} 작성합니다. SEO에 최적화된 {angle} 형식의 블로그 글을 작성하세요."
        user = f"""키워드: {keyword}
카테고리: {niche}

작성 규칙:
1. HTML 형식 출력 (<h2>, <p>, <ul>, <li>, <table> 태그 사용. <h1>은 사용 금지)
2. H2 소제목 4~6개 (키워드를 자연스럽게 포함)
3. 총 1,800~2,500자
4. 글 구조: {structure}
5. {selected_details[0]}
6. {selected_details[1]}
7. {selected_details[2]}
8. 이미지가 들어갈 위치를 [IMAGE_SLOT_1], [IMAGE_SLOT_2], [IMAGE_SLOT_3]으로 표시
9. 글 끝에 자연스러운 구매 유도 CTA 포함{f' (링크: {affiliate_link})' if affiliate_link else ''}
10. 반드시 글 맨 앞에 ---TITLE: 제목--- 형식으로 제목 출력
11. 반드시 글 맨 뒤에 ---META: 메타디스크립션--- 형식으로 150자 이내 메타디스크립션 출력"""
    else:
        system = f"{persona_text}. Write an SEO-optimized blog post in {angle} format."
        user = f"""Keyword: {keyword}
Category: {niche}

Rules:
1. Output HTML (<h2>, <p>, <ul>, <li>, <table> tags. Do NOT use <h1>)
2. 4-6 H2 subheadings with natural keyword inclusion
3. Total 1,800-2,500 words
4. Structure: {structure}
5. {selected_details[0]}
6. {selected_details[1]}
7. {selected_details[2]}
8. Mark image positions: [IMAGE_SLOT_1], [IMAGE_SLOT_2], [IMAGE_SLOT_3]
9. Include a natural CTA at the end{f' (link: {affiliate_link})' if affiliate_link else ''}
10. Start with ---TITLE: your title--- format
11. End with ---META: meta description under 155 chars--- format"""

    return system, user, temperature


# ===== AI API Callers =====

def _call_grok(system, user, temperature):
    key = os.getenv("GROK_API_KEY")
    if not key:
        raise ValueError("GROK_API_KEY not set")
    r = requests.post("https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "grok-4-1-fast", "temperature": temperature, "max_tokens": 4000,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], "grok-4-1-fast"


def _call_gemini(system, user, temperature):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
              "generationConfig": {"temperature": temperature, "maxOutputTokens": 4000}},
        timeout=120)
    r.raise_for_status()
    data = r.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return text, "gemini-2.5-flash"


def _call_claude(system, user, temperature):
    key = os.getenv("CLAUDE_API_KEY")
    if not key:
        raise ValueError("CLAUDE_API_KEY not set")
    r = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 4000, "temperature": temperature,
              "messages": [{"role": "user", "content": f"{system}\n\n{user}"}]},
        timeout=120)
    r.raise_for_status()
    return r.json()["content"][0]["text"], "claude-haiku-4-5"


def _call_openai(system, user, temperature):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not set")
    r = requests.post("https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o-mini", "temperature": temperature, "max_tokens": 4000,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], "gpt-4o-mini"


AI_CALLERS = {
    "grok": _call_grok,
    "gemini": _call_gemini,
    "claude": _call_claude,
    "openai": _call_openai,
}

# 우선순위 (환경변수로 오버라이드 가능)
DEFAULT_PRIORITY = ["grok", "gemini", "claude", "openai"]


def _parse_response(raw_text):
    """AI 응답에서 제목, 본문, 메타디스크립션 추출"""
    title = ""
    meta = ""
    content = raw_text
    
    # 제목 추출
    title_match = re.search(r'---TITLE:\s*(.+?)\s*---', raw_text)
    if title_match:
        title = title_match.group(1).strip()
        content = content.replace(title_match.group(0), "")
    
    # 메타 추출
    meta_match = re.search(r'---META:\s*(.+?)\s*---', raw_text, re.DOTALL)
    if meta_match:
        meta = meta_match.group(1).strip()[:155]
        content = content.replace(meta_match.group(0), "")
    
    # 제목 폴백: 첫 번째 <h2> 사용
    if not title:
        h2_match = re.search(r'<h2[^>]*>(.+?)</h2>', content)
        if h2_match:
            title = re.sub(r'<[^>]+>', '', h2_match.group(1)).strip()
    
    # 메타 폴백: 첫 150자
    if not meta:
        plain = re.sub(r'<[^>]+>', '', content)
        meta = plain[:150].strip()
    
    content = content.strip()
    return title, content, meta


def generate_post(keyword, niche, prompt_type, language, affiliate_link, tenant_id, preferred_model="auto"):
    """
    메인 글 생성 함수.
    preferred_model: 'auto' = 우선순위 순 폴백, 'grok'/'gemini' 등 = 해당 모델 우선
    """
    system, user, temperature = build_unique_prompt(
        keyword, niche, prompt_type, language, affiliate_link, tenant_id
    )
    
    # 우선순위 결정
    priority = list(DEFAULT_PRIORITY)
    custom = os.getenv("AI_PRIORITY")
    if custom:
        priority = [x.strip() for x in custom.split(",") if x.strip()]
    
    if preferred_model != "auto" and preferred_model in AI_CALLERS:
        priority.remove(preferred_model) if preferred_model in priority else None
        priority.insert(0, preferred_model)
    
    # 순서대로 시도
    last_error = None
    for model_key in priority:
        caller = AI_CALLERS.get(model_key)
        if not caller:
            continue
        try:
            raw_text, model_name = caller(system, user, temperature)
            title, content, meta = _parse_response(raw_text)
            return {
                "title": title,
                "content": content,
                "meta_description": meta,
                "model_used": model_name,
                "temperature": temperature,
            }
        except Exception as e:
            last_error = e
            print(f"  [AI FALLBACK] {model_key} 실패: {e}")
            continue
    
    raise RuntimeError(f"모든 AI 모델 실패. 마지막 에러: {last_error}")
