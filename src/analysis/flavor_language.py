"""Core Flavor Language Analysis (SCA/WCR Hierarchical Lexicon + Specificity vs Narrative).

Strictly separates:
1. Observed lexical occurrences in cleaned official brand SKU descriptions
2. Analytical taxonomy (SCA/WCR flavor families, sensory specificity, narrative density,
   product type & origin type)
3. Statistical tests (Monte Carlo permutation Chi-square + Cramer's V, rare-category
   robustness check, and OLS controlling for text_length, origin_type, and brand_id)
"""

from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
RAW_BEANS_PATH = ROOT / "data" / "raw" / "brands" / "official_brand_beans_raw.csv"
RAW_BRAND_REG_PATH = ROOT / "data" / "raw" / "brands" / "official_brand_registry.csv"
PROCESSED_DIR = ROOT / "data" / "processed" / "brands"
OUT_DIR = ROOT / "outputs" / "tables"

# SCA/WCR-inspired hierarchical lexicon: Family -> (Broad terms, Specific anchors)
FLAVOR_HIERARCHY: dict[str, dict[str, list[str]]] = {
    "Berry": {
        "broad": ["베리류", "베리", "berry"],
        "anchors": [
            "스트로베리", "블루베리", "라즈베리", "크랜베리", "블랙베리", "딸기", "체리",
            "strawberry", "blueberry", "raspberry", "blackberry", "cranberry", "cherry",
        ],
    },
    "Citrus": {
        "broad": ["시트러스", "감귤류", "citrus"],
        "anchors": [
            "블러드오렌지", "만다린", "오렌지", "감귤", "자몽", "레몬", "라임", "유자", "귤",
            "grapefruit", "mandarin", "orange", "lemon", "lime", "yuzu",
        ],
    },
    "Stone/Other Fruit": {
        "broad": ["열대과일", "과일향", "과일", "fruity", "fruit", "tropical"],
        "anchors": [
            "패션프루트", "청포도", "청사과", "파인애플", "복숭아", "무화과", "건과일",
            "황도", "백도", "살구", "자두", "사과", "포도", "망고", "석류", "멜론", "배",
            "dried fruit", "pineapple", "apricot", "peach", "apple", "grape", "mango", "plum", "fig", "pear",
        ],
    },
    "Floral": {
        "broad": ["플로럴", "꽃향", "꽃", "floral"],
        "anchors": [
            "오렌지블라썸", "엘더플라워", "히비스커스", "캐모마일", "베르가못", "아카시아",
            "라벤더", "자스민", "재스민", "장미", "로즈", "허브",
            "chamomile", "bergamot", "lavender", "jasmine", "blossom", "rose",
        ],
    },
    "Nutty": {
        "broad": ["견과류", "견과", "너티", "고소", "nutty", "nut"],
        "anchors": [
            "마카다미아", "피스타치오", "헤이즐넛", "캐슈넛", "아몬드", "호두", "땅콩", "피칸",
            "hazelnut", "almond", "walnut", "peanut", "cashew", "pecan",
        ],
    },
    "Chocolate/Cocoa": {
        "broad": ["초콜릿", "카카오", "코코아", "초코", "chocolate", "cacao", "cocoa"],
        "anchors": [
            "다크초콜릿", "밀크초콜릿", "화이트초콜릿", "카카오닙스", "가나슈", "모카",
            "dark chocolate", "milk chocolate", "white chocolate", "ganache", "mocha",
        ],
    },
    "Sweet/Caramel": {
        "broad": ["단맛", "달콤", "스윗", "sweetness", "sweet"],
        "anchors": [
            "버터스카치", "브라운슈가", "슈거시럽", "사탕수수", "마시멜로", "흑설탕",
            "카라멜", "캐러멜", "메이플", "달고나", "바닐라", "토피", "당밀", "허니", "꿀",
            "brown sugar", "molasses", "caramel", "vanilla", "toffee", "maple", "honey",
        ],
    },
}

NARRATIVE_ABSTRACT_TERMS: list[str] = [
    "기억", "꿈", "공기", "여운", "일상", "위로", "계절", "바람", "숲", "밤", "아침",
    "여행", "사랑", "영감", "감성", "조화", "우아", "클래식", "시그니처", "이야기",
    "풍경", "여유", "편안", "기분", "오후", "순간", "마음",
]

ORIGIN_KEYWORDS = [
    "에티오피아", "콜롬비아", "케냐", "브라질", "과테말라", "코스타리카", "파나마",
    "페루", "르완다", "온두라스", "인도네시아", "엘살바도르", "니카라과", "예멘", "멕시코", "에콰도르",
    "ethiopia", "colombia", "kenya", "brazil", "guatemala", "costa rica", "panama",
    "mexico", "ecuador", "peru", "rwanda", "honduras", "indonesia", "el salvador", "nicaragua",
]


def _compile_term_pattern(term: str) -> re.Pattern[str]:
    """Compile boundary-aware regex for Korean and English flavor/narrative terms."""
    t = term.lower()
    if re.fullmatch(r"[a-z0-9\s\-]+", t):
        return re.compile(rf"\b{re.escape(t)}\b", flags=re.I)

    # Collision-prone Korean terms need strict right/left boundary guards
    if t == "배":
        # Match standalone pear (e.g., "배,", "배와", "배의", "배 ") — NEVER 배송, 배전, 중약배전, 예배, 배운, 재배
        return re.compile(r"(?<![가-힣0-9])배(?=(?:[,\s·/\.\)]|와|과|의|처럼|같은|향|풍미|$))")
    if t == "모카":
        # Never match 모카포트 (moka pot)
        return re.compile(r"(?<![가-힣])모카(?!포트|[가-힣])")
    if t == "고소":
        return re.compile(r"(?<![가-힣])고소(?=한|함|하고|하며|운|음|[,\s·/\.\)]|$)")
    if t in {"꽃", "꿀", "귤", "밤", "꿈", "숲"}:
        return re.compile(rf"(?<![가-힣]){re.escape(t)}(?=향|내음|맛|의|과|와|에|을|를|은|는|이|가|으로|로|[,\s·/\.\)]|$)")

    return re.compile(rf"(?<![가-힣]){re.escape(t)}")


# Precompile unified lexicon sorted by term length descending (longest phrase wins span)
_LEXICON_ITEMS: list[tuple[str, str, str, re.Pattern[str]]] = []
for _fam, _spec in FLAVOR_HIERARCHY.items():
    for _tier in ("anchors", "broad"):
        for _kw in _spec[_tier]:
            _LEXICON_ITEMS.append((_kw, _fam, "anchor" if _tier == "anchors" else "broad", _compile_term_pattern(_kw)))
_LEXICON_ITEMS.sort(key=lambda x: len(x[0]), reverse=True)

_NARRATIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (kw, _compile_term_pattern(kw)) for kw in NARRATIVE_ABSTRACT_TERMS
]


def classify_product_type(sku_name: str, tags: str = "") -> str:
    txt = f"{sku_name} {tags}".lower()
    if any(k in txt for k in ["정기배송", "개월", "구독", "subscription"]):
        return "subscription"
    if any(k in txt for k in ["드립백", "drip bag", "티백"]):
        return "drip_bag"
    if any(k in txt for k in ["캡슐", "capsule"]):
        return "capsule"
    if any(k in txt for k in ["세트", "키트", "set", "kit"]):
        return "set_kit"
    return "whole_bean"


def classify_origin_type(sku_name: str, desc: str, tags: str = "") -> str:
    name_tags = f"{sku_name} {tags}".lower()
    full = f"{name_tags} {desc}".lower()

    if any(k in name_tags for k in ["블렌드", "blend"]):
        return "Blend"
    if any(k in desc.lower() for k in ["블렌드입니다", "blend입니다", "블렌드로"]):
        return "Blend"

    name_origins = [o for o in ORIGIN_KEYWORDS if o in name_tags]
    if any(k in name_tags for k in ["싱글", "single origin", "single-origin", "마이크로랏", "micro-lot", "게이샤", "geisha"]):
        return "Single Origin"
    if len(name_origins) == 1:
        return "Single Origin"
    if len(name_origins) >= 2:
        return "Blend"

    full_origins = [o for o in ORIGIN_KEYWORDS if o in full]
    if len(full_origins) == 1 and "블렌드" not in full and "blend" not in full:
        return "Single Origin"
    return "Unspecified"


def clean_text_for_analysis(text: str) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    return t


def _overlaps(span: tuple[int, int], used: list[tuple[int, int]]) -> bool:
    s, e = span
    return any(not (e <= us or s >= ue) for us, ue in used)


def extract_sku_features(row: pd.Series) -> dict[str, Any]:
    sku_name = str(row.get("sku_name") or "")
    desc = clean_text_for_analysis(str(row.get("description_raw") or ""))
    tags = str(row.get("tags_raw") or "")
    combined = f"{sku_name} {desc}".strip()
    lower = combined.lower()
    text_len = max(len(combined), 1)

    product_type = classify_product_type(sku_name, tags)
    origin_type = classify_origin_type(sku_name, desc, tags)

    used_spans: list[tuple[int, int]] = []
    matched_records: list[dict[str, Any]] = []
    family_counts: dict[str, int] = {fam: 0 for fam in FLAVOR_HIERARCHY}
    unique_broad: set[str] = set()
    unique_anchors: set[str] = set()

    for kw, fam, tier, pat in _LEXICON_ITEMS:
        for m in pat.finditer(lower):
            span = (m.start(), m.end())
            if _overlaps(span, used_spans):
                continue
            used_spans.append(span)
            family_counts[fam] += 1
            if tier == "anchor":
                unique_anchors.add(f"{fam}:{kw}")
            else:
                unique_broad.add(f"{fam}:{kw}")
            matched_records.append(
                {
                    "family": fam,
                    "tier": tier,
                    "term": kw,
                    "pos": m.start(),
                }
            )

    matched_records.sort(key=lambda r: r["pos"])
    total_mentions = len(matched_records)
    broad_count = len(unique_broad)
    anchor_count = len(unique_anchors)

    # Dominant flavor family: explicit None-Stated and Multi-Family (Tie)
    max_hits = max(family_counts.values()) if family_counts else 0
    if max_hits == 0:
        dominant_family = "None-Stated"
    else:
        top_fams = [f for f, c in family_counts.items() if c == max_hits]
        dominant_family = top_fams[0] if len(top_fams) == 1 else "Multi-Family (Tie)"

    # Clean Sensory Specificity (separated from broad-word repetition)
    if anchor_count > 0:
        specificity_tier = "Specific-Anchored"
        sensory_specificity = float(anchor_count)
    elif broad_count > 0:
        specificity_tier = "Broad-Only"
        sensory_specificity = 0.5
    else:
        specificity_tier = "None-Stated"
        sensory_specificity = 0.0

    # Narrative Density: total occurrences of narrative/abstract terms per 100 chars
    nar_used: list[tuple[int, int]] = []
    nar_terms: list[str] = []
    for kw, pat in _NARRATIVE_PATTERNS:
        for m in pat.finditer(lower):
            span = (m.start(), m.end())
            if _overlaps(span, nar_used):
                continue
            nar_used.append(span)
            nar_terms.append(kw)
    narrative_count = len(nar_terms)
    narrative_density = round(narrative_count / (text_len / 100.0), 4)

    # Explicit acidity / body cues (never inferred from Berry/Citrus)
    acidity_explicit = int(any(k in lower for k in ["산미", "acidity", "산뜻", "청량"]))
    body_explicit = int(any(k in lower for k in ["바디", "질감", "body", "크리미", "실키", "묵직"]))

    out: dict[str, Any] = {
        "product_type_std": product_type,
        "is_comparable_whole_bean": int(product_type == "whole_bean"),
        "origin_type": origin_type,
        "is_single_origin": int(origin_type == "Single Origin"),
        "text_length": text_len,
        "dominant_flavor_family": dominant_family,
        "total_flavor_mentions": int(total_mentions),
        "broad_term_count": int(broad_count),
        "specific_anchor_count": int(anchor_count),
        "sensory_specificity": sensory_specificity,
        "specificity_tier": specificity_tier,
        "narrative_count": int(narrative_count),
        "narrative_density": narrative_density,
        "acidity_explicit": acidity_explicit,
        "body_explicit": body_explicit,
        "matched_flavor_terms": "; ".join(
            f"{r['family']}:{r['tier']}:{r['term']}@{r['pos']}" for r in matched_records
        ),
        "extracted_anchors": ", ".join(sorted({r["term"] for r in matched_records if r["tier"] == "anchor"})),
        "extracted_narrative": ", ".join(nar_terms),
    }
    for fam, cnt in family_counts.items():
        out[f"fam_{fam}_cnt"] = cnt
        out[f"fam_{fam}_has"] = int(cnt > 0)
    return out


def _monte_carlo_chi2(ct: pd.DataFrame, n_resamples: int = 10000, seed: int = 42) -> dict[str, Any]:
    """Compute chi2, Cramer's V, sparse-cell %, and Monte Carlo exact p-value."""
    arr = ct.to_numpy(dtype=int)
    chi2, p_asymp, dof, expected = stats.chi2_contingency(arr)
    n_obs = int(arr.sum())
    min_dim = min(arr.shape) - 1
    cramers_v = float(np.sqrt(chi2 / (n_obs * min_dim))) if min_dim > 0 and n_obs > 0 else 0.0
    sparse_cells = int((expected < 5).sum())
    total_cells = int(expected.size)

    # Permutation-based Monte Carlo p-value preserving row & column marginals
    row_totals = arr.sum(axis=1)
    col_totals = arr.sum(axis=0)
    rng = np.random.default_rng(seed)
    col_pool = np.repeat(np.arange(len(col_totals)), col_totals)
    ge_count = 0
    for _ in range(n_resamples):
        perm = rng.permutation(col_pool)
        sim = np.zeros_like(arr)
        idx = 0
        for r_i, r_cnt in enumerate(row_totals):
            counts = np.bincount(perm[idx : idx + r_cnt], minlength=len(col_totals))
            sim[r_i] = counts
            idx += r_cnt
        with np.errstate(divide="ignore", invalid="ignore"):
            sim_chi2 = np.nansum((sim - expected) ** 2 / expected)
        if sim_chi2 >= chi2 - 1e-12:
            ge_count += 1
    p_mc = float((ge_count + 1) / (n_resamples + 1))

    return {
        "chi2": round(float(chi2), 3),
        "dof": int(dof),
        "p_asymptotic": round(float(p_asymp), 6),
        "p_monte_carlo": round(p_mc, 6),
        "cramers_v": round(cramers_v, 4),
        "sparse_cells_lt5": sparse_cells,
        "total_cells": total_cells,
        "sparse_cell_pct": round(sparse_cells / total_cells * 100, 1) if total_cells else 0.0,
    }


def _compute_cooccurrence(df: pd.DataFrame, families: list[str]) -> pd.DataFrame:
    rows = []
    for f1, f2 in combinations(families, 2):
        both = int(((df[f"fam_{f1}_has"] == 1) & (df[f"fam_{f2}_has"] == 1)).sum())
        c1 = int(df[f"fam_{f1}_has"].sum())
        c2 = int(df[f"fam_{f2}_has"].sum())
        union = int(((df[f"fam_{f1}_has"] == 1) | (df[f"fam_{f2}_has"] == 1)).sum())
        jaccard = round(both / union, 3) if union > 0 else 0.0
        rows.append(
            {
                "family_a": f1,
                "family_b": f2,
                "co_occur_skus": both,
                "family_a_skus": c1,
                "family_b_skus": c2,
                "jaccard": jaccard,
            }
        )
    return pd.DataFrame(rows).sort_values(["co_occur_skus", "jaccard"], ascending=False).reset_index(drop=True)


def _run_population_stats(df: pd.DataFrame, families: list[str]) -> dict[str, Any]:
    ct_all = pd.crosstab(df["brand_id"], df["dominant_flavor_family"])
    q1_all = _monte_carlo_chi2(ct_all)

    # Robustness check: collapse rare dominant categories (< 5% of SKUs) into Other/Rare
    fam_freq = df["dominant_flavor_family"].value_counts(normalize=True)
    rare_fams = set(fam_freq[fam_freq < 0.05].index)
    dom_collapsed = df["dominant_flavor_family"].apply(lambda x: "Other/Rare" if x in rare_fams else x)
    ct_col = pd.crosstab(df["brand_id"], dom_collapsed)
    q1_collapsed = _monte_carlo_chi2(ct_col)

    # Q2: narrative_density vs sensory_specificity
    r_raw, p_raw = stats.pearsonr(df["narrative_density"], df["sensory_specificity"])
    rho_raw, p_rho = stats.spearmanr(df["narrative_density"], df["sensory_specificity"])
    ols_simple = smf.ols(
        "sensory_specificity ~ narrative_density + text_length + is_single_origin",
        data=df,
    ).fit()
    ols_brand = smf.ols(
        "sensory_specificity ~ narrative_density + text_length + is_single_origin + C(brand_id)",
        data=df,
    ).fit()

    return {
        "n_skus": int(len(df)),
        "specificity_tier_counts": df["specificity_tier"].value_counts().to_dict(),
        "dominant_family_counts": df["dominant_flavor_family"].value_counts().to_dict(),
        "origin_type_counts": df["origin_type"].value_counts().to_dict(),
        "q1_brand_vs_dominant_family": q1_all,
        "q1_collapsed_rare_categories": q1_collapsed,
        "q2_narrative_vs_specificity": {
            "pearson_r": round(float(r_raw), 4),
            "pearson_p": round(float(p_raw), 6),
            "spearman_rho": round(float(rho_raw), 4),
            "spearman_p": round(float(p_rho), 6),
            "ols_r2": round(float(ols_simple.rsquared), 4),
            "ols_narrative_coef": round(float(ols_simple.params["narrative_density"]), 4),
            "ols_narrative_p": round(float(ols_simple.pvalues["narrative_density"]), 6),
            "ols_text_length_p": round(float(ols_simple.pvalues["text_length"]), 6),
            "ols_single_origin_coef": round(float(ols_simple.params["is_single_origin"]), 4),
            "ols_single_origin_p": round(float(ols_simple.pvalues["is_single_origin"]), 6),
            "ols_brand_fe_r2": round(float(ols_brand.rsquared), 4),
            "ols_brand_fe_narrative_coef": round(float(ols_brand.params["narrative_density"]), 4),
            "ols_brand_fe_narrative_p": round(float(ols_brand.pvalues["narrative_density"]), 6),
            "ols_brand_fe_single_origin_coef": round(float(ols_brand.params["is_single_origin"]), 4),
            "ols_brand_fe_single_origin_p": round(float(ols_brand.pvalues["is_single_origin"]), 6),
        },
    }


def analyze_flavor_language() -> dict[str, Any]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_BEANS_PATH).drop_duplicates(subset=["brand_id", "sku_name"]).reset_index(drop=True)
    reg = pd.read_csv(RAW_BRAND_REG_PATH)

    feat_df = pd.DataFrame([extract_sku_features(row) for _, row in df.iterrows()])
    coded = pd.concat([df, feat_df], axis=1)
    coded["weight_g"] = pd.to_numeric(coded["weight_g"], errors="coerce")
    coded["price_krw"] = pd.to_numeric(coded["price_krw"], errors="coerce")
    coded["price_per_100g"] = np.where(
        (coded["price_krw"] > 0) & (coded["weight_g"] > 0) & (coded["product_type_std"] == "whole_bean"),
        (coded["price_krw"] / coded["weight_g"] * 100).round(0),
        np.nan,
    )
    coded = coded.merge(reg[["brand_id", "brand_segment"]], on="brand_id", how="left")
    coded.to_csv(PROCESSED_DIR / "sku_flavor_language_coded.csv", index=False, encoding="utf-8-sig")

    families = list(FLAVOR_HIERARCHY.keys())
    # Brand-level Fingerprint using SKU Mention Rate (%) + Detection Rate (%)
    fp_rows = []
    for (bid, bname, bseg), grp in coded.groupby(["brand_id", "brand_name", "brand_segment"]):
        n_skus = len(grp)
        wb_grp = grp[grp["is_comparable_whole_bean"] == 1]
        detected_n = int((grp["specificity_tier"] != "None-Stated").sum())
        row_d: dict[str, Any] = {
            "brand_id": bid,
            "brand_name": bname,
            "brand_segment": bseg,
            "sku_count": int(n_skus),
            "whole_bean_count": int(len(wb_grp)),
            "flavor_detected_count": detected_n,
            "flavor_detected_pct": round(detected_n / n_skus * 100, 1) if n_skus else 0.0,
            "median_whole_bean_price_per_100g": round(float(wb_grp["price_per_100g"].median()), 0)
            if wb_grp["price_per_100g"].notna().any()
            else np.nan,
            "mean_text_length": round(float(grp["text_length"].mean()), 1),
            "mean_sensory_specificity": round(float(grp["sensory_specificity"].mean()), 2),
            "mean_narrative_density": round(float(grp["narrative_density"].mean()), 3),
            "pct_specific_anchored": round(float((grp["specificity_tier"] == "Specific-Anchored").mean() * 100), 1),
        }
        for f in families:
            row_d[f"sku_pct_{f}"] = round(float(grp[f"fam_{f}_has"].mean() * 100), 1)
            row_d[f"wb_sku_pct_{f}"] = round(float(wb_grp[f"fam_{f}_has"].mean() * 100), 1) if len(wb_grp) else 0.0
        fp_rows.append(row_d)

    fp_df = pd.DataFrame(fp_rows).sort_values("mean_sensory_specificity", ascending=False).reset_index(drop=True)
    fp_df.to_csv(OUT_DIR / "brand_flavor_fingerprint.csv", index=False, encoding="utf-8-sig")

    cooc_df = _compute_cooccurrence(coded, families)
    cooc_df.to_csv(OUT_DIR / "flavor_cooccurrence.csv", index=False, encoding="utf-8-sig")

    wb_only = coded[coded["is_comparable_whole_bean"] == 1].copy()
    stats_summary = {
        "total_skus": int(len(coded)),
        "comparable_whole_bean_skus": int(len(wb_only)),
        "brand_count": int(coded["brand_id"].nunique()),
        "product_type_counts": coded["product_type_std"].value_counts().to_dict(),
        "all_skus": _run_population_stats(coded, families),
        "whole_bean_only": _run_population_stats(wb_only, families),
        "top_cooccurrences": cooc_df.head(5).to_dict(orient="records"),
    }
    (OUT_DIR / "flavor_language_stats.json").write_text(
        json.dumps(stats_summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return stats_summary


def main() -> int:
    res = analyze_flavor_language()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
