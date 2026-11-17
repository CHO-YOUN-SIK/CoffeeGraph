# Research Methodology — CoffeeGraph

## 1. Core Principles
- **Source-First**: 모든 정량 분석은 공식 원본 데이터(`data/raw/`)에서 출발하며, SHA-256 체크섬과 수집 로그(`data/metadata/collection_log.csv`)를 남긴다.
- **Full-Dataset Analysis**: 샘플 추정을 금지하고 확보된 전체 행(서울시 `CS100010` 전수, CQI 1,339건 전수, 공식 브랜드 온라인몰 검증 SKU 전수)을 분석한다.
- **Evidence Traceability**: 모든 인사이트는 `Source → Raw Data → Cleaning → Analysis → Observation → Interpretation → Hypothesis` 경로로 추적 가능해야 한다.
- **Research Integrity**:
  - **Observed**: 데이터에서 직접 확인된 사실
  - **Interpretation**: 관찰된 사실에 대한 가능한 설명
  - **Hypothesis**: 아직 검증되지 않았으나 반증 가능한 가설
  - **Unknown**: 추가 데이터가 필요한 영역
  - 상관관계를 인과관계로 주장하지 않으며, 상권 집계 매출을 개별 소비자의 구매 동기로 단정하지 않는다.
  - CQI 커핑 점수를 국내 판매 원두의 품질이나 서울 소비자의 향미 선호로 대체하지 않는다.

## 2. Four-Level Join Architecture
1. **Direct Join**: 서울시 점포(`OA-22173`), 추정매출(`OA-22176`), 상권(`OA-15577`, `OA-15572`)을 동일 기준분기(`기준_년분기_코드`)·공간(`자치구_코드`/`상권_코드`)·업종(`CS100010`) 키로 직접 결합한다.
2. **Context Join**: 브랜드의 서울 주요 매장 소재 자치구·상권 맥락을 시장 구조 지표와 연결한다.
3. **Comparative Analysis**: 공식 웹사이트에서 확인된 원두 SKU·가격·향미 언어(9차원 코드북)를 브랜드 간·상권 맥락 간 비교한다.
4. **Reference Analysis**: CQI 국제 커핑 데이터(1,339건)를 산지·가공법별 배경 참고 자료로만 활용하며 개별 브랜드 제품 점수로 직접 결합하지 않는다.
