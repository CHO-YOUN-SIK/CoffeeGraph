# CoffeeGraph — Consumer Signals × Brand Values Integration (2026-11-19)

## Design decision
CoffeeGraph is an **aesthetic, data-driven generative visual system**, not a customer-relationship scorecard.
The long-term artistic idea is to let people's stated coffee-experience values encounter brands' publicly expressed values.
For now, the evidence has **different units and populations**, so consumer data and brand data are independent visual layers.

## Latest code and source audit
- Main at 2026-11-19 includes Track C with 8 brand websites and a 3D Brand Value Space.
- The existing Track C brand X/Y/Z values were created by researcher-chosen weights on SKU counts, descriptions and philosophy-page keywords. They **are not** measured brand morals, consumer perceptions, purchase preferences, or validated value constructs.
- Official web pages for TERAROSA and Center Coffee have inadequate analyzable main-body text after cleaning. Treat Z as **missing/unobserved**, never as zero philosophical commitment. Limited descriptions are also not definitive evidence of missing values.
- Brand SKU categorization can still contain accessories, capsules, ready-to-drink items and imputed weights (see prior audit). **Practical/Sensory X/Y are exploratory**, not definitive rankings. Review the open data-cleaning PR before production use.
- Previous 3D display drew a made-up translucent ellipsoid labelled "Consumer Field"; this version removes it to avoid false quantitative meaning.

## Verified, directly observable consumer signals
Source: Opensurvey, *Cafe Trend Report 2025*, reporting article published 2025-12-08:
https://blog.opensurvey.co.kr/article/cafe-2025-2/

| Question construct | Published signal | % | Can be inferred? |
|---|---|---:|---|
| Ever used drink customization | Personalization options | 82.4 | Experience, not importance or practical-value index |
| Specific customization option | Coffee strength adjustment | 44.1 | Behavior, not premium preference |
| Cafe premium criterion | Coffee and bean quality | 58.4 | Premium cue; indicates sensory importance in that question |
| Cafe premium criterion | Atmosphere and interior | 49.8 | Space experience cue, separate from ethical values |
| Cafe premium criterion | Bakery/dessert quality | 40.9 | Product/experience cue, not philosophical values |

The survey is national (age 20–59, 2-phase design, initial n=2,000). Published article aggregates do **not** provide a harmonized respondent-level basis, comparable ethical-values item, or a direct respondent-brand linkage for the current 8 specialty brands.

Curated numerical evidence: `data/curated/consumer/opensurvey_cafe_2025_public_metrics.csv`.
Deterministic validation: `python -m src.analysis.consumer_value_evidence`.
Output: `outputs/tables/consumer_value_evidence.json`.

## Public-market data remains the primary spatial and temporal layer
Seoul CS100010 district/commercial-area estimated sales, store counts and transactions provide context, not personal motivations. Local sales time shares do not establish that individual buyers choose a brand because of convenience or philosophical values.

## Three-dimensional mapping policy (no made-up coordinates)
| Visual layer | Source | Identifiable construct | Allowed rendering |
|---|---|---|---|
| Market field | Seoul public market data | Sales mix, store change, units and share | Space/time field; observed measurements |
| Consumer signals | National cafe survey aggregates | Each distinct measured behavior/criterion | Independent evidence ribbons/cards with wording/denominator |
| Brand disclosure | Official brand pages and vetted SKUs | Published product/brand communication | Brand marks, textual cue fields, coverage-aware XYZ *proxies* |

**Not allowed yet**: consumer 3D coordinates produced by averaging unrelated response percentages; invented consumer ellipsoids; calling geometrical overlap a brand-consumer fit; assigning zero to missing brand text; interpreting website keyword counts as ethical commitments.

## Next evidence requirements
1. Obtain KREI 2025 original survey/questionnaire with proper access/use approval; identify coffee-specific questionnaire variables, sample strata, final weights and lawful derivative publication.
2. Verify each Opensurvey full-report item denominator before computing cross-item comparators; avoid redistributing raw proprietary tables.
3. If credentials are available, connect NAVER API HUB Search Trend to measure **relative** search interest; it is not sales, preference, or attitude. Follow current API HUB documentation; never commit API credentials.
4. For meaningful consumer/brand **joint spatial mapping**, obtain aligned coffee-consumer survey questions about practical, sensory and ethical values on a common scale and matched brand perceptions, followed by a measurement validation study.
5. In the meantime, emphasize aesthetic *juxtaposition of truthful data layers*, with a viewer-selectable lens for each measured construct, clear source and missingness labels, and stable generative seeds.

## Release/check rules
- Every observed survey number must preserve source URL, wording, scope, denominator caveat, and publication date.
- Consumer/brand comparators may not share a numerical axis until measurement equivalence is demonstrated.
- Z brand coordinate can be NaN: render visibly as "not located", never infer (0,0,0).
- Automated tests verify pipeline semantics, but source-content review and data licensing still need manual follow-up.
