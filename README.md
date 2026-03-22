# WP Auto-Blog: GitHub Actions Edition

WordPress 블로그 자동화 시스템. AI가 글을 쓰고, 이미지를 삽입하고, 품질을 검증하고, 자동 발행합니다.

## 기능
- **멀티 AI 로테이션**: Grok → Gemini → Claude → GPT (자동 폴백)
- **5-Layer Unique Algorithm**: 같은 키워드라도 완전히 다른 글 생성
- **이미지 자동 삽입**: Unsplash/Pexels API (무료)
- **품질 검증**: AdSense 승인 기준 100점 자동 채점
- **중복 방지**: 해시 + 유사도 3단계 체크
- **GitHub Actions**: 서버 불필요, 무료 2,000분/월

## 빠른 시작 (15분)

### 1. 이 Template Fork
`Use this template` → 자신의 레포 생성

### 2. GitHub Secrets 등록
Settings → Secrets → Actions에서 추가:

| Secret | 필수 | 예시 |
|--------|------|------|
| WP_URL | 필수 | `https://your-domain.com` |
| WP_USER | 필수 | `admin` |
| WP_APP_PASSWORD | 필수 | `xxxx xxxx xxxx xxxx` |
| GROK_API_KEY | 권장 | `xai-xxx...` |
| GEMINI_API_KEY | 권장 | `AIzaSy...` |
| CLAUDE_API_KEY | 선택 | `sk-ant-...` |
| UNSPLASH_KEY | 권장 | `Client-ID xxx` |
| PEXELS_KEY | 권장 | `xxx...` |

### 3. 키워드 추가
`data/keywords.csv`에 키워드 추가 후 커밋.

### 4. 테스트 실행
Actions 탭 → WP Auto Blog Publisher → Run workflow

## 비용
- GitHub Actions: **$0** (무료 2,000분/월)
- AI API: **$0~8/월** (Grok+Gemini 무료 티어)
- 이미지: **$0** (Unsplash/Pexels 무료)
- 총: **호스팅비만** ($11~/월)

## 파일 구조
```
scripts/
  main.py              # 메인 오케스트레이터
  ai_writer.py         # 멀티 AI + 5-Layer Unique
  image_fetcher.py     # Unsplash/Pexels 이미지
  quality_checker.py   # 100점 품질 채점
  duplicate_guard.py   # 3단계 중복 방지
  wp_publisher.py      # WordPress REST API
  sheet_manager.py     # 키워드 관리 (Supabase/CSV)
data/
  keywords.csv         # 키워드 목록
  published_hashes.json # 중복 방지 DB
.github/workflows/
  publish.yml          # GitHub Actions 스케줄
supabase_schema.sql    # 대시보드 DB 스키마
```

## 대시보드 연동
Supabase + Vercel 대시보드를 사용하면 웹에서 설정을 변경할 수 있습니다.
`supabase_schema.sql`을 Supabase SQL Editor에서 실행하세요.

---
PlanX Solution | Clone Factory v3.0
