# CoffeeGraph — Coffee Flavor Language Map & Opportunity Research

GitHub Cloud 기반 데이터 리서치 & 커피 향미 언어 시각화 문법 연구 프로젝트

## 1. 프로젝트 개요
- **핵심 연구 질문**: *"브랜드별 원두 설명에 나타나는 향미 언어의 차이는 무엇이며, 이를 일관된 시각적 문법으로 변환할 수 있는가?"*
- **3계층 엄격 분리**:
  1. **Observed**: 8개 브랜드 공식 온라인몰 **129개 원두 SKU** 설명문 내 어휘 출현·공출현 관찰
  2. **Analytical Taxonomy**: SCA/WCR Sensory Lexicon 기반 `flavor_family`, `sensory_specificity`, `narrative_density` 코딩 (`src/analysis/flavor_language.py`)
  3. **Visual Encoding**: **Visualization A (Brand Language Landscape)** & **Visualization B (Flavor Language Fingerprint)** (`src/visualization/flavor_language_map.py`, `outputs/reports/Coffee_Flavor_Language_Report.md`)
- **연구 배경·참조**: 서울시 공공 상권 데이터(`CS100010`) 및 글로벌 CQI(1,339건)는 시장·감각 체계 참조 배경으로 유지하며, 브랜드 SKU의 품질·매출 변수로 억지 결합하지 않습니다.

## 2. 현재 진행 상태 (Milestone Status)

| Phase / Milestone | 상태 | 근거 및 산출물 |
|---|---|---|
| M1. Official Data Acquisition | **COMPLETED** | 서울시 공식 데이터 4종(`OA-22173`, `OA-22176`, `OA-15577`, `OA-15572`) + CQI 2종(`Arabica`, `Robusta`) 원본 수집 완료 (`data/metadata/source_registry.csv`, `collection_log.csv`) |
| M2. Data Validation | **VALIDATED** | 전수 스키마·결측·중복·산술 정합성 검증 통과 (`data/metadata/validation_results.json`, `tests/test_data_validation.py`) |
| M3. Seoul Market Analysis (Background) | **COMPLETED** | 자치구(25개)·상권(1,064개 매칭) 시장 구조·소비 맥락·군집 분석 및 기존 지표 재현 검증 완료 (`src/analysis/market_structure.py`, `consumer_context.py`) |
| M4. CQI Analysis (Reference) | **COMPLETED** | CQI 1,339건 전수 분석, 산지·수확시기 통제 OLS 및 표본 편향 진단 완료 (`src/analysis/cqi_quality.py`) |
| M5. Brand Flavor Language Analysis | **COMPLETED** | 8개 브랜드 공식몰 129 SKU 수집·SCA/WCR 기반 향미 언어 분석 (`src/collectors/brand_collector.py`, `src/analysis/flavor_language.py`) |
| M6. Visual Grammar & Maps | **COMPLETED** | Brand Language Landscape & Flavor Language Fingerprint 생성 (`outputs/figures/coffee_flavor_language_map.html`, `fig05_flavor_language_map.png`) |
| M7. Flavor Language Report & Validation | **COMPLETED** | 핵심 보고서(`outputs/reports/Coffee_Flavor_Language_Report.md`) 및 한국 소비자 색–향미 매칭 실험 프로토콜 설계 |
| M8. Background Reports (A~D) | **COMPLETED** | 배경 시장·CQI·교차 분석 보고서(`outputs/reports/A~D`) 및 근거 추적표(`research/evidence/evidence_ledger.csv`) |

## 3. 수집 및 검증된 공식 데이터 현황

| Dataset Key | ID | 전체 행수 | 열수 | `CS100010` 행수 | 제공 기간 | 상태 |
|---|---|---:|---:|---:|---|---|
| `seoul_store_district` | `OA-22173` | 54,765 | 12 | 550 (25개 구 × 22분기) | `20211` ~ `20262` | `VALIDATED` |
| `seoul_sales_district` | `OA-22176` | 33,803 | 53 | 550 (25개 구 × 22분기) | `20211` ~ `20262` | `VALIDATED` |
| `seoul_store_commercial` | `OA-15577` | 456,659 | 14 | 9,119 (1,535개 상권) | `20251` ~ `20262` | `VALIDATED` |
| `seoul_sales_commercial` | `OA-15572` | 128,053 | 55 | 6,424 (1,107개 상권) | `20251` ~ `20262` | `VALIDATED` |
| `cqi_arabica` | `CQI-ARABICA` | 1,311 | 44 | - | - | `VALIDATED` |
| `cqi_robusta` | `CQI-ROBUSTA` | 28 | 44 | - | - | `VALIDATED` |

> **참고**: `OA-15577` 및 `OA-15572` 원본 파일은 각각 44MB, 57MB로 대용량이므로 `.gitignore`에서 제외되며, `CS100010` 필터링 정제본(`data/processed/seoul/cs100010_*.csv`)이 저장소에 포함됩니다. 전체 원본은 `collect_seoul.yml` 또는 `python -m src.collectors.seoul_open_data`로 언제든 재수집할 수 있습니다.

## 4. 로컬 실행 방법

```bash
uv venv
uv pip install -e ".[dev]"
.venv/bin/python -m src.cleaning.validate_seoul
.venv/bin/pytest -v
```
