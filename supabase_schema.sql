-- =============================================
-- WP Auto-Blog: Supabase 멀티테넌트 스키마
-- 대시보드 연동용. Supabase SQL Editor에서 실행.
-- =============================================

-- 1. 유저/테넌트 테이블
CREATE TABLE IF NOT EXISTS public.tenants (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    name VARCHAR(100) NOT NULL,
    persona_id VARCHAR(20) DEFAULT 'expert',
    niche_id VARCHAR(20),
    language VARCHAR(5) DEFAULT 'ko',
    ai_priority TEXT DEFAULT 'grok,gemini,claude,openai',
    wp_url TEXT,
    wp_user VARCHAR(100),
    wp_app_password TEXT,
    github_repo TEXT,
    unsplash_key TEXT,
    pexels_key TEXT,
    temperature DECIMAL(3,2) DEFAULT 0.75,
    angle_index INTEGER DEFAULT 0,
    structure_index INTEGER DEFAULT 0,
    detail_indexes INTEGER[] DEFAULT '{0,3,6}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 키워드 테이블
CREATE TABLE IF NOT EXISTS public.keywords (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    niche VARCHAR(50),
    prompt_type VARCHAR(20) DEFAULT 'review',
    ai_model VARCHAR(20) DEFAULT 'auto',
    language VARCHAR(5) DEFAULT 'ko',
    affiliate_link TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    published_url TEXT,
    published_date TIMESTAMPTZ,
    quality_score INTEGER,
    word_count INTEGER,
    ai_model_used VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 발행 로그 테이블
CREATE TABLE IF NOT EXISTS public.publish_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    keyword_id UUID REFERENCES public.keywords(id),
    title TEXT,
    url TEXT,
    ai_model VARCHAR(50),
    quality_score INTEGER,
    word_count INTEGER,
    image_count INTEGER,
    temperature DECIMAL(3,2),
    cost_estimate DECIMAL(10,6),
    status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 수익 추적 테이블
CREATE TABLE IF NOT EXISTS public.revenue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    month VARCHAR(7) NOT NULL,  -- '2026-03'
    adsense_revenue DECIMAL(10,2) DEFAULT 0,
    affiliate_revenue DECIMAL(10,2) DEFAULT 0,
    other_revenue DECIMAL(10,2) DEFAULT 0,
    ai_cost DECIMAL(10,2) DEFAULT 0,
    hosting_cost DECIMAL(10,2) DEFAULT 0,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, month)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_keywords_tenant_status ON public.keywords(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_keywords_status ON public.keywords(status);
CREATE INDEX IF NOT EXISTS idx_logs_tenant ON public.publish_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_revenue_tenant ON public.revenue(tenant_id);

-- RLS (Row Level Security) 활성화
ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.publish_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.revenue ENABLE ROW LEVEL SECURITY;

-- RLS 정책: 자기 데이터만 접근
CREATE POLICY "tenants_own" ON public.tenants
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "keywords_own" ON public.keywords
    FOR ALL USING (
        tenant_id IN (SELECT id FROM public.tenants WHERE user_id = auth.uid())
    );

CREATE POLICY "logs_own" ON public.publish_logs
    FOR ALL USING (
        tenant_id IN (SELECT id FROM public.tenants WHERE user_id = auth.uid())
    );

CREATE POLICY "revenue_own" ON public.revenue
    FOR ALL USING (
        tenant_id IN (SELECT id FROM public.tenants WHERE user_id = auth.uid())
    );

-- 서비스 키용 정책 (GitHub Actions에서 접근)
CREATE POLICY "service_keywords" ON public.keywords
    FOR ALL USING (true)
    WITH CHECK (true);
