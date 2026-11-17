# CoffeeGraph — Coffee Brand Opportunity Map

GitHub Cloud 기반 데이터 리서치 & BX/CX 전략 분석 프로젝트

## 1. 프로젝트 개요
서울 커피 시장(`CS100010`, 커피-음료)의 점포·매출·경쟁 구조와 소비 맥락, 글로벌 CQI 커핑 품질 데이터, 브랜드 원두 향미 커뮤니케이션을 정량·정성 데이터로 분석하여 기존 브랜드의 BX/CX 전략적 기회를 탐색하는 재현 가능한 연구 저장소입니다.

## 2. 현재 진행 상태 (Milestone Status)

| Phase / Milestone | 상태 | 근거 및 산출물 |
|---|---|---|
| M1. Official Data Acquisition | **COMPLETED** | 서울시 공식 데이터 4종(`OA-22173`, `OA-22176`, `OA-15577`, `OA-15572`) + CQI 2종(`Arabica`, `Robusta`) 원본 수집 완료 (`data/metadata/source_registry.csv`, `collection_log.csv`) |
| M2. Data Validation | **VALIDATED** | 전수 스키마·결측·중복·산술 정합성 검증 통과 (`data/metadata/validation_results.json`, `tests/test_data_validation.py`) |
| M3. Seoul Market Analysis | **NOT_STARTED** | 다음 단계 진행 예정 (`src/analysis/market_structure.py`) |
| M4. CQI Analysis | **NOT_STARTED** | `src/analysis/cqi_quality.py` |
| M5. Brand Research | **NOT_STARTED** | `src/collectors/brand_collector.py` |
| M6. Cross Analysis | **NOT_STARTED** | `src/analysis/cross_analysis.py` |
| M7. Insights & Hypotheses | **NOT_STARTED** | `research/insights/`, `research/hypotheses/` |
| M8. Final Report | **NOT_STARTED** | `outputs/reports/` |

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
