"""Core Flavor Language Analysis (SCA/WCR Hierarchical Lexicon + Specificity vs Narrative).

Strictly separates:
1. Observed lexical occurrences in 129 official brand SKU descriptions
2. Analytical taxonomy (SCA/WCR flavor families, sensory specificity, narrative density)
3. Statistical tests (Chi-square + Cramer's V across brands; OLS controlling for
   text_length and single-origin vs blend)
"""

from __future__ import annotations

import json
import re
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
        "broad": ["베리", "베리류", "berry"],
        "anchors": [
            "딸기", "블루베리", "라즈베리", "크랜베리", "블랙베리", "체리",
            "스트로베리", "strawberry", "blueberry", "raspberry", "blackberry", "cherry",
        ],
    },
    "Citrus": {
        "broad": ["시트러스", "감귤류", "citrus"],
        "anchors": [
            "오렌지", "감귤", "귤", "유자", "자몽", "레몬", "라임", "만다린", "블러드오렌지",
            "orange", "lemon", "lime", "grapefruit", "yuzu", "mandarin",
        ],
    },
    "Stone/Other Fruit": {
        "broad": ["과일", "과일향", "열대과일", "fruity", "fruit", "tropical"],
        "anchors": [
            "복숭아", "황도", "백도", "살구", "자두", "사과", "청사과", "청포도", "포도",
            "망고", "파인애플", "패션프루트", "무화과", "석류", "건과일", "멜론", "배",
            "peach", "apricot", "plum", "apple", "grape", "mango", "pineapple", "fig", "dried fruit",
        ],
    },
    "Floral": {
        "broad": ["꽃", "꽃향", "플로럴", "floral"],
        "anchors": [
            "자스민", "재스민", "장미", "로즈", "아카시아", "라벤더", "베르가못",
            "캐모마일", "오렌지블라썸", "히비스커스", "엘더플라워", "허브",
            "jasmine", "rose", "blossom", "bergamot", "lavender", "chamomile",
        ],
    },
    "Nutty": {
        "broad": ["견과", "견과류", "너티", "고소", "nut", "nutty"],
        "anchors": [
            "아몬드", "헤이즐넛", "호두", "땅콩", "피칸", "마카다미아", "캐슈넛", "피스타치오",
            "almond", "hazelnut", "walnut", "pecan", "peanut", "cashew",
        ],
    },
    "Chocolate/Cocoa": {
        "broad": ["초코", "초콜릿", "카카오", "코코아", "chocolate", "cacao", "cocoa"],
        "anchors": [
            "다크초콜릿", "밀크초콜릿", "화이트초콜릿", "모카", "가나슈", "카카오닙스",
            "dark chocolate", "milk chocolate", "mocha", "ganache",
        ],
    },
    "Sweet/Caramel": {
        "broad": ["단맛", "달콤", "스윗", "sweet", "sweetness"],
        "anchors": [
            "카라멜", "캐러멜", "토피", "버터스카치", "흑설탕", "브라운슈가", "메이플",
            "당밀", "꿀", "허니", "슈거시럽", "달고나", "사탕수수", "바닐라", "마시멜로",
            "caramel", "toffee", "brown sugar", "maple", "honey", "vanilla", "molasses",
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
    "페루", "르완다", "온두라스", "인도네시아", "엘살바도르", "니카라과", "예멘",
    "ethiopia", "colombia", "kenya", "brazil", "guatemala", "costa rica", "panama",
]


def clean_boilerplate(text: str) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    return t


def extract_sku_features(row: pd.Series) -> dict[str, Any]:
    sku_name = str(row.get("sku_name") or "")
    desc = clean_boilerplate(str(row.get("description_raw") or ""))
    tags = str(row.get("tags_raw") or "")
    combined = f"{sku_name} {desc} {tags}".strip()
    lower = combined.lower()
    text_len = max(len(combined), 1)

    family_hits: dict[str, int] = {}
    extracted_anchors: list[str] = []
    broad_hits = 0
    anchor_hits = 0

    for fam, spec in FLAVOR_HIERARCHY.items():
        fam_anchors = [kw for kw in spec["anchors"] if kw.lower() in lower]
        fam_broad = [kw for kw in spec["broad"] if kw.lower() in lower]
        total_fam = len(fam_anchors) + len(fam_broad)
        family_hits[fam] = total_fam
        broad_hits += len(fam_broad)
        anchor_hits += len(fam_anchors)
        extracted_anchors.extend(fam_anchors)

    # Dominant flavor family (highest mention count; Ties broken by order, 0 -> Unspecified)
    max_hits = max(family_hits.values()) if family_hits else 0
    if max_hits > 0:
        dominant_family = max(family_hits.keys(), key=lambda k: family_hits[k])
    else:
        dominant_family = "Unspecified"

    # Independent Coding 1: Sensory Specificity (broad=1, specific anchor=2)
    sensory_specificity = float(broad_hits * 1.0 + anchor_hits * 2.0)
    if anchor_hits > 0:
        specificity_tier = "Specific-Anchored"
    elif broad_hits > 0:
        specificity_tier = "Broad-Only"
    else:
        specificity_tier = "None-Stated"

    # Independent Coding 2: Narrative Density (abstract/emotional terms per 100 chars)
    abstract_matches = [kw for kw in NARRATIVE_ABSTRACT_TERMS if kw in lower]
    narrative_count = len(abstract_matches)
    narrative_density = round(narrative_count / (text_len / 100.0), 4)

    # Explicit acidity / body cues (never inferred from Berry/Citrus!)
    acidity_explicit = int(any(k in lower for k in ["산미", "acidity", "산뜻", "청량"]))
    body_explicit = int(any(k in lower for k in ["바디", "질감", "body", "크리미", "실키", "묵직"]))

    origin_hits = [o for o in ORIGIN_KEYWORDS if o in lower]
    is_single_origin = int(
        len(origin_hits) == 1
        or ("싱글" in lower or "single" in lower)
        and "블렌드" not in lower
        and "blend" not in lower
    )

    out: dict[str, Any] = {
        "text_length": text_len,
        "dominant_flavor_family": dominant_family,
        "total_flavor_mentions": int(sum(family_hits.values())),
        "broad_term_count": int(broad_hits),
        "specific_anchor_count": int(anchor_hits),
        "sensory_specificity": sensory_specificity,
        "specificity_tier": specificity_tier,
        "narrative_count": narrative_count,
        "narrative_density": narrative_density,
        "acidity_explicit": acidity_explicit,
        "body_explicit": body_explicit,
        "is_single_origin": is_single_origin,
        "extracted_anchors": ", ".join(dict.fromkeys(extracted_anchors)) if extracted_anchors else "",
        "extracted_narrative": ", ".join(dict.fromkeys(abstract_matches)) if abstract_matches else "",
    }
    for fam, cnt in family_hits.items():
        out[f"fam_{fam}_cnt"] = cnt
        out[f"fam_{fam}_has"] = int(cnt > 0)
    return out


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
        (coded["price_krw"] > 0) & (coded["weight_g"] > 0),
        (coded["price_krw"] / coded["weight_g"] * 100).round(0),
        np.nan,
    )
    coded = coded.merge(reg[["brand_id", "brand_segment"]], on="brand_id", how="left")
    coded.to_csv(PROCESSED_DIR / "sku_flavor_language_coded.csv", index=False, encoding="utf-8-sig")

    # Brand-level Fingerprint: SKU Mention Rate (%) AND Term Share (%)
    families = list(FLAVOR_HIERARCHY.keys())
    fp_rows = []
    for (bid, bname, bseg), grp in coded.groupby(["brand_id", "brand_name", "brand_segment"]):
        n_skus = len(grp)
        total_terms = grp[[f"fam_{f}_cnt" for f in families]].sum().sum()
        row_d: dict[str, Any] = {
            "brand_id": bid,
            "brand_name": bname,
            "brand_segment": bseg,
            "sku_count": int(n_skus),
            "median_price_per_100g": round(float(grp["price_per_100g"].median()), 0)
            if grp["price_per_100g"].notna().any()
            else np.nan,
            "mean_text_length": round(float(grp["text_length"].mean()), 1),
            "mean_sensory_specificity": round(float(grp["sensory_specificity"].mean()), 2),
            "mean_narrative_density": round(float(grp["narrative_density"].mean()), 3),
            "pct_specific_anchored": round(float((grp["specificity_tier"] == "Specific-Anchored").mean() * 100), 1),
        }
        for f in families:
            row_d[f"sku_pct_{f}"] = round(float(grp[f"fam_{f}_has"].mean() * 100), 1)
            fam_terms = float(grp[f"fam_{f}_cnt"].sum())
            row_d[f"term_share_{f}"] = round(fam_terms / total_terms * 100, 1) if total_terms > 0 else 0.0
        fp_rows.append(row_d)

    fp_df = pd.DataFrame(fp_rows).sort_values("mean_sensory_specificity", ascending=False).reset_index(drop=True)
    fp_df.to_csv(OUT_DIR / "brand_flavor_fingerprint.csv", index=False, encoding="utf-8-sig")

    # Q1: Chi-square & Cramer's V across brands x dominant_flavor_family (excluding Unspecified or including all)
    ct_all = pd.crosstab(coded["brand_id"], coded["dominant_flavor_family"])
    chi2, p_chi2, dof, _ = stats.chi2_contingency(ct_all)
    n_obs = ct_all.sum().sum()
    min_dim = min(ct_all.shape) - 1
    cramers_v = float(np.sqrt(chi2 / (n_obs * min_dim))) if min_dim > 0 else 0.0

    # Q2: Relationship between narrative_density and sensory_specificity (raw + controlled OLS)
    r_raw, p_raw = stats.pearsonr(coded["narrative_density"], coded["sensory_specificity"])
    rho_raw, p_rho = stats.spearmanr(coded["narrative_density"], coded["sensory_specificity"])
    ols = smf.ols(
        "sensory_specificity ~ narrative_density + text_length + is_single_origin",
        data=coded,
    ).fit()

    stats_summary = {
        "total_skus": int(len(coded)),
        "brand_count": int(coded["brand_id"].nunique()),
        "specificity_tier_counts": coded["specificity_tier"].value_counts().to_dict(),
        "dominant_family_counts": coded["dominant_flavor_family"].value_counts().to_dict(),
        "q1_brand_vs_dominant_family": {
            "chi2": round(float(chi2), 3),
            "dof": int(dof),
            "p_value": round(float(p_chi2), 6),
            "cramers_v": round(cramers_v, 4),
        },
        "q2_narrative_vs_specificity": {
            "pearson_r": round(float(r_raw), 4),
            "pearson_p": round(float(p_raw), 6),
            "spearman_rho": round(float(rho_raw), 4),
            "spearman_p": round(float(p_rho), 6),
            "ols_controlled_r2": round(float(ols.rsquared), 4),
            "ols_narrative_coef": round(float(ols.params["narrative_density"]), 4),
            "ols_narrative_p": round(float(ols.pvalues["narrative_density"]), 6),
            "ols_text_length_coef": round(float(ols.params["text_length"]), 6),
            "ols_text_length_p": round(float(ols.pvalues["text_length"]), 6),
            "ols_single_origin_coef": round(float(ols.params["is_single_origin"]), 4),
            "ols_single_origin_p": round(float(ols.pvalues["is_single_origin"]), 6),
        },
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
