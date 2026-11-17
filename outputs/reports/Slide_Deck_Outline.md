# CoffeeGraph — Figma Slides 보고서 장표 구성안 (10 Slides)

- **작성 기준**: `CHO-YOUN-SIK/CoffeeGraph` 감사 완료본 (`f2136ce`) 기반
- **권장 톤앤매너**: 미니멀 리서치 덱 (White/Warm Off-White 배경, Deep Espresso `#2C1E16` 타이틀, Forest Green `#1B9E77` / Amber `#D95F02` 포인트, 1장표 1메시지 원칙)

---

## Slide 1. 표지 (Title)
- **메인 타이틀**: **Coffee Brand Opportunity Map**
- **서브 타이틀**: 서울 커피 시장 구조 · 소비 맥락 · CQI 품질 · 브랜드 향미 언어 교차 분석 기반 BX/CX 기회 탐색
- **하단 메타**: 데이터 출처: 서울 열린데이터광장(673,280행) · CQI(1,339건) · 공식 브랜드 몰(8개 브랜드 129 SKU) | 기준: 2026Q1 (2026Q2 병기)

---

## Slide 2. 연구 목적 및 방법론 (Research Design & Integrity)
- **헤드라인**: *"단순 트렌드 조사가 아닌, 원천 데이터 추적 가능한 BX/CX 기회 구조화"*
- **3대 원천 데이터 & 결합 원칙**:
  1. **Direct Join**: 서울시 공공데이터 (`OA-22173·22176·15577·15572`, `CS100010` 커피-음료)
  2. **Reference Analysis**: CQI 국제 커핑 데이터 (1,339건) — *개별 국내 제품 점수로 직접 결합 금지*
  3. **Context Join & Comparative**: 8개 브랜드 공식 온라인몰 직접 수집 (스페셜티 7 + 프랜차이즈 비교군 1, 총 129 SKU)
- **연구 무결성 원칙**: `Observed(관찰)` / `Interpretation(해석)` / `Hypothesis(가설)` / `Unknown(미측정)` 엄격 분리

---

## Slide 3. 서울 커피 시장 전체 추이 (2024Q2 → 2026Q2)
- **헤드라인**: *"25개 중 23개 구 점포 감소 속, 프랜차이즈 여부가 아닌 '점포당 매출 체력'이 생존을 가른다"*
- **핵심 KPI 카드 3개**:
  - **27,333개**: `2026Q1` 서울 커피·음료 점포 (`2024Q2` 28,639개 대비 -4.56%, `2026Q2` 27,351개 소폭 반등)
  - **23 / 25개 구**: 점포 순감 자치구 수 (영등포구·용산구만 순증)
  - **$r = 0.5641$** ($p = 0.0033$): 점포당 매출 vs 점포 변화율 (반면 프랜차이즈 비중 $r = 0.0145, p = 0.945$)
- **배치 차트**: [`fig01_seoul_quarterly_trend.png`](file:///home/antigravity/CHO-YOUN-SIK/CoffeeGraph/outputs/figures/fig01_seoul_quarterly_trend.png) + [`fig02_district_store_change_vs_sales.png`](file:///home/antigravity/CHO-YOUN-SIK/CoffeeGraph/outputs/figures/fig02_district_store_change_vs_sales.png)

---

## Slide 4. 서울 상권 소비 맥락 4개 유형 (`2026Q1`, n=1,064)
- **헤드라인**: *"매출이 가장 높은 '오피스·점심형'과 체류가 긴 '주말·방문형'으로 소비 맥락이 분화된다"*
- **표본 선정 깔때기**: `2026Q1` 점포 상권 1,519개 → 매출 매칭 상권 **1,064개** (소규모·마스킹 455개 제외)
- **4개 군집 요약 테이블**:
  - **오피스·점심 집중형 (n=275)**: `11~14시` **48.28%** | 주말 16.57% | 점포당 **2,283만 원** (최고)
  - **주말·방문형 (n=269)**: 주말 **35.42%** | `17~21시` 26.94% | 점포당 **2,197만 원**
  - **모닝·복합형 (n=484)**: `11~14시` 34.62% | 주말 32.98% | 점포당 1,943만 원
  - **저녁·생활형 (n=36)**: `17~21시` **29.58%** | 점포당 **878만 원** (최저)
- **방법론 각주**: `k=4` Silhouette = `0.1798`, 5시드 ARI = `0.9815` → 연속적 스펙트럼 위의 탐색적 유형화(Archetypes)
- **배치 차트**: [`fig03_commercial_context_clusters.png`](file:///home/antigravity/CHO-YOUN-SIK/CoffeeGraph/outputs/figures/fig03_commercial_context_clusters.png)

---

## Slide 5. 글로벌 CQI 품질 데이터 전수 분석 (1,339건)
- **헤드라인**: *"'내추럴=고품질' 통념은 산지 통제 시 통계적으로 사라진다 — 가공법은 절대 품질 신호가 아니다"*
- **핵심 수치**:
  - 전수 1,339건 (Arabica 1,311 + Robusta 28) → 0점 이상치 1건 제외 유효 Arabica **n=1,310**
  - 상위 5개 산지 표본 편중 **61.62%** (Mexico, Colombia, Guatemala, Brazil, Taiwan)
  - `Natural` vs `Washed` 원차이 **+0.39점** ($p=0.049$) → **산지 통제 OLS +0.27점 ($p=0.2585$, 비유의)**
- **시사점**: CQI는 커핑 점수일 뿐 국내 소비자 선호가 아니며, 가공법 명칭만으로 소비자에게 품질을 설득하기 어렵다.
- **배치 차트**: [`fig04_cqi_processing_and_country.png`](file:///home/antigravity/CHO-YOUN-SIK/CoffeeGraph/outputs/figures/fig04_cqi_processing_and_country.png)

---

## Slide 6. 브랜드 향미 언어 및 포지셔닝 비교 (8개 브랜드, 129 SKU)
- **헤드라인**: *"스페셜티 브랜드는 '감성·추상 서사'와 '전문 감각 스펙' 사이에서 극단적으로 분화되어 있다"*
- **9차원 향미 언어 코드북 분석 결과**:
  - **감성·추상 중심**: 테라로사(100%), 블루보틀(83.3%, 감각차원 4.00), 센터커피(71.4%)
  - **감각·스펙 중심**: 커피리브레(감성 0.0%, 9,500원/100g), 펠트(감성 13.6%, 감각차원 1.86, 13,250원/100g)
  - **균형/대중 비교**: 프릳츠(감성 30.0%, 9,000원/100g), 폴바셋(프랜차이즈 비교군 20 SKU, 감각차원 0.10)
- **채널 명시**: 공식 온라인몰/카탈로그 기준(오프라인 매장 SKU 및 개별 매출과 별개)

---

## Slide 7. Coffee Brand Opportunity Map (통합 4-패널 시각화)
- **헤드라인**: *"서울 상권 맥락과 브랜드 언어 포지셔닝을 연결하면 '적정 서사 × 고감각 번역'의 기회 영역이 보인다"*
- **시각화 구성** ([`coffee_opportunity_map.html`](file:///home/antigravity/CHO-YOUN-SIK/CoffeeGraph/outputs/figures/coffee_opportunity_map.html) 캡처 또는 임베드):
  1. 서울 25개 자치구 지도 (점포 증감률 × 점포당 매출)
  2. 상권 4군집 산점도 (`n=1,064`)
  3. 브랜드 포지셔닝 맵 + **BX/CX Opportunity Whitespace** (감성 15~45% × 감각차원 $\ge 2.2$)
  4. 브랜드 × 9차원 향미 언어 히트맵
- **주의 문구**: 입지 자치구 평균 매출은 시장 배경(Context Join)이며 브랜드 개별 매출이 아님

---

## Slide 8. BX/CX 핵심 인사이트 2가지 (근거와 한계 분리)
- **Insight 1 — 상권 시간대 집중도와 탐색 마찰 가능성 (`신뢰도: Medium-Low`)**
  - *Observed*: 오피스·점심형(11~14시 48.3%) vs 주말·방문형(주말 35.4%)
  - *Interpretation*: 점심 피크 상권은 시간 압박으로 탐색 마찰이 클 수 있으나, 실제 선택 시간·혼잡도·주문 로그는 미측정 상태
- **Insight 2 — 품질 신호 비대칭과 이중 레이어 번역 (`신뢰도: Medium`)**
  - *Observed*: 가공법 단독 품질 신호 한계(CQI $p=0.259$) vs 브랜드 카피의 감성/스펙 양극화
  - *Interpretation*: 감성 서사 + 3대 감각(산미·단맛·바디) 병기가 이해도를 높일 수 있으나, 실제 소비자 이해·구매 확신은 `Unknown`

---

## Slide 9. 검증 가능한 후속 가설 (H1 · H2)
- **핵심 다음 질문**: *"원두 정보 표현 방식의 차이가 실제로 고객의 이해도·선택 소요시간·구매 전환에 어떤 영향을 미치는가?"*
- **H1 (상권 맥락 맞춤형 탐색 UI)**: 오피스형 상권 모바일 오더에서 '산미/바디 2축 + 상황 태그' 압축 UI가 전문 스펙 나열 대비 선택 시간을 단축하고 전환율을 높일 것 → *POS/주문 로그 기반 A/B 테스트*
- **H2 (이중 레이어 카피 실험)**: '감성 + 감각 번역' 병기 카피가 감성 단독/스펙 단독 대비 비전문 소비자의 이해도와 구매 의도를 높일 것 → *온라인 무작위 배정(A/B/C) 실험*

---

## Slide 10. 연구 산출물 및 재현 체계 (Summary)
- **GitHub Cloud 저장소**: `CHO-YOUN-SIK/CoffeeGraph`
- **자동화 및 검증**: `GitHub Actions` (Data Validation · Analyze Market · Analyze CQI · Build Report), `pytest` 7/7 통과
- **산출물 일람**: 보고서 A~D 4종, 인터랙티브 Opportunity Map HTML 1종, 정적 차트 4종, 근거 추적표(`evidence_ledger.csv`)
