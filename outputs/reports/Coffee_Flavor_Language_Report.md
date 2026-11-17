# Coffee Flavor Language Map — 브랜드 향미 언어 구조 및 시각화 문법 보고서 (정제·재검증본)

## 1. 핵심 연구 질문 및 데이터 정합성 감사 반영 사항
> **핵심 질문**: *"브랜드별 원두 설명에 나타나는 향미 언어의 차이는 무엇이며, 이를 일관된 시각적 문법으로 변환할 수 있는가?"*

본 보고서는 초기 감사에서 발견된 측정 오류를 전수 교정한 재검증 결과입니다.
1. **공통 웹사이트 텍스트 제거 (문제 C 해결)**: 테라로사(`추천 검색어 피칸파이`), 센터커피·앤트러사이트(`모카포트` 등 메뉴·알림), 블루보틀(`배송 안내`), 카페24(`SOLD OUT·제조일`) 공통 문구를 스크래퍼 단계에서 원천 제거하고 제품 본문 전용 셀렉터만 추출했습니다.
2. **단어 경계 및 중복 매칭 교정 (문제 A 해결)**: 한국어 정규식 경계 가드를 도입해 `배송`/`중약배전`→`배`, `모카포트`→`모카` 오인식을 차단하고, 최장 구문 우선 비겹침(non-overlapping) 매칭으로 `다크초콜릿`+`초콜릿` 중복 집계를 제거했습니다.
3. **상품 유형 분리 (문제 B 해결)**: 전체 **129개 SKU**를 `whole_bean`(**98개**), `subscription`(12개), `drip_bag`(9개), `set_kit`(5개), `capsule`(5개)로 분리해 비교 가능한 일반 원두 모집단과 전체 모집단을 병행 분석했습니다.
4. **파라미터·시각화 분리 (문제 E·F·G 해결)**: `sensory_specificity`(0=미검출, 0.5=광의, 1+=고유 구체 앵커 수)를 단순 어휘량과 분리했고, 대표 향미 동률은 `Multi-Family (Tie)`, 미검출은 `None-Stated`로 명시했습니다. 가격 결측치 임의 대입(점 크기)을 제거하고 점 크기를 고정했습니다.

---

## 2. Relationship 01 — 브랜드 × 향미 언어 분석 결과 (Observed & Statistical)

### A. 향미 계열 분포 및 브랜드 간 독립성 (Monte Carlo 순열 검정)
- **전체 129개 SKU**: `Specific-Anchored` **48개**, `Broad-Only` **18개**, `None-Stated` **63개** (동률 `Multi-Family (Tie)` **28개**).
- **일반 원두(whole_bean, n=98)**: `Specific-Anchored` **45개**, `Broad-Only` **15개**, `None-Stated` **38개**.
- **브랜드 × 대표 향미 계열 독립성 검정 (희소 셀 보완)**:
  - 전체 129 SKU 교차표는 기대빈도 5 미만 셀이 **89.3%**(50/56)이므로 점근 근사 대신 **10,000회 Monte Carlo 순열 검정**을 적용했습니다: $\chi^2 = 104.582$, **Monte Carlo $p = 0.0001$**, **Cramér's $V = 0.3676$**.
  - 희소 범주(<5%) 통합 강건성 검정에서도 **Cramér's $V = 0.419$** (Monte Carlo $p = 0.0001$)로 유의했습니다.
  - 일반 원두(`whole_bean`, n=98) 한정 검정에서도 $\chi^2 = 87.793$, **Monte Carlo $p = 0.0002$**, **Cramér's $V = 0.3864$**로 브랜드 간 향미 언어 차이가 일관되게 확인되었습니다.

### B. 감성 서사 밀도(`narrative_density`)와 감각 구체성(`sensory_specificity`)의 관계
- **전체 129 SKU**: 단순 상관 Pearson $r = -0.0193$ ($p = 0.828013$), Spearman $\rho = 0.1459$ ($p = 0.099062$).
- **텍스트 길이·원산지 유형(`origin_type`)·브랜드 고정효과(`C(brand_id)`) 통제 OLS**:
  - 전체 129 SKU ($R^2 = 0.4963$): `narrative_density` $\beta = 0.0529$ ($p = 0.742811$, **비유의**), `is_single_origin` $\beta = +1.2216$ ($p = 0.0$).
  - 일반 원두(n=98, $R^2 = 0.4913$): `narrative_density` $\beta = 0.0124$ ($p = 0.955767$, **비유의**), `is_single_origin` $\beta = +1.1521$ ($p = 1.8e-05$).
- **결론**: 브랜드 차이와 텍스트 길이를 통제해도 감성 서사 밀도와 감각 구체성은 서로 배타적이지 않으며 독립적으로 설계할 수 있습니다.

### C. 향미 계열 공출현(Co-occurrence) 상위 쌍 (전체 129 SKU)
| family_a          | family_b        |   co_occur_skus |   jaccard |
|:------------------|:----------------|----------------:|----------:|
| Stone/Other Fruit | Sweet/Caramel   |              20 |     0.377 |
| Stone/Other Fruit | Chocolate/Cocoa |              14 |     0.269 |
| Stone/Other Fruit | Floral          |              12 |     0.25  |
| Chocolate/Cocoa   | Sweet/Caramel   |              11 |     0.25  |
| Floral            | Sweet/Caramel   |              10 |     0.256 |

### D. 브랜드별 향미 언어 프로파일 요약
| brand_id       |   sku_count |   whole_bean_count |   flavor_detected_count |   flavor_detected_pct |   median_whole_bean_price_per_100g |   mean_sensory_specificity |   mean_narrative_density |
|:---------------|------------:|-------------------:|------------------------:|----------------------:|-----------------------------------:|---------------------------:|-------------------------:|
| felt_coffee    |          22 |                 19 |                      20 |                  90.9 |                              12500 |                       2.27 |                    0.193 |
| fritz          |          10 |                 10 |                       8 |                  80   |                               9000 |                       1.15 |                    0.306 |
| blue_bottle_kr |          12 |                 10 |                      11 |                  91.7 |                              12750 |                       1    |                    0.946 |
| terarosa       |           9 |                  6 |                       7 |                  77.8 |                              10600 |                       0.89 |                    0.511 |
| coffee_libre   |          32 |                 20 |                       9 |                  28.1 |                               8500 |                       0.7  |                    0     |
| anthracite     |          17 |                 16 |                       9 |                  52.9 |                               8500 |                       0.47 |                    0.203 |
| paul_bassett   |          20 |                 10 |                       2 |                  10   |                                nan |                       0.05 |                    0.413 |
| center_coffee  |           7 |                  7 |                       0 |                   0   |                              12381 |                       0    |                    0     |

---

## 3. Relationship 02 — 수정된 시각화 문법 및 핵심 시각화 2종

| 데이터 파라미터 | 측정 대상 | 시각적 표현 |
|---|---|---|
| `dominant_flavor_family` | 대표 향미 계열 (동률=`Multi-Family (Tie)`, 미검출=`None-Stated`) | 색상 (Hue, 후보 팔레트) |
| `sku_pct_{family}` | 브랜드 내 각 계열 언급 SKU 비율 (중복 허용, 합계 ≠ 100%) | Fingerprint 히트맵 셀 + `검출 k/n` 병기 |
| `sensory_specificity` | 0=미검출, 0.5=광의 표현만, 1+=고유 구체 앵커 수 | X축 위치 (미검출 경계선 `x=0.25` 표시) |
| `narrative_density` | 정제 본문 100자당 감성·추상 표현 출현 수 | Y축 위치 |
| `product_type_std` / `brand_id` | 상품 유형(`whole_bean` 등) 및 브랜드 | 인터랙티브 필터 (`coffee_flavor_language_map.html`) |
| `price_per_100g` | 일반 원두 100g 환산 가격 (결측 임의 대입 제거) | 점 크기 고정, 툴팁(상세정보)에만 표시 |

- **Visualization A & B 인터랙티브 맵**: [`coffee_flavor_language_map.html`](file:///home/antigravity/CHO-YOUN-SIK/CoffeeGraph/outputs/figures/coffee_flavor_language_map.html)

![Coffee Flavor Language Map](../figures/fig05_flavor_language_map.png)

---

## 4. 후속 디자인 검증 프로토콜 (색–향미 매칭 실험)
시각화 인코딩(Layer 3)의 타당성을 검증하기 위해 한국 소비자를 대상으로 **색–향미 교차감각 매칭 실험**을 제안합니다.
- **실험 과제**: 7개 향미 계열 후보 색상(Berry `#C0392B`, Citrus `#E67E22`, Stone Fruit `#E84393`, Floral `#8E44AD`, Nutty `#A67C52`, Chocolate `#5D4037`, Sweet/Caramel `#D4AC0D`)과 한국어 향미 앵커 간 매칭 일치율(Accuracy) 및 반응시간(RT) 측정.
- **평가 기준**: 무작위 기대 일치율(14.3%) 대비 유의한 초과 일치율 및 문화적 혼동 쌍(예: Berry vs Citrus, Nutty vs Chocolate) 식별 후 팔레트 보정.
