# Luvoire Landing Page - Design Brief v1

Author: Celovin (Choi Jihwan)
Date: 2026-04-22
Target: Claude Designer (web service)
Deliverable: `luvoire.com` 루트 랜딩 페이지 (정적 또는 Next.js 15+ SSG)
Scope: 단일 랜딩 페이지 (기능 페이지 / 문서 / 가격 / 상태 페이지는 별도 라우트, 이번 브리프 범위 밖)

---

## 1. Product One-Liner

Luvoire는 **결정적으로 재생 가능한 에이전트 기반 시뮬레이션 엔진**입니다. 연구자가 논문에 인용하고 게임 스튜디오가 NPC에 탑재할 수 있는 수준의 단일 Python 엔진.

Pronunciation guide (소규모 UI 컴포넌트로 노출): **Luvoire** /luː.vwɑːr/ — 루부아르

어원 내러티브 (사용 선택):
- 프랑스어 `-oire` 접미사 계열 — **mémoire**(기억) · **histoire**(역사) · **répertoire**(목록)
- 세 개념이 곧 이 엔진의 핵심 스택 (memory · replay · persona library)

---

## 2. Target Audience

### Primary (1차 — H1·히어로 카피는 이 그룹 기준)

- 계산 사회과학 · 범죄학 · 도시학 · agent-based modeling (ABM) 연구자 및 대학원생
- 시뮬레이션 기반 논문을 쓰거나 심사하는 교수
- Didimdol · NRF · MSIT 등 한국 연구 grant 심사·제안자

### Secondary (2차 — 기능 섹션에서 확장)

- 게임 스튜디오 NPC 디자이너·테크니컬 디렉터 (결정적 재현성 필요 케이스)
- 기업 R&D 랩 (위기 시뮬레이션, 운영 계획)
- 도시·교통·안전 정책 시뮬레이션 팀

### Tertiary (3차 — 부차적)

- 개발자 오픈소스 커뮤니티 (ABM에 LLM 접목 관심군)

---

## 3. Positioning

### vs. 기존 ABM 도구 (NetLogo · MASON · Repast · Mesa)

- **Luvoire는 LLM 네이티브** — 에이전트 의사결정·대화·기억이 LLM으로 구동 (기존 룰 기반 ABM에서 불가능한 규모의 개성 표현)
- **Luvoire는 결정적 재생** — 동일 시드에서 SHA256 byte-identical msgpack 생성, 재현성 논문 심사 통과 수준
- **Luvoire는 10K 에이전트까지 검증됨** — 60×60 격자 도시 규모, 공개 벤치마크

### vs. 상용 게임 AI (Inworld · Convai 등)

- **Luvoire는 연구 pedigree** — CAT-28 학술 참고문헌 기반, Nemotron CC-BY-4.0, SBOM·attribution 완비, 논문에서 검증 가능한 재현성
- **Luvoire는 자체 호스팅 가능** — 엔터프라이즈 티어 on-prem, 데이터 주권 확보

### vs. 의사결정 플랫폼 (pol.is 등)

- 카테고리 자체가 다름 (**시뮬레이션** vs. **심의**). 랜딩에서 직접 언급 불필요. 필요시 FAQ 배치.

---

## 4. Visual Direction

### 4.1 Palette

CLAUDE DESIGNER TO NOTE: **TheLabForge의 테라코타 팔레트를 재사용하지 마세요**. Luvoire는 Celovin 포트폴리오 내 별도 제품이며 시각적 중복을 피해야 합니다.

제안 팔레트 (조정 가능):

- **Base**: Warm cream `#F7F3EC` 또는 clean off-white `#FAFAF7`
- **Text primary**: Near-black `#141414`
- **Text secondary**: Deep taupe `#5C5148`
- **Accent 1 (Primary)**: Antique bronze/burnished gold `#A8753A` 계열 (Louvre·박물관·-oire 격조 연상)
  - 대체안: Ink-navy `#1E293B` (보수적 선택)
- **Accent 2 (Secondary)**: Muted sage `#7A8F7B` 또는 dove gray `#9AA0A6` (차분한 보조)
- **Error/Alert**: Oxblood `#7F1D1D` (최소 사용)
- **Code block bg**: `#1A1815` (진한 갈색-검정, 크림과 대비)

**금지 색상**:
- 테라코타 오렌지 계열 (TheLabForge 전용)
- 민트·에메랄드 그린 (Seizn/Praxiqa 영역 — 엔티티 분리 위반 리스크)

### 4.2 Typography

- **Display/Headings**: 우아한 세리프
  - 1순위: **Source Serif 4** (오픈소스, 가변) 또는 **Crimson Pro**
  - 대체: Fraunces (variable, 학술 톤)
- **Body/UI**: 한영 혼용 최적화 sans
  - 1순위: **Pretendard Variable** (한글) + **Inter Variable** (영문) 페어링
  - 또는 Pretendard 단독 (한글·라틴 모두 커버)
- **Mono**: **JetBrains Mono** 또는 **IBM Plex Mono**

### 4.3 Tone / Voice

- **에디토리얼하고 신중함** — 학술지 introduction 문단 톤
- **과장 없음** — "혁신적인 AI 플랫폼" 금지. "결정적으로 재생 가능한 에이전트 엔진" 같이 사실 서술
- **단문 + 구체성** — 능동태, 숫자, 고유명사 선호
- **이모지 0개**. 인용부호는 작은 따옴표 ''만 사용 (큰 따옴표 "" 금지)

### 4.4 Motion / Interaction

- 스크롤 기반 가벼운 fade/translate (20-40px, 300ms)
- 에이전트 격자 히어로 비주얼은 **자동 루프 재생 (6-10초)**, 정지 가능 버튼 노출
- 호버·포커스 상태는 underline + tonal shift (컬러 flash 금지)
- Reduced-motion 쿼리 존중

---

## 5. Page Structure (Top to Bottom)

### 5.1 Top Nav (sticky)

- 좌: Luvoire 워드마크 (발음 툴팁 `/luː.vwɑːr/`)
- 중앙: `Features` · `Research` · `Pricing` · `Docs` · `Status`
- 우: `GitHub` (외부 링크 아이콘) · `Sign in` (고스트 버튼) · `Start free` (프라이머리)
- 언어 토글: EN / KO (초기 2개, 추후 확장)

### 5.2 Hero

- **H1 후보 (Claude Designer가 선택 또는 변주):**
  1. `Agent simulation that remembers.`
  2. `Deterministic multi-agent simulation for research and production.`
  3. `Replayable city-scale simulation, citable in papers.`

  추천: 1번 (mémoire 어원 이중 의미, 짧음, 학술 + 상용 공존)

- **Sub (H1 아래 1-2줄, ~120-180자):**
  > City-scale multi-agent simulation with deterministic replay, a layered memory stack, and 28 research-grounded personality archetypes. Open methodology, reproducible artifacts, commercial tiers.

- **CTA 블록:**
  - Primary: `Try the playground →` (HF Space 링크)
  - Secondary: `Read the paper →` (임시로 Didimdol 1-pager PDF 또는 preprint 링크, 후속 처리)
  - 작은 텍스트: `pip install luvoire-engine` (원클릭 복사, monospace)

- **Hero visual:**
  - 격자 (60×60 grid) 위에 에이전트 점이 이동하는 minimal SVG/Canvas 애니메이션
  - 저채도, 낮은 프레임레이트 (8fps 수준), 시청각 stress 최소화
  - 재생 바 (replay timeline) 하단 표시 — '결정적 재생' 정체성 강조
  - Reduced-motion 환경에서는 정지 프레임 + `▶ Play` 버튼

### 5.3 Social Proof Strip (Placeholder)

- 초기 버전: grant·학회·파트너 플레이스홀더 (논리적 여백 확보)
  - 예: "Submitted to ASC 2026" · "Part of Celovin's research stack" · "Nemotron-Personas-Korea (NVIDIA, CC-BY-4.0)"
- 실데이터 쌓이면 로고 스트립으로 교체 (약관: 실제 허가 받은 기관만)

### 5.4 Core Capabilities (3-4 columns)

헤더: `What Luvoire gives you`

1. **Deterministic replay**
   - 동일 시드에서 SHA256 byte-identical 재생. 10K 에이전트까지 공개 검증.
   - 지표: `replay_10000agents_gangnam_7pm.msgpack` · 9.5MB · SHA pinned

2. **Layered memory stack**
   - 작업 기억 · 에피소드 기억 · 장기 기억 분리. 세션 간 지속, 망각 동력학 포함.

3. **28 research-grounded personas**
   - CAT-28 아키타입 (22 single + 6 composite) + 범죄학 Tier 1/2 아키타입. 학술 참고문헌 포함.

4. **Open methodology**
   - CycloneDX SBOM · attribution · audit log · reproducible artifacts. 연구 심사 · 컴플라이언스 대응.

각 카드: 아이콘/심볼 + 제목 + 2줄 설명 + "Learn more →" 링크.

### 5.5 Live Playground Preview

- 헤더: `See it replay`
- 내용: HF Space 임베드 (iframe) 또는 녹화 MP4/WebM 스크린캐스트
- 캡션: "60×60 격자, 10,000 에이전트, 강남 오후 7시 시뮬레이션. 모든 프레임 결정적으로 재현 가능."
- CTA: `Open full playground →`

### 5.6 Research Positioning

헤더: `Built for research-grade work`

블록 레이아웃 (2×2 또는 가로 4열):

1. **Bibliography-backed archetypes**
   - CAT-28은 12개 동료 리뷰 인용 + 6권의 단행본 (DOI · ISBN · ISSN 명시)
   - Link: `View citations →`

2. **Dataset provenance**
   - Nemotron-Personas-Korea (NVIDIA, 2025) · CC-BY-4.0 · KOSIS 인구통계 기반 · 리비전 SHA 핀

3. **Reproducible artifacts**
   - 5개 공개 replay msgpack 파일 · SHA256 고정 · 15% regression guard · 주간 CI 검증

4. **Commercial-ready**
   - MIT 라이선스 코어 + 상업 티어 · Toss Payments KR + Paddle global · PIPA/GDPR 대비 개인정보 처리방침 초안

### 5.7 Pricing Preview

- 4 티어 카드 요약 (Free · Pro $49/mo · Team $199/mo · Enterprise 문의)
- 상세 비교 표는 `/pricing` 페이지로 이관, 랜딩에는 핵심 숫자만
- "Start free" / "Book a call" CTA

### 5.8 Use Cases (3 segment strips)

가로 3열:

1. **For researchers** — "Cite Luvoire in your methods section." · 예시 인용 BibTeX · `How to cite →`
2. **For game studios** — "Ship NPCs with behavior that holds up to playtest." · 예시 통합 코드 · `Get a Team license →`
3. **For R&D labs** — "Run scenario simulations with auditable replay." · 엔터프라이즈 연락 · `Talk to sales →`

### 5.9 Technical Quickstart

- 헤더: `Get running in 60 seconds`
- 코드 블록 (탭: Python · CLI · REST):
  ```python
  import luvoire

  sim = luvoire.City(grid=(60, 60), agents=10_000, seed=42)
  replay = sim.run(ticks=100)
  replay.save("my_run.msgpack")  # deterministic
  ```
- 대체 카드: CLI / cURL / Unity adapter

### 5.10 Trust Signals

가로 스트립, 작은 아이콘 + 레이블:

- `CC-BY-4.0 dataset` (Nemotron attribution)
- `MIT core license`
- `CycloneDX SBOM`
- `Audit log (PIPA-ready)`
- `Stripe metering`
- `HMAC-SHA256 webhooks`

각 항목은 해당 문서·페이지로 연결.

### 5.11 Footer

- 좌: Celovin 로고 + `A research engine by Celovin.`
- 중앙: Product · Research · Legal · Status 4열
- 우: GitHub · Email `hello@celovin.com` · Pronunciation `Luvoire /luː.vwɑːr/`
- 하단 법적 줄: `© 2026 Celovin · Terms · Privacy · DPA · Refund Policy`

---

## 6. Draft Copy (Claude Designer may refine tone)

### EN

- H1: `Agent simulation that remembers.`
- Sub: `City-scale multi-agent simulation with deterministic replay, a layered memory stack, and 28 research-grounded personality archetypes. Open methodology, reproducible artifacts, commercial tiers.`
- Primary CTA: `Try the playground`
- Secondary CTA: `Read the paper`
- Install tagline: `pip install luvoire-engine`

### KO

- H1: `기억하는 에이전트 시뮬레이션.`
- Sub: `결정적으로 재생 가능한 도시 규모 멀티 에이전트 시뮬레이션. 계층형 메모리 스택과 28개의 학술 근거 성격 아키타입. 개방된 방법론, 재현 가능한 산출물, 상업 티어.`
- Primary CTA: `플레이그라운드 열기`
- Secondary CTA: `논문 읽기`
- Install tagline: `pip install luvoire-engine`

모든 카피: **이모지 0개 · 큰 따옴표 "" 대신 작은 따옴표 '' · 불필요한 영어 감탄사 금지**.

---

## 7. CTAs & Funnel

단일 랜딩에서 3개 이상의 primary CTA 금지. 우선순위:

1. **Playground 진입** (가장 가벼운 상호작용, 제품 체감)
2. **Pricing 진입** (상용 전환 의도)
3. **Docs 진입** (기술 평가 의도)

`Sign up` / `Get API key`는 Pricing 페이지에서 처리. 랜딩에서는 Playground가 최우선 터미널.

---

## 8. Technical Requirements

- **프레임워크**: Next.js 15+ (App Router, SSG 기본, ISR 불필요)
- **스타일**: Tailwind CSS v4 + CSS variables for theme tokens
- **i18n**: EN / KO 초기 릴리스 (`next-intl` 또는 `next-i18next`). 추가 locale은 slug만 확장 가능한 구조.
- **성능 목표**:
  - LCP < 1.8s (4G 기준)
  - JS bundle < 180KB gzipped
  - CLS < 0.05
  - Hero 애니메이션은 30KB 이하 SVG/Canvas, GIF/MP4 금지 (bandwidth 낭비)
- **접근성**: WCAG 2.1 AA. 모든 상호작용 요소 키보드 통과. prefers-reduced-motion 존중. focus ring 시각적 명확.
- **SEO**:
  - OG 이미지 1200×630 (격자 + 워드마크)
  - schema.org `SoftwareApplication` + `Organization`
  - canonical URL · `hreflang` EN/KO
- **Analytics**: Plausible 또는 self-hosted (Google Analytics 금지 — PIPA/GDPR 복잡도)

---

## 9. Don'ts (금지 목록)

- 이모지 사용 금지 (전 페이지 절대 규칙)
- 큰 따옴표 `""` 금지, 작은 따옴표 `''`만
- "혁신적" · "차세대" · "AI 기반" 같은 buzz 어휘 남용 금지
- 가짜 통계 / 미검증 수치 (`사용자 10,000명` 같은 플레이스홀더 숫자 금지)
- Stock photo (특히 인물 사진) 금지 — 박물관·고전 모티브 또는 추상 그래픽
- Terracotta / salmon orange 계열 (TheLabForge 전용)
- Mint green · emerald (Seizn/Praxiqa 영역)
- 어떤 파일에도 다음 문자열 금지: `Litheon` · `Seizn` · `Ovriel` · `Fangden` · `Notrivo` · `Milkypix` · `Yami`
- 경쟁사 FUD (NetLogo·Mesa·Inworld 직접 비판 금지, 포지셔닝만)

---

## 10. References (for visual inspiration, not to copy)

- **[stripe.com](https://stripe.com)** — 기술 제품 명료성
- **[linear.app](https://linear.app)** — 미니멀 에디토리얼
- **[scikit-learn.org](https://scikit-learn.org)** — 학술 도구 톤
- **[mesa-abm.org](https://mesa.readthedocs.io)** — ABM 도구 레퍼런스 (단 우리는 더 현대적)
- **[anthropic.com](https://anthropic.com)** — 학술 + 상용 혼합 톤
- **[fraunces.dev](https://fonts.google.com/specimen/Fraunces)** — 서체 참고

참고 레퍼런스는 **모사 대상이 아니라 톤 기준점**. Luvoire만의 격조 (-oire / 박물관 / 학술 / 재현성) 자체 구축.

---

## 11. Assets Checklist (Claude Designer가 생성 또는 요청)

- [ ] Luvoire 워드마크 (SVG, light + dark 버전)
- [ ] 로고마크 심볼 옵션 3개 (격자·재생 바·-oire 리본 중 택)
- [ ] OG 이미지 1200×630 (1종)
- [ ] Hero 격자 애니메이션 컴포넌트 (React + Canvas 또는 SVG)
- [ ] Favicon (ICO + SVG + 192/512 PNG)
- [ ] Pronunciation 툴팁 컴포넌트
- [ ] 4가지 Use-case 일러스트 (추상, 인물 없음)
- [ ] 코드 샘플 스니펫 3종 (Python · CLI · cURL)
- [ ] Footer 파트너 logo strip (플레이스홀더 4-6개)

---

## 12. Out of Scope (이번 브리프 제외)

- 풀 docs 사이트 디자인 (mkdocs 기존 테마 유지)
- 대시보드 / 로그인 UI (별도 브리프)
- 블로그 / changelog 페이지 (별도)
- Paywall / checkout flow (Stripe Meter + Toss 연동 별도)
- 이메일 디자인 (웹훅 영수증 · 온보딩 메일)

---

## 13. Timeline / Handoff

- **Draft 1**: Hero + Pricing preview + Footer (48-72시간 목표)
- **Draft 2**: 전체 섹션 통합 + i18n 구조 (추가 48시간)
- **Review 게이트**: 사용자(Celovin) 승인 후 Vercel preview 배포 → `luvoire.com` DNS 연결 (사용자 작업)

의견·변경 요청은 이 문서 `## 14. Revisions` 섹션에 append.

---

## 14. Revisions

_(빈 섹션 — Claude Designer 또는 사용자가 수정 요청 시 여기 기록)_
