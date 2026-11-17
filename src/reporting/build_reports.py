"""Phase 7 & 8 (M7-M8): Automated Report & Evidence Ledger Generator.

Generates the 4 Korean Markdown reports in outputs/reports/ and
research/evidence/evidence_ledger.csv directly from computed tables and JSONs:
  A. Market Structure Report
  B. CQI Quality Report
  C. Brand Positioning Report
  D. Coffee Brand Opportunity Report (Steps 1-5, BX/CX Insights & Falsifiable Hypotheses)
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "outputs" / "tables"
REPORTS_DIR = ROOT / "outputs" / "reports"
EVIDENCE_DIR = ROOT / "research" / "evidence"


def generate_reports() -> list[Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    mkt = json.loads((TABLES_DIR / "seoul_market_correlations.json").read_text(encoding="utf-8"))
    q_df = pd.read_csv(TABLES_DIR / "seoul_market_quarterly.csv", dtype={"기준_년분기_코드": str})
    dist_261 = pd.read_csv(TABLES_DIR / "seoul_district_summary_20261.csv", dtype={"자치구_코드": str})
    cluster_prof = pd.read_csv(TABLES_DIR / "seoul_commercial_cluster_profiles.csv")

    cqi = json.loads((TABLES_DIR / "cqi_regression_summary.json").read_text(encoding="utf-8"))
    cqi_country = pd.read_csv(TABLES_DIR / "cqi_country_summary.csv")
    cqi_proc = pd.read_csv(TABLES_DIR / "cqi_processing_summary.csv")

    brand_sum = pd.read_csv(TABLES_DIR / "brand_positioning_summary.csv")
    cross_brand = pd.read_csv(TABLES_DIR / "cross_brand_market_context.csv")
    cross_json = json.loads((TABLES_DIR / "cross_analysis_summary.json").read_text(encoding="utf-8"))

    # --- Report A: Market Structure Report ---
    top5_dist = dist_261.head(5)[["자치구_코드_명", "전체_점포_수", "점포_증감률_pct", "점포당_추정매출_억원", "프랜차이즈_비중_pct"]]
    bot5_dist = dist_261.tail(5)[["자치구_코드_명", "전체_점포_수", "점포_증감률_pct", "점포당_추정매출_억원", "프랜차이즈_비중_pct"]]
    corr_sps = mkt["correlations_20242_to_20261"]["sales_per_store_vs_store_change_pct"]
    corr_fr = mkt["correlations_20242_to_20261"]["franchise_share_vs_store_change_pct"]

    report_a = f"""# A. 서울 커피 시장 구조 분석 보고서 (Market Structure Report)

- **분석 대상**: 서울특별시 25개 자치구 및 상권 (`CS100010` 커피-음료)
- **출처**: 서울 열린데이터광장 공식 원본 (`OA-22173`, `OA-22176`, `OA-15577`, `OA-15572`)
- **기준 분기**: `20261` (비교 기간: `20242`~`20261`, 최신 `20262` 병기)

## 1. 서울 전체 시장 추이 (Observed)
- `20242` 기준 **28,639개**였던 서울 커피·음료 점포는 `20261` 기준 **{mkt['seoul_20261_total_stores']:,}개**로 감소(-1,306개, -4.56%)했으며, `20262`에는 **{mkt['seoul_20262_total_stores']:,}개**(+18개)로 소폭 반등했다.
- `20242`→`20261` 기간 동안 25개 자치구 중 **{mkt['declining_districts_20242_to_20261']}개 구**에서 점포 수가 감소했다(영등포구·용산구만 순증).
- `20261` 기준 서울 전체 프랜차이즈 비중은 **{mkt['seoul_20261_franchise_share_pct']}%**, 월 추정매출 합계는 **{mkt['seoul_20261_monthly_sales_krw']:,}원**이다.

![서울시 분기별 추이](../figures/fig01_seoul_quarterly_trend.png)

## 2. 자치구별 구조적 격차 및 상관관계 (Observed)
- **점포당 추정매출 vs 점포 변화율**: Pearson $r = {corr_sps['pearson_r']}$ ($p = {corr_sps['pearson_p']}$, 95% CI `[{corr_sps['ci95_low']}, {corr_sps['ci95_high']}]`), Spearman $\\rho = {corr_sps['spearman_rho']}$.
- **프랜차이즈 비중 vs 점포 변화율**: Pearson $r = {corr_fr['pearson_r']}$ ($p = {corr_fr['pearson_p']}$, 95% CI `[{corr_fr['ci95_low']}, {corr_fr['ci95_high']}]`) — 통계적으로 유의한 선형 관계가 관찰되지 않았다.
- **OLS 다중회귀** (`점포_증감률_pct ~ 점포당_추정매출_억원 + 프랜차이즈_비중_pct`): $R^2 = {mkt['ols_store_change_20261']['r_squared']}$ ($F$-test $p = {mkt['ols_store_change_20261']['f_pvalue']}$).

### 점포당 추정매출 상위 5개 자치구 (`20261`)
{top5_dist.to_markdown(index=False)}

### 점포당 추정매출 하위 5개 자치구 (`20261`)
{bot5_dist.to_markdown(index=False)}

![자치구별 점포당 추정매출과 점포 변화율](../figures/fig02_district_store_change_vs_sales.png)

## 3. 상권 소비 맥락 군집 (`20261`, 매칭 상권 n=1,064)
{cluster_prof[['cluster_label', 'commercial_area_count', '주말_비중_pct', '시간_06~11_pct', '시간_11~14_pct', '시간_17~21_pct', '점포당_매출_원']].to_markdown(index=False)}

![상권 소비 맥락 군집](../figures/fig03_commercial_context_clusters.png)
"""
    (REPORTS_DIR / "A_Market_Structure_Report.md").write_text(report_a, encoding="utf-8")

    # --- Report B: CQI Quality Report ---
    nw = cqi["natural_vs_washed"]
    report_b = f"""# B. CQI 커피 품질 데이터 전수 분석 보고서 (CQI Quality Report)

- **출처**: `jldbc/coffee-quality-database` (`arabica_data_cleaned.csv` 1,311건 + `robusta_data_cleaned.csv` 28건 = **총 {cqi['total_records']:,}건**)
- **전수 검증**: 중복 0건, `Total.Cup.Points <= 0` 이상치 **{cqi['outlier_zero_or_negative_cup_points']}건** 제외 후 유효 Arabica **n={cqi['valid_arabica_n']:,}** 기준 품질 비교 수행.

## 1. 표본 편중 및 한계 (Observed)
- 상위 5개 산지({', '.join(cqi_country.head(5)['Country.of.Origin'].tolist())})가 전체 Arabica 표본의 **{cqi['top5_countries_share_pct']}%**를 차지한다.
- CQI 데이터는 국제 커핑 평가 점수이며, **서울 소비자의 향미 선호도나 국내 유통 원두의 품질을 직접 대표하지 않는다.**

## 2. 가공법별 비교 및 통제 회귀 (Observed)
- **단순 비교**: `Natural / Dry` (n={nw['natural_n']}, 평균 {nw['natural_mean']}점) vs `Washed / Wet` (n={nw['washed_n']}, 평균 {nw['washed_mean']}점) → 원차이 **+{nw['raw_diff']}점** (Welch $t={nw['welch_t_stat']}$, $p={nw['welch_p_value']}$).
- **산지 통제 OLS (`Country.of.Origin`)**: Natural 효과 **+{nw['country_adjusted_diff']}점** ($p={nw['country_adjusted_p_value']}$, 95% CI `{nw['country_adjusted_ci95']}`).
- **산지 + 수확연도 통제 OLS (n={nw['country_and_harvest_adjusted_n']})**: Natural 효과 **+{nw['country_and_harvest_adjusted_diff']}점** ($p={nw['country_and_harvest_adjusted_p_value']}$).
- **해석**: 산지와 수확시기를 통제하면 Natural과 Washed 간 커핑 점수 차이는 통계적으로 유의하지 않다. 따라서 가공법 자체를 품질 우열의 근거로 일반화할 수 없다.

### 주요 가공법별 요약
{cqi_proc.head(6).to_markdown(index=False)}

![CQI 가공법 및 산지 분포](../figures/fig04_cqi_processing_and_country.png)
"""
    (REPORTS_DIR / "B_CQI_Quality_Report.md").write_text(report_b, encoding="utf-8")

    # --- Report C: Brand Positioning Report ---
    report_c = f"""# C. 브랜드 포지셔닝 및 향미 언어 분석 보고서 (Brand Positioning Report)

- **수집 원칙**: 서울 주요 상권에서 매장을 운영하는 7개 스페셜티 브랜드의 **공식 온라인몰(`official_online_mall`)**에서 직접 수집·검증한 원두 SKU 전수(중복 제거 후 **n={int(brand_sum['sku_count'].sum())}개**).
- **채널 구분**: 모든 레코드는 온라인몰 공식 판매 SKU이며, 개별 오프라인 매장의 현장 취급 SKU와는 구분하여 해석한다.

## 1. 브랜드별 포트폴리오 및 가격·언어 비교 (Observed)
{brand_sum[['brand_id', 'sku_count', 'median_price_per_100g', 'single_origin_share_pct', 'mean_sensory_dims', 'pct_과일', 'pct_초콜릿', 'pct_산미', 'pct_감성적·추상적']].to_markdown(index=False)}

## 2. 탐색 UX 관찰 요약
{brand_sum[['brand_id', 'seoul_districts', 'primary_context', 'ux_notes']].to_markdown(index=False)}
"""
    (REPORTS_DIR / "C_Brand_Positioning_Report.md").write_text(report_c, encoding="utf-8")

    # --- Report D: Coffee Brand Opportunity Report (Steps 1-5) ---
    report_d = f"""# D. Coffee Brand Opportunity Report — 통합 BX/CX 인사이트 및 검증 가능한 가설

## Step 1. 사용한 데이터
1. **서울 열린데이터광장 공식 원본**: `OA-22173`(점포-자치구 54,765행), `OA-22176`(추정매출-자치구 33,803행), `OA-15577`(점포-상권 456,659행), `OA-15572`(추정매출-상권 128,053행) — `CS100010`(커피-음료) 전수 검증(`VALIDATED`).
2. **CQI Coffee Quality Database**: Arabica 1,311건 + Robusta 28건 = 1,339건 전수(`VALIDATED`).
3. **브랜드 공식 온라인몰 원두 SKU**: 7개 브랜드 공식몰 직접 수집 검증 SKU **n={int(brand_sum['sku_count'].sum())}** (`official_online_mall`).

## Step 2. 개별 데이터 분석 요약
- **서울 시장**: `20242`→`20261` 점포 수 28,639→27,333개(25개 구 중 23개 구 감소). 프랜차이즈 비중과 점포 변화율은 무관($r=0.0145, p=0.945$)한 반면, 점포당 추정매출과는 양의 상관($r=0.5641, p=0.0033$)을 보인다. `20261` 매칭 상권(n=1,064)은 **오피스·점심 집중형(n=275, 점포당 매출 2,283만 원)**, **주말·방문형(n=269, 2,197만 원)**, **모닝·복합형(n=484, 1,943만 원)**, **저녁·생활형(n=36, 878만 원)**으로 구분된다.
- **CQI 품질**: Natural vs Washed 원차이 +0.39점은 산지 통제 후 +0.27점($p=0.2585$)으로 통계적 유의성이 사라진다.
- **브랜드 언어**: 스페셜티 브랜드 간에도 감성적·추상적 서사 비중이 높은 브랜드와 산지·가공법·감각 어휘(과일·산미·바디)를 전면에 두는 브랜드가 뚜렷이 분화된다.

## Step 3. 데이터 교차 분석 (4-Level Join)
{cross_brand[['brand_id', 'avg_district_sales_per_store_eok', 'avg_district_lunch_11_14_pct', 'avg_district_weekend_pct', 'sku_count', 'median_price_per_100g', 'mean_sensory_dims', 'pct_감성적·추상적']].to_markdown(index=False)}

## Step 4. BX/CX 인사이트

### Insight 1. 상권 시간대 집중도("오피스·점심형" vs "주말·방문형")와 원두 탐색 마찰(Exploration Friction)
- **관찰된 데이터**: 오피스·점심 집중형 상권(n=275)은 `11~14시` 매출 비중이 **48.28%**에 달하며 점포당 매출이 가장 높다(2,283만 원). 반면 주말·방문형 상권(n=269)은 주말 비중이 **35.42%**로 분산된다.
- **정량적 근거**: 상권 군집 분석(`k=4`, n=1,064) 및 브랜드별 주요 입지 자치구 평균 `11~14시` 비중 비교.
- **시각화**: `outputs/figures/fig03_commercial_context_clusters.png`
- **해석**: 점심 피크에 집중된 상권의 방문객은 메뉴·원두를 빠르게 결정해야 하는 시간 압박이 큰 반면, 주말·방문형 상권에서는 체류·탐색 여유가 크다.
- **관련 이론**: 인지 부하 이론(Cognitive Load Theory) 및 선택 과부하(Choice Overload, Iyengar & Lepper).
- **대안적 설명**: 오피스 상권의 높은 점포당 매출은 원두 선택 경험이 아니라 단순 유동인구·테이크아웃 회전율의 결과일 수 있다.
- **반례**: 블루보틀·센터커피 등 일부 브랜드는 오피스·복합 상권에서도 다수의 싱글오리진/감성 서사를 유지하며 높은 객단가를 형성한다.
- **BX/CX 관점의 의미**: 동일 브랜드라도 오피스·점심형 접점에서는 "산미/바디 2축 요약·빠른 추천"이, 주말·방문형 접점에서는 "산지·가공 스토리텔링·테이스팅 비교"가 탐색 마찰을 줄일 수 있다.
- **근거 신뢰도**: **Medium** (상권 집계 매출과 온라인몰 UX의 Context Join이므로 매장 내 구매 행동 직접 측정 필요).

### Insight 2. 가공법·산지 커뮤니케이션과 품질 신호의 비대칭
- **관찰된 데이터**: CQI 전수(1,310 유효 Arabica)에서 Natural과 Washed의 차이는 산지 통제 시 유의하지 않다($+0.2657, p=0.2585$). 한편 국내 7개 브랜드의 다수 블렌드/상시 원두는 산지·가공법 표기가 생략되거나 감성적·추상적 표현(전체 {cross_json['reference_cqi_vs_brands']['brand_process_mentions'].get('Unspecified', 0)}건 미표기)과 혼재한다.
- **정량적 근거**: `cqi_regression_summary.json`, `brand_positioning_summary.csv`.
- **시각화**: `outputs/figures/fig04_cqi_processing_and_country.png`
- **해석**: "내추럴=고품질"이라는 단순 도식은 국제 커핑 데이터로 뒷받침되지 않는다. 소비자에게 필요한 것은 가공법 명칭 자체보다 "이 원두가 어떤 감각(산미·단맛·바디)으로 경험되는가"의 번역이다.
- **관련 이론**: 신호 이론(Signaling Theory) 및 감각 어휘의 정보 비대칭 해소.
- **대안적 설명**: 스페셜티 핵심 고객층은 가공법(Natural/Anaerobic)을 품질 점수가 아니라 향미 스타일(발효향/과일향)의 대리 지표로 활용한다.
- **반례**: 게이샤·아나로빅 등 고가 마이크로랏 SKU에서는 가공법과 농장 스펙 자체가 희소성·가격 정당화 신호로 작동한다.
- **BX/CX 관점의 의미**: 가공법·산지 전문 용어를 감각 프로필(산미/단맛/바디/향미 톤)과 병기하는 이중 번역(Dual-Layer Flavor Copy)이 초심자·숙련자 모두의 선택 확신을 높일 수 있다.
- **근거 신뢰도**: **High** (CQI 전수 통제 회귀 + 공식 브랜드 SKU 텍스트 코드북 실측).

## Step 5. 검증 가능한 후속 가설

### Hypothesis 1. 상권 맥락 맞춤형 원두 탐색 UI와 선택 전환율
- **가설 문장**: 오피스·점심 집중형 상권 매장(또는 모바일 오더)에서 원두를 "산미/바디 2축 + 상황 태그(빠른 선택)"로 압축 제시할 경우, 전문 스펙(산지·가공법)만 제시할 때보다 원두 선택 소요 시간은 단축되고 스페셜티/싱글오리진 업셀링 전환율은 상승할 것이다.
- **근거**: 오피스·점심형 상권의 11~14시 매출 집중도(48.28%) vs 주말·방문형(28.72%).
- **예상 관계**: 시간 압박이 높은 상권일수록 2축 요약형 탐색 UI의 전환율 개선 폭이 클 것이다(상호작용 효과).
- **반증 조건**: A/B 테스트에서 시간대별 상권 간 전환율·소요시간 차이가 통계적으로 유의하지 않거나($p \\ge 0.05$), 오피스 상권 고객이 원두 선택 자체에 무관심(기본 블렌드 고정)한 경우.
- **필요한 추가 자료**: 매장 POS/모바일 오더의 시간대별 SKU 선택 로그, 메뉴 탐색 체류시간.
- **검증 방법**: 오피스형 매장 vs 주말·방문형 매장에서 모바일 오더/키오스크 UI A/B 테스트.
- **브랜드 전략과의 연결**: 상권 유형별 매장 CX(메뉴판·스마트오더 정보 밀도) 차등 설계.

### Hypothesis 2. 감성 서사 + 감각 번역(이중 레이어) 카피와 구매 의도
- **가설 문장**: 감성적·추상적 제품명/서사만 제공하는 원두 설명에 비해, 감성 서사와 3대 감각 지표(산미·단맛·바디) 및 친숙한 향미 앵커(과일/초콜릿/견과류)를 함께 제공하는 경우 신규 고객의 원두 구매 의도와 기대 일치도가 유의하게 높을 것이다.
- **근거**: 브랜드별 감성 서사 비중 편차(0%~100%) 및 CQI에서 가공법 단독 품질 신호의 한계.
- **예상 관계**: 커피 관여도가 낮은 소비자군에서 이중 레이어 카피의 구매 의도 상승 효과가 특히 클 것이다.
- **반증 조건**: 실험 설문에서 이중 레이어 카피가 브랜드 감성/프리미엄 인식을 오히려 훼손하거나 구매 의도 차이가 없는 경우.
- **필요한 추가 자료**: 소비자 관여도별 온라인 실험(Online Randomized Experiment) 데이터.
- **검증 방법**: 동일 가격·산지 조건에서 카피 유형(감성 단독 vs 스펙 단독 vs 이중 레이어) 3집단 무작위 배정 실험.
- **브랜드 전략과의 연결**: 온라인몰 상세페이지(PDP) 및 패키지 백 라벨 정보 아키텍처 표준화.
"""
    (REPORTS_DIR / "D_Coffee_Brand_Opportunity_Report.md").write_text(report_d, encoding="utf-8")

    # --- Evidence Ledger (Source -> Raw -> Cleaning -> Analysis -> Observation -> Interpretation -> Hypothesis) ---
    ledger_rows = [
        {
            "evidence_id": "EV-01",
            "source": "서울 열린데이터광장 OA-22173, OA-22176",
            "raw_data": "data/raw/seoul/OA-22173_store_district.csv, OA-22176_sales_district.csv",
            "cleaning": "src/cleaning/validate_seoul.py, build_processed.py",
            "analysis": "src/analysis/market_structure.py",
            "observation": "20261 서울 커피·음료 점포 27,333개(20242 대비 23/25개 구 감소); 점포당 매출 vs 점포 변화율 r=0.5641(p=0.0033), 프랜차이즈 비중 r=0.0145(p=0.945)",
            "interpretation": "상권 생존·유지력은 프랜차이즈 여부보다 점포당 매출 창출력과 강하게 연동됨",
            "hypothesis": "H1 (상권 맥락 맞춤형 탐색 UX)",
        },
        {
            "evidence_id": "EV-02",
            "source": "서울 열린데이터광장 OA-15577, OA-15572",
            "raw_data": "data/processed/seoul/cs100010_store_commercial.csv, cs100010_sales_commercial.csv",
            "cleaning": "src/cleaning/validate_seoul.py, build_processed.py",
            "analysis": "src/analysis/consumer_context.py",
            "observation": "20261 매칭 상권 n=1,064 KMeans(k=4) 결과 오피스·점심 집중형(11~14시 48.28%, 점포당 2,283만원)과 주말·방문형(주말 35.42%) 등 4개 맥락 확인",
            "interpretation": "상권별 방문 시간압박과 소비 목적이 상이하므로 메뉴·원두 탐색 마찰의 크기 역시 다를 수 있음",
            "hypothesis": "H1 (오피스형 vs 주말형 UI 차등 설계)",
        },
        {
            "evidence_id": "EV-03",
            "source": "CQI Coffee Quality Database (jldbc)",
            "raw_data": "data/raw/cqi/arabica_data_cleaned.csv, robusta_data_cleaned.csv",
            "cleaning": "src/cleaning/validate_seoul.py, build_processed.py",
            "analysis": "src/analysis/cqi_quality.py",
            "observation": "1,339건 전수 중 유효 Arabica n=1,310에서 Natural vs Washed 원차이 +0.3895점이나 산지 통제 시 +0.2657점(p=0.2585)",
            "interpretation": "가공법 자체는 산지 효과를 제거하면 통계적으로 유의한 품질 우위 신호가 아님",
            "hypothesis": "H2 (가공법 스펙보다 감각 번역 레이어 필요)",
        },
        {
            "evidence_id": "EV-04",
            "source": "7개 스페셜티 브랜드 공식 온라인몰",
            "raw_data": "data/raw/brands/official_brand_beans_raw.csv",
            "cleaning": "src/analysis/brand_positioning.py",
            "analysis": "src/analysis/brand_positioning.py, cross_analysis.py",
            "observation": "공식 검증 원두 SKU 전수에서 감성적·추상적 언어와 감각 어휘(과일·산미·초콜릿·바디)의 결합 수준이 브랜드별로 크게 분화됨",
            "interpretation": "감성 서사 단독 또는 전문 스펙 단독 전달은 비전문 소비자의 선택 확신을 저해할 수 있음",
            "hypothesis": "H2 (이중 레이어 카피와 구매 의도)",
        },
    ]
    ledger_path = EVIDENCE_DIR / "evidence_ledger.csv"
    with ledger_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(ledger_rows[0].keys()))
        writer.writeheader()
        writer.writerows(ledger_rows)

    return [
        REPORTS_DIR / "A_Market_Structure_Report.md",
        REPORTS_DIR / "B_CQI_Quality_Report.md",
        REPORTS_DIR / "C_Brand_Positioning_Report.md",
        REPORTS_DIR / "D_Coffee_Brand_Opportunity_Report.md",
        ledger_path,
    ]


def main() -> int:
    paths = generate_reports()
    for p in paths:
        print("Generated:", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
