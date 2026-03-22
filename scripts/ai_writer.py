"""
AI Writer v2.0: 핵심 개선
- tenant별 완전히 다른 제목 생성 (15가지 포맷)
- Gemini systemInstruction 분리 + 모델 변경 (2.0-flash)
- 마크다운→HTML 자동 변환
- 프롬프트 품질 대폭 강화 (비교표/리스트 강제)
- max_tokens 8000으로 증가
"""
import os, json, hashlib, random, requests, re
from datetime import datetime

PERSONAS_KO = [
    "당신은 해당 분야 10년 경력 전문가입니다. 과학적 근거와 실험 데이터 기반으로 신뢰도 높은 분석을 제공합니다.",
    "당신은 가성비 최우선 실속파 블로거입니다. 가격 대비 성능을 꼼꼼하게 비교합니다.",
    "당신은 프리미엄 제품 전문 리뷰어입니다. 품질과 브랜드 가치를 중시합니다.",
    "당신은 초보자 눈높이에 맞춘 친절한 가이드 작성자입니다.",
    "당신은 숫자와 통계를 사랑하는 데이터 분석가입니다. 구체적 수치로 설득합니다.",
    "당신은 실제 사용 경험을 생생하게 전달하는 체험 리뷰어입니다.",
    "당신은 여러 제품을 체계적으로 비교하는 비교 분석 전문가입니다.",
    "당신은 구매 실수를 방지해주는 소비자 보호 전문가입니다.",
    "당신은 최신 트렌드를 분석하는 시장 전문가입니다.",
    "당신은 친환경과 건강을 중시하는 내추럴리스트입니다.",
]
PERSONAS_EN = [
    "You are a 10-year industry expert providing analysis backed by scientific evidence.",
    "You are a budget-conscious reviewer comparing price-to-performance ratios.",
    "You are a premium product specialist valuing quality and brand reputation.",
    "You are a beginner-friendly guide explaining complex terms simply.",
    "You are a data analyst using specific statistics and comparison charts.",
    "You are an experience-based reviewer sharing vivid personal usage stories.",
    "You are a systematic comparison expert using tables for objective analysis.",
    "You are a consumer protection expert warning about common purchase mistakes.",
    "You are a market trend analyst covering industry developments.",
    "You are a naturalist focused on ingredient safety and environmental impact.",
]
TITLE_FMT_KO = [
    "{keyword} 완벽 가이드 ({year}년 최신)", "{keyword} 추천 TOP {n}선 | 전문가 비교",
    "{keyword} 어떤 것을 골라야 할까? {year} 비교", "{year} {keyword} 선택법 | 실패 없는 가이드",
    "솔직 비교! {keyword} 장단점 총정리 ({year})", "{keyword} 구매 전 반드시 알아야 할 {n}가지",
    "{keyword} 실사용 후기 | 돈 낭비 방지 가이드", "{year} {keyword} 가성비 순위 | 전문가 추천",
    "{keyword} 고르는 법 | 초보자도 쉽게 따라하기", "{keyword} 비교 리뷰 | 가격~성능 완벽 정리",
    "전문가 추천 {keyword} BEST {n} ({year})", "{keyword} 핵심 체크리스트 | 후회 없는 구매",
    "2달 사용해본 {keyword} 솔직 리뷰", "{keyword} 인기 {n}종 비교 | 최저가 포함",
    "{keyword} 선택 가이드 | 후회 없는 구매를 위해",
]
TITLE_FMT_EN = [
    "Best {keyword} in {year}: Complete Guide", "Top {n} {keyword} Compared | Expert Analysis",
    "{keyword}: Which Should You Choose? ({year})", "Ultimate {keyword} Guide {year} | Save Money",
    "Honest {keyword} Review: Pros, Cons & Picks", "{n} Things to Know Before Buying {keyword}",
    "{keyword} Comparison: Price & Value ({year})", "Best Budget {keyword} {year} | Expert Picks",
    "How to Choose {keyword} | Beginner's Guide", "{keyword} Showdown: Top {n} Options Tested",
    "{year} {keyword} Rankings: Budget to Premium", "{keyword} Buying Checklist Every Shopper Needs",
    "After 2 Months: {keyword} Long-Term Review", "{keyword} Face-Off: {n} Popular Picks",
    "Stop Wasting Money on {keyword} | Read This",
]
STRUCTURES_KO = [
    "결론 먼저 1~2문장 → 선택 기준 → 제품별 상세(장점/단점/추천대상) → 비교표 → FAQ 3개 → 구매 가이드",
    "독자 공감 도입 → 핵심 기준 3~4가지 → 기준별 제품 분석 → 가격대별 추천 → CTA",
    "개인 경험(첫 구매 실수) → 배운 선택 기준 → 추천 제품 분석 → 비교표 → 구매 팁",
    "체크리스트 5~7개 먼저 → 각 기준 상세 설명+제품 매칭 → 최종 TOP 3",
    "질문 형태 도입 → 객관적 데이터 답변 → 대안 제시 → 상황별 추천 → 결론",
]
STRUCTURES_EN = [
    "Verdict first → selection criteria → product analysis (pros/cons/for whom) → table → FAQ → guide",
    "Reader empathy → 3-4 key criteria → analyze by criteria → price-range picks → CTA",
    "Personal story (mistake) → learned criteria → top picks analysis → table → tips",
    "5-7 checklist first → explain each with product matches → TOP 3",
    "Question opening → data-backed answers → alternatives → situational picks → verdict",
]
DETAILS_KO = [
    "최근 3개월 가격 변동 추이와 최저가 시기/경로를 구체적으로 언급",
    "실제 구매자 리뷰에서 반복되는 불만 2~3개를 솔직하게 포함",
    "경쟁 제품 대비 숨겨진 장점/차별 포인트를 구체적으로 강조",
    "상황별(1인가구/가족/사무실) 다른 추천을 제시",
    "초보자 질문 3개를 Q&A 형태로 포함",
    "전문가 인터뷰 형식으로 신뢰감을 높이는 내용 삽입",
    "실제 측정 데이터나 테스트 결과를 표로 정리",
    "흔한 구매 실수 사례를 먼저 보여주고 올바른 선택법으로 연결",
]
DETAILS_EN = [
    "Mention 3-month price trends and cheapest buying time/place",
    "Include 2-3 common complaints from verified buyer reviews",
    "Highlight hidden advantages vs competitors specifically",
    "Provide different picks by situation (single/family/office)",
    "Include 3 beginner Q&As", "Add expert-style quotes for credibility",
    "Present measurement data or test results in a table",
    "Show common buying mistakes first, then the right choice",
]

def _unique_seed(tenant_id, keyword):
    now = datetime.now()
    s = f"{tenant_id}:{keyword}:{now.strftime('%Y%m%d%H%M%S')}:{random.randint(0,999999)}"
    random.seed(int(hashlib.sha256(s.encode()).hexdigest()[:10], 16))

def _unique_title(keyword, lang, tenant_id):
    year = datetime.now().year
    n = random.choice([3, 5, 7, 10])
    fmts = TITLE_FMT_KO if lang == "ko" else TITLE_FMT_EN
    v = int(hashlib.md5(f"{tenant_id}:{keyword}:{random.randint(0,9999)}".encode()).hexdigest()[:6], 16)
    return fmts[v % len(fmts)].format(keyword=keyword, year=year, n=n)

def build_unique_prompt(keyword, niche, prompt_type, language, affiliate_link, tenant_id):
    _unique_seed(tenant_id, keyword)
    ph = int(hashlib.md5(tenant_id.encode()).hexdigest()[:4], 16)
    persona = (PERSONAS_KO if language=="ko" else PERSONAS_EN)[ph % 10]
    structure = random.choice(STRUCTURES_KO if language=="ko" else STRUCTURES_EN)
    dets = random.sample(DETAILS_KO if language=="ko" else DETAILS_EN, k=3)
    temp = round(random.uniform(0.6, 0.85), 2)
    title = _unique_title(keyword, language, tenant_id)

    html_rule = "반드시 HTML 형식으로만 출력. 마크다운(#, *, ```) 절대 사용 금지. <h2>,<p>,<ul>,<li>,<table>,<strong>,<em> 태그만 사용. <h1> 사용 금지." if language=="ko" else "Output ONLY HTML. NEVER use Markdown. Use only <h2>,<p>,<ul>,<li>,<table>,<strong>,<em>. NO <h1>."

    if language == "ko":
        system = f"당신은 전문 블로그 콘텐츠 작성자입니다.\n{persona}\n\n중요: {html_rule}"
        user = f"""제목: {title}
키워드: {keyword} | 카테고리: {niche}

=== 출력 형식 ===
첫 줄: ---TITLE: {title}---
마지막 줄: ---META: 150자 이내 메타디스크립션---
중간: 순수 HTML만

=== 작성 규칙 ===
1. {html_rule}
2. <h2> 소제목 5~7개 (키워드 변형 포함)
3. 총 2,000~3,000자 (짧은 글 금지)
4. 글 구조: {structure}
5. 반드시 <table> 비교표 1개+ (3~5개 제품 비교, <th>헤더 포함)
6. <ul><li> 리스트 2개+
7. {dets[0]}
8. {dets[1]}
9. {dets[2]}
10. 이미지 위치: [IMAGE_SLOT_1] (첫H2 아래), [IMAGE_SLOT_2] (비교표 위), [IMAGE_SLOT_3] (결론 위)
11. 글 끝 CTA{f' (링크: {affiliate_link})' if affiliate_link else ''}
12. 도입부에 독자 관심을 끄는 강력한 첫 문장
13. 각 H2 섹션 150자+"""
    else:
        system = f"You are a professional blog writer.\n{persona}\n\nCritical: {html_rule}"
        user = f"""Title: {title}
Keyword: {keyword} | Category: {niche}

=== FORMAT ===
Line 1: ---TITLE: {title}---
Last line: ---META: under 155 chars---
Middle: Pure HTML only

=== RULES ===
1. {html_rule}
2. 5-7 <h2> subheadings with keyword variations
3. 2,000-3,000 words (short articles NOT acceptable)
4. Structure: {structure}
5. At least 1 <table> comparison (3-5 products, with <th> headers)
6. At least 2 <ul><li> lists
7. {dets[0]}
8. {dets[1]}
9. {dets[2]}
10. Images: [IMAGE_SLOT_1] after first H2, [IMAGE_SLOT_2] before table, [IMAGE_SLOT_3] before conclusion
11. CTA at end{f' (link: {affiliate_link})' if affiliate_link else ''}
12. Attention-grabbing opening sentence
13. Each H2 section 100+ words"""

    return system, user, temp, title

# ===== API Callers =====
def _call_grok(system, user, temperature):
    key = os.getenv("GROK_API_KEY")
    if not key: raise ValueError("GROK_API_KEY not set")
    r = requests.post("https://api.x.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "grok-4-1-fast", "temperature": temperature, "max_tokens": 8000,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], "grok-4-1-fast"

def _call_gemini(system, user, temperature):
    key = os.getenv("GEMINI_API_KEY")
    if not key: raise ValueError("GEMINI_API_KEY not set")
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
        headers={"Content-Type": "application/json"},
        json={"systemInstruction": {"parts": [{"text": system}]},
              "contents": [{"parts": [{"text": user}]}],
              "generationConfig": {"temperature": temperature, "maxOutputTokens": 8000}}, timeout=180)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"], "gemini-2.0-flash"

def _call_claude(system, user, temperature):
    key = os.getenv("CLAUDE_API_KEY")
    if not key: raise ValueError("CLAUDE_API_KEY not set")
    r = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
        json={"model": "claude-haiku-4-5-20251001", "max_tokens": 8000, "temperature": temperature,
              "system": system, "messages": [{"role": "user", "content": user}]}, timeout=180)
    r.raise_for_status()
    return r.json()["content"][0]["text"], "claude-haiku-4-5"

def _call_openai(system, user, temperature):
    key = os.getenv("OPENAI_API_KEY")
    if not key: raise ValueError("OPENAI_API_KEY not set")
    r = requests.post("https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o-mini", "temperature": temperature, "max_tokens": 8000,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], "gpt-4o-mini"

AI_CALLERS = {"grok": _call_grok, "gemini": _call_gemini, "claude": _call_claude, "openai": _call_openai}
DEFAULT_PRIORITY = ["grok", "gemini", "claude", "openai"]

def _md_to_html(text):
    text = re.sub(r'```html?\s*\n?', '', text)
    text = re.sub(r'```\s*\n?', '', text)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    lines, result, in_list = text.split('\n'), [], False
    for line in lines:
        s = line.strip()
        if re.match(r'^[-*]\s', s):
            if not in_list: result.append('<ul>'); in_list = True
            result.append(f'<li>{re.sub(r"^[-*]\\s+", "", s)}</li>')
        else:
            if in_list: result.append('</ul>'); in_list = False
            if s and not s.startswith('<') and not s.startswith('---'):
                result.append(f'<p>{s}</p>')
            else:
                result.append(line)
    if in_list: result.append('</ul>')
    return '\n'.join(result)

def _parse_response(raw, fallback_title=""):
    title, meta, content = "", "", raw
    m = re.search(r'---TITLE:\s*(.+?)\s*---', raw)
    if m: title = m.group(1).strip(); content = content.replace(m.group(0), "")
    m = re.search(r'---META:\s*(.+?)\s*---', raw, re.DOTALL)
    if m: meta = m.group(1).strip()[:155]; content = content.replace(m.group(0), "")
    if '```' in content or re.search(r'^#+\s', content, re.MULTILINE):
        content = _md_to_html(content)
    if not title: title = fallback_title
    if not title:
        h = re.search(r'<h2[^>]*>(.+?)</h2>', content)
        if h: title = re.sub(r'<[^>]+>', '', h.group(1)).strip()
    if not meta:
        p = re.sub(r'<[^>]+>', '', content); meta = re.sub(r'\s+', ' ', p).strip()[:150]
    content = re.sub(r'<p>\s*</p>', '', content.strip())
    content = re.sub(r'\n{3,}', '\n\n', content)
    return title, content, meta

def generate_post(keyword, niche, prompt_type, language, affiliate_link, tenant_id, preferred_model="auto"):
    system, user, temp, title_hint = build_unique_prompt(keyword, niche, prompt_type, language, affiliate_link, tenant_id)
    print(f"  [Prompt] Title: {title_hint} | Temp: {temp}")
    priority = list(DEFAULT_PRIORITY)
    c = os.getenv("AI_PRIORITY")
    if c: priority = [x.strip() for x in c.split(",") if x.strip()]
    if preferred_model != "auto" and preferred_model in AI_CALLERS:
        if preferred_model in priority: priority.remove(preferred_model)
        priority.insert(0, preferred_model)
    last_err = None
    for mk in priority:
        caller = AI_CALLERS.get(mk)
        if not caller: continue
        try:
            raw, model = caller(system, user, temp)
            t, ct, mt = _parse_response(raw, fallback_title=title_hint)
            plain = re.sub(r'<[^>]+>', '', ct)
            if len(plain) < 500:
                print(f"  [RETRY] {mk}: too short ({len(plain)} chars)")
                continue
            return {"title": t, "content": ct, "meta_description": mt, "model_used": model, "temperature": temp}
        except Exception as e:
            last_err = e; print(f"  [FALLBACK] {mk}: {e}"); continue
    raise RuntimeError(f"All AI models failed: {last_err}")
