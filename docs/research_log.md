# Research Log — CoffeeGraph (Coffee Brand Opportunity Map)

## 2026-11-17 — Milestone 1 & 2: Repository Setup, Official Data Acquisition & Validation

- **Repository**: `CHO-YOUN-SIK/CoffeeGraph` (Private, `main`)
- **Python Environment**: Python 3.11.2, `uv` + `requirements.lock`
- **Status**:
  - `M1. Official Data Acquisition`: **COMPLETED**
  - `M2. Data Validation`: **VALIDATED**

### Official Datasets Acquired & Verified
1. **서울시 상권분석서비스(점포-자치구)** (`OA-22173`):
   - Rows: 54,765 | Cols: 12 | `CS100010` (커피-음료): 550 rows (25 districts × 22 quarters, `20211`~`20262`)
   - Duplicate keys: 0 | Store sum diff (`전체 - (일반 + 프랜차이즈)`): 0.0 | Missing rate: 0.0%
2. **서울시 상권분석서비스(추정매출-자치구)** (`OA-22176`):
   - Rows: 33,803 | Cols: 53 | `CS100010` (커피-음료): 550 rows (25 districts × 22 quarters, `20211`~`20262`)
   - Duplicate keys: 0 | Weekday+Weekend / 7-day / 6-timeslot rel diff: 0.0 | Missing rate: 0.0%
3. **서울시 상권분석서비스(점포-상권)** (`OA-15577`):
   - Rows: 456,659 | Cols: 14 | `CS100010`: 9,119 rows (1,535 unique commercial areas, `20251`~`20262`)
   - Observed note: Official portal provides `20251`~`20262` (6 quarters) for commercial-area tables, and spatial unit counts vary slightly by quarter (`20251`: 1,525 → `20261`: 1,519).
4. **서울시 상권분석서비스(추정매출-상권)** (`OA-15572`):
   - Rows: 128,053 | Cols: 55 | `CS100010`: 6,424 rows (1,107 unique commercial areas, `20251`~`20262`)
5. **CQI Coffee Quality Database** (`jldbc/coffee-quality-database`):
   - `arabica_data_cleaned.csv`: 1,311 rows, 44 cols (1 row with `Total.Cup.Points <= 0` flagged for Phase 4 handling)
   - `robusta_data_cleaned.csv`: 28 rows, 44 cols

### Next Steps
- **M3. Seoul Market Analysis**: Implement `src/analysis/market_structure.py` and `src/analysis/consumer_context.py`, verify/re-evaluate prior findings (`27,333` stores, `23/25` districts declining, correlations) against the official `20242`~`20262` data.
- **M4. CQI Analysis**: Implement `src/analysis/cqi_quality.py` to analyze full 1,339 records.
