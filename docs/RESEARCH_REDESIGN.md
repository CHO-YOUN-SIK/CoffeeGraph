# CoffeeGraph — Evidence-first Research & Visualization Redesign

## Decision to support
Locate **where** Seoul coffee demand differs by time, competition and estimated sales, identify **which of those observations** warrants testing, and determine **how to represent coffee flavor information** for an actual user. A visual artifact must answer one specific decision question, not simply display all available metrics.

## Layer 1 — Public market evidence (primary)
- Source: Seoul Open Data, CS100010, with explicit quarter, district, commercial-area keys and provenance.
- Visual A: 25-district small multiples for 2024Q2 → 2026Q1 store count change and store-normalized estimated sales, with denominators and observation windows in tooltips.
- Visual B: commercial-area scatter/linked table for lunch-sales share, weekend-sales share, store count and estimated sales per store; compare selected commercial areas without inferring customer choice time.
- Missingness: report 1,519 store-observed areas versus 1,064 matched sales-observed areas; 455 unmatched areas are excluded (not zero-sales), and are systematically smaller.
- Cluster use: optional exploratory filter only. Silhouette 0.1798 does not establish four objectively distinct audience types.

## Layer 2 — Brand-language evidence (context only)
- Audit the complete 129-row catalogue first and exclude merchandise, drinks, capsules, subscriptions, and mixed sets from comparable whole-bean inference.
- Distinguish **text not found** from **flavor absent**; product-page HTML may omit sensory information that exists in images.
- Recompute counts, prices, effect sizes, p-values and visualizations after audit. No fixed historical n=98 or historical significance criteria.
- Use brand × flavor-family mention-rate heatmap with numerator/denominator, coverage score, confidence/collection notes, and separate single-origin/blend strata.
- CQI is a sensory reference, not Seoul consumer preference, brand sales, or a causal predictor of the brand market.

## Layer 3 — Interpretation and hypotheses
Each finding must show: Observation → scope/unit → known limitations → alternative explanation → candidate design hypothesis → test required.
Examples:
- Observed: office-associated areas have more lunch-concentrated sales. Unknown: whether individuals feel time pressure or need shorter menus.
- Observed: brand product pages differ in lexical description. Unknown: whether readers comprehend, prefer, or purchase products based on these descriptions.
- H1: a concise taste-summary card may improve comprehension and completion time compared with professional tasting notes.
- H2: descriptive flavor-color mapping may improve recognition over arbitrary colors; **never** call the palette validated before testing.

## Layer 4 — Visualization grammar and usability
- Main overview: public-market time/space patterns; explicit contextual legend and comparator.
- Secondary explorer: filtered, audited brand language distributions; no arbitrary "opportunity whitespace" rectangles.
- Hypothesis workspace: change text encoding (professional, everyday, dual-layer) and color families; show *experiment setup*, not fabricated outcome.
- Link public market and brand evidence only by explanatory annotation: their datasets have no direct consumer-level matching key.
- Default to counts/rates with base population and uncertainty, fixed marker sizes for missing/heterogeneous price variables, colorblind-aware categorical encodings.

## Consumer validation protocol
Use a randomized A/B/C survey with the same coffee, controlled price, photo, origin, and roast information. Compare professional tasting notes, everyday sensory translation, and layered translation; measure objective comprehension (correct answers), selection completion time, confidence, and qualitative reason. Test semantic flavor-to-color mapping independently with forced-choice accuracy and response time, counterbalancing display order. Prespecify sample-size/power, outcomes, exclusions and analysis; do not infer purchase conversion without behavioral purchase data.

## Publication gates
1. Data audit passes: no merchandise or ready-to-drink products in whole-bean denominator; no default weight used for price calculation without provenance.
2. Each chart's measure, unit, denominator, inclusion rule and missingness are visible.
3. Every inferential sentence is labeled Observed / Interpretation / Hypothesis / Validated.
4. Any claim of BX "opportunity" must be tied to public market evidence AND an independently testable consumer task.
5. Automated tests only establish code consistency, not construct validity; manual data annotation and user study still required.

## Current implementation boundary
This redesign removes known non-bean catalogue items from flavor analysis, prevents unsupported opportunity shading and missing-price bubble imputation, and updates tests to reject contamination. Original market data collection and external validation remain unchanged. Brand positioning's legacy pipeline is retained for compatibility and **must not** be presented as a validated consumer or brand-performance comparison before further data audit.
