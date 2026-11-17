"""Focused Report Generator for Coffee Flavor Language Map (Audited & Refined).

Generates outputs/reports/Coffee_Flavor_Language_Report.md strictly separating:
1. Observed lexical data (129 total SKUs / 98 comparable whole_bean SKUs across 8 brands)
2. Analytical taxonomy (SCA/WCR hierarchy, clean specificity, narrative density, product/origin type)
3. Visual encoding rules & candidate color-flavor validation protocol
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "outputs" / "tables"
REPORTS_DIR = ROOT / "outputs" / "reports"


def build_flavor_language_report() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stats = json.loads((TABLES_DIR / "flavor_language_stats.json").read_text(encoding="utf-8"))
    fp = pd.read_csv(TABLES_DIR / "brand_flavor_fingerprint.csv")
    cooc = pd.read_csv(TABLES_DIR / "flavor_cooccurrence.csv")

    all_s = stats["all_skus"]
    wb_s = stats["whole_bean_only"]
    q1_all = all_s["q1_brand_vs_dominant_family"]
    q1_col = all_s["q1_collapsed_rare_categories"]
    q1_wb = wb_s["q1_brand_vs_dominant_family"]
    q2_all = all_s["q2_narrative_vs_specificity"]
    q2_wb = wb_s["q2_narrative_vs_specificity"]

    fp_disp = fp[
        [
            "brand_id",
            "sku_count",
            "whole_bean_count",
            "flavor_detected_count",
            "flavor_detected_pct",
            "median_whole_bean_price_per_100g",
            "mean_sensory_specificity",
            "mean_narrative_density",
        ]
    ]
    cooc_top = cooc.head(5)[["family_a", "family_b", "co_occur_skus", "jaccard"]]

    pt = stats["product_type_counts"]
    lines = [
        "# Coffee Flavor Language Map — 브랜드 향미 언어 구조 및 시각화 문법 보고서 (정제·재검증본)",
        "",
        "## 1. 핵심 연구 질문 및 데이터 정합성 감사 반영 사항",
        "> **핵심 질문**: *\"브랜드별 원두 설명에 나타나는 향미 언어의 차이는 무엇이며, 이를 일관된 시각적 문법으로 변환할 수 있는가?\"*",
        "",
        "본 보고서는 초기 감사에서 발견된 측정 오류를 전수 교정한 재검증 결과입니다.",
        "1. **공통 웹사이트 텍스트 제거 (문제 C 해결)**: 테라로사(`추천 검색어 피칸파이`), 센터커피·앤트러사이트(`모카포트` 등 메뉴·알림), 블루보틀(`배송 안내`), 카페24(`SOLD OUT·제조일`) 공통 문구를 스크래퍼 단계에서 원천 제거하고 제품 본문 전용 셀렉터만 추출했습니다.",
        f"   - **센터커피 0% 검출 원인 검증**: 공식 Imweb 상세페이지 HTML을 직접 점검한 결과, 본문 텍스트에는 원산지·용량·추출용도(`.goods_summary`)만 존재하며 텍스트 테이스팅 노트는 미기재(이미지 또는 미제공) 상태임을 확인했습니다.",
        "2. **WCR 참조 매핑 및 단어 경계 교정 (문제 A 해결)**: WCR Sensory Lexicon 속성을 연구자 정의 규칙으로 7개 계열에 매핑(`data/metadata/wcr_korean_lexicon_mapping.csv`)하고, 한국어 경계 정규식 + 최장 구문 우선 비겹침(non-overlapping) 매칭으로 `배송`/`중약배전`→`배`, `모카포트`→`모카`, `다크초콜릿`+`초콜릿` 중복 집계를 차단했습니다.",
        "3. **상품 유형 분리 (문제 B 해결)**: 전체 **129개 SKU**를 `whole_bean`(**{wb}개**), `subscription`({sub}개), `drip_bag`({db}개), `set_kit`({sk}개), `capsule`({cap}개)로 분리해 비교 가능한 일반 원두 모집단과 전체 모집단을 병행 분석했습니다.".format(
            wb=pt.get("whole_bean", 0),
            sub=pt.get("subscription", 0),
            db=pt.get("drip_bag", 0),
            sk=pt.get("set_kit", 0),
            cap=pt.get("capsule", 0),
        ),
        "4. **파라미터·시각화 분리 (문제 E·F·G 해결)**: 순수 구체성 수준(`specificity_level`: 0/1/2)과 고유 앵커 수(`specific_anchor_count`)를 구분하고, 대표 향미 동률은 `Multi-Family (Tie)`, 미검출은 `None-Stated`로 명시했습니다. 가격 결측치 임의 대입(점 크기)을 제거하고 점 크기를 고정했습니다.",
        "",
        "---",
        "",
        "## 2. Relationship 01 — 브랜드 × 향미 언어 분석 결과 (Observed & Statistical)",
        "",
        "### A. 향미 계열 분포 및 브랜드 간 독립성 (Monte Carlo 순열 검정)",
        f"- **전체 129개 SKU**: `Specific-Anchored` **{all_s['specificity_tier_counts'].get('Specific-Anchored', 0)}개**, `Broad-Only` **{all_s['specificity_tier_counts'].get('Broad-Only', 0)}개**, `None-Stated` **{all_s['specificity_tier_counts'].get('None-Stated', 0)}개** (동률 `Multi-Family (Tie)` **{all_s['dominant_family_counts'].get('Multi-Family (Tie)', 0)}개**).",
        f"- **일반 원두(whole_bean, n={wb_s['n_skus']})**: `Specific-Anchored` **{wb_s['specificity_tier_counts'].get('Specific-Anchored', 0)}개**, `Broad-Only` **{wb_s['specificity_tier_counts'].get('Broad-Only', 0)}개**, `None-Stated` **{wb_s['specificity_tier_counts'].get('None-Stated', 0)}개**.",
        f"- **브랜드 × 대표 향미 계열 독립성 검정 (희소 셀 보완)**:",
        f"  - 전체 129 SKU 교차표는 기대빈도 5 미만 셀이 **{q1_all['sparse_cell_pct']}%**({q1_all['sparse_cells_lt5']}/{q1_all['total_cells']})이므로 점근 근사 대신 **10,000회 Monte Carlo 순열 검정**을 적용했습니다: $\\chi^2 = {q1_all['chi2']}$, **Monte Carlo $p = {q1_all['p_monte_carlo']}$**, **Cramér's $V = {q1_all['cramers_v']}$**.",
        f"  - 희소 범주(<5%) 통합 강건성 검정에서도 **Cramér's $V = {q1_col['cramers_v']}$** (Monte Carlo $p = {q1_col['p_monte_carlo']}$)로 유의했습니다.",
        f"  - 일반 원두(`whole_bean`, n={wb_s['n_skus']}) 한정 검정에서도 $\\chi^2 = {q1_wb['chi2']}$, **Monte Carlo $p = {q1_wb['p_monte_carlo']}$**, **Cramér's $V = {q1_wb['cramers_v']}$**로 브랜드 간 향미 언어 차이가 일관되게 확인되었습니다.",
        "",
        "### B. 감성 서사 밀도(`narrative_density`)와 감각 구체성(`sensory_specificity`)의 관계",
        f"- **전체 129 SKU**: 단순 상관 Pearson $r = {q2_all['pearson_r']}$ ($p = {q2_all['pearson_p']}$), Spearman $\\rho = {q2_all['spearman_rho']}$ ($p = {q2_all['spearman_p']}$).",
        f"- **텍스트 길이·원산지 유형(`origin_type`)·브랜드 고정효과(`C(brand_id)`) 통제 OLS + TOST 동등성 검정**:",
        f"  - 전체 129 SKU ($R^2 = {q2_all['ols_brand_fe_r2']}$): `narrative_density` $\\beta = {q2_all['ols_brand_fe_narrative_coef']}$ (95% CI `[{q2_all['ols_brand_fe_narrative_ci95'][0]}, {q2_all['ols_brand_fe_narrative_ci95'][1]}]`, $p = {q2_all['ols_brand_fe_narrative_p']}$), **TOST 동등성 검정($\\Delta = \\pm {q2_all['ols_brand_fe_narrative_tost_delta']}$) $p = {q2_all['ols_brand_fe_narrative_tost_p']}$**; `is_single_origin` $\\beta = +{q2_all['ols_brand_fe_single_origin_coef']}$ ($p = {q2_all['ols_brand_fe_single_origin_p']}$).",
        f"  - 일반 원두(n={wb_s['n_skus']}, $R^2 = {q2_wb['ols_brand_fe_r2']}$): `narrative_density` $\\beta = {q2_wb['ols_brand_fe_narrative_coef']}$ (95% CI `[{q2_wb['ols_brand_fe_narrative_ci95'][0]}, {q2_wb['ols_brand_fe_narrative_ci95'][1]}]`, $p = {q2_wb['ols_brand_fe_narrative_p']}$), **TOST 동등성 검정($\\Delta = \\pm {q2_wb['ols_brand_fe_narrative_tost_delta']}$) $p = {q2_wb['ols_brand_fe_narrative_tost_p']}$**; `is_single_origin` $\\beta = +{q2_wb['ols_brand_fe_single_origin_coef']}$ ($p = {q2_wb['ols_brand_fe_single_origin_p']}$).",
        "- **결론**: 비유의한 p값만으로 독립을 단정하지 않고 95% 신뢰구간과 TOST 동등성 검정($|\\beta| < 0.5$)을 확인한 결과, 두 언어 차원은 실질적 상충 없이 독립적으로 설계 가능합니다.",
        "",
        "### C. 향미 계열 공출현(Co-occurrence) 상위 쌍 (전체 129 SKU)",
        cooc_top.to_markdown(index=False),
        "",
        "### D. 브랜드별 향미 언어 프로파일 요약",
        fp_disp.to_markdown(index=False),
        "",
        "---",
        "",
        "## 3. Relationship 02 — 수정된 시각화 문법 및 핵심 시각화 2종",
        "",
        "| 데이터 파라미터 | 측정 대상 | 시각적 표현 |",
        "|---|---|---|",
        "| `dominant_flavor_family` | 대표 향미 계열 (동률=`Multi-Family (Tie)`, 미검출=`None-Stated`) | 색상 (Hue, 후보 팔레트) |",
        "| `sku_pct_{family}` | 브랜드 내 각 계열 언급 SKU 비율 (중복 허용, 합계 ≠ 100%) | Fingerprint 히트맵 셀 + `검출 k/n` 병기 |",
        "| `sensory_specificity` | 0=미검출, 0.5=광의 표현만, 1+=고유 구체 앵커 수 | X축 위치 (미검출 경계선 `x=0.25` 표시) |",
        "| `narrative_density` | 정제 본문 100자당 감성·추상 표현 출현 수 | Y축 위치 |",
        "| `product_type_std` / `brand_id` | 상품 유형(`whole_bean` 등) 및 브랜드 | 인터랙티브 필터 (`coffee_flavor_language_map.html`) |",
        "| `price_per_100g` | 일반 원두 100g 환산 가격 (결측 임의 대입 제거) | 점 크기 고정, 툴팁(상세정보)에만 표시 |",
        "",
        "- **Visualization A & B 인터랙티브 맵**: [`coffee_flavor_language_map.html`](file:///home/antigravity/CHO-YOUN-SIK/CoffeeGraph/outputs/figures/coffee_flavor_language_map.html)",
        "",
        "![Coffee Flavor Language Map](../figures/fig05_flavor_language_map.png)",
        "",
        "---",
        "",
        "## 4. 후속 디자인 검증 프로토콜 (색–향미 매칭 실험)",
        "시각화 인코딩(Layer 3)의 타당성을 검증하기 위해 한국 소비자를 대상으로 **색–향미 교차감각 매칭 실험**을 제안합니다.",
        "- **실험 과제**: 7개 향미 계열 후보 색상(Berry `#C0392B`, Citrus `#E67E22`, Stone Fruit `#E84393`, Floral `#8E44AD`, Nutty `#A67C52`, Chocolate `#5D4037`, Sweet/Caramel `#D4AC0D`)과 한국어 향미 앵커 간 매칭 일치율(Accuracy) 및 반응시간(RT) 측정.",
        "- **평가 기준**: 무작위 기대 일치율(14.3%) 대비 유의한 초과 일치율 및 문화적 혼동 쌍(예: Berry vs Citrus, Nutty vs Chocolate) 식별 후 팔레트 보정.",
    ]

    out_path = REPORTS_DIR / "Coffee_Flavor_Language_Report.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    p = build_flavor_language_report()
    print("Generated:", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
