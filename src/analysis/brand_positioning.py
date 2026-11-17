"""Phase 5 (M5): Brand Positioning & 9-Dimension Flavor Language Codebook Analysis.

Applies the 9-category flavor language codebook (과일, 꽃, 초콜릿, 견과류, 카라멜,
산미, 단맛, 바디·질감, 감성적·추상적 표현) to verified official brand bean SKUs,
computes price-per-100g, origin/process mentions, and sensory-vs-abstract ratios.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_BEANS_PATH = ROOT / "data" / "raw" / "brands" / "official_brand_beans_raw.csv"
RAW_BRAND_REG_PATH = ROOT / "data" / "raw" / "brands" / "official_brand_registry.csv"
PROCESSED_BRAND_DIR = ROOT / "data" / "processed" / "brands"
OUT_DIR = ROOT / "outputs" / "tables"

FLAVOR_CODEBOOK: dict[str, list[str]] = {
    "과일": [
        "과일", "베리", "블루베리", "라즈베리", "딸기", "체리", "자두", "복숭아",
        "살구", "사과", "포도", "오렌지", "감귤", "귤", "유자", "자몽", "레몬",
        "라임", "망고", "파인애플", "패션프루트", "열대과일", "무화과", "석류",
        "berry", "citrus", "peach", "apple", "plum", "cherry", "orange", "lemon", "tropical", "fruity",
    ],
    "꽃": [
        "꽃", "플로럴", "자스민", "재스민", "장미", "로즈", "아카시아", "라벤더",
        "베르가못", "캐모마일", "오렌지블라썸", "엘더플라워", "히비스커스", "허브",
        "floral", "jasmine", "rose", "blossom", "bergamot",
    ],
    "초콜릿": [
        "초콜릿", "초코", "카카오", "코코아", "다크초콜릿", "밀크초콜릿", "모카", "가나슈",
        "chocolate", "cacao", "cocoa", "mocha",
    ],
    "견과류": [
        "견과", "아몬드", "헤이즐넛", "호두", "땅콩", "피칸", "마카다미아", "캐슈넛", "너티", "고소",
        "nut", "nutty", "almond", "hazelnut", "walnut", "pecan",
    ],
    "카라멜": [
        "카라멜", "캐러멜", "토피", "버터스카치", "흑설탕", "브라운슈가", "설탕", "달고나", "메이플", "당밀",
        "caramel", "toffee", "brown sugar", "molasses", "maple",
    ],
    "산미": [
        "산미", "상큼", "산뜻", "시트러스", "쥬시", "청량", "화사", "밝은", "스파클링", "와인",
        "acidity", "bright", "crisp", "juicy", "vibrant", "tangy",
    ],
    "단맛": [
        "단맛", "달콤", "스윗", "꿀", "허니", "캔디", "사탕", "달달",
        "sweet", "sweetness", "honey", "candy",
    ],
    "바디·질감": [
        "바디", "질감", "크리미", "실키", "벨벳", "부드러", "묵직", "깔끔", "밸런스", "라운드", "시럽",
        "body", "creamy", "silky", "velvety", "smooth", "syrupy", "balance", "mouthfeel",
    ],
    "감성적·추상적": [
        "기억", "꿈", "공기", "여운", "일상", "위로", "계절", "바람", "숲", "밤", "아침",
        "여행", "사랑", "영감", "감성", "조화", "우아", "클래식", "시그니처", "이야기", "풍경",
    ],
}

ORIGIN_PATTERNS = {
    "Ethiopia": ["에티오피아", "ethiopia", "예가체프", "시다모", "구지"],
    "Colombia": ["콜롬비아", "colombia", "우일라", "카우카", "안티오키아"],
    "Kenya": ["케냐", "kenya", "니에리", "키리냐가"],
    "Brazil": ["브라질", "brazil", "세하도", "모지아나"],
    "Guatemala": ["과테말라", "guatemala", "안티구아", "우에우에테낭고"],
    "Costa Rica": ["코스타리카", "costa rica", "따라주"],
    "Panama": ["파나마", "panama", "보케테"],
    "Peru": ["페루", "peru"],
    "Rwanda": ["르완다", "rwanda"],
    "Honduras": ["온두라스", "honduras"],
    "Indonesia": ["인도네시아", "indonesia", "수마트라", "만델링"],
    "El Salvador": ["엘살바도르", "el salvador"],
}

PROCESS_PATTERNS = {
    "Natural": ["내추럴", "natural", "건식"],
    "Washed": ["워시드", "washed", "수세"],
    "Honey": ["허니", "honey", "펄프드"],
    "Anaerobic/Experimental": ["아나로빅", "무산소", "anaerobic", "인퓨즈", "발효", "코지"],
    "Decaf": ["디카페인", "decaf", "스위스워터", "슈가케인"],
}


def detect_keywords(text: str, mapping: dict[str, list[str]]) -> list[str]:
    tl = (text or "").lower()
    found = []
    for label, kws in mapping.items():
        if any(k.lower() in tl for k in kws):
            found.append(label)
    return found


def analyze_brand_positioning() -> dict[str, Any]:
    PROCESSED_BRAND_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_BEANS_PATH)
    reg = pd.read_csv(RAW_BRAND_REG_PATH)

    # Deduplicate same brand + sku_name
    df = df.drop_duplicates(subset=["brand_id", "sku_name"]).reset_index(drop=True)
    df["combined_text"] = df["sku_name"].fillna("") + " " + df["description_raw"].fillna("") + " " + df["tags_raw"].fillna("")

    # Apply 9-dimension flavor codebook
    for dim in FLAVOR_CODEBOOK:
        kws = FLAVOR_CODEBOOK[dim]
        df[f"dim_{dim}"] = df["combined_text"].apply(lambda t: int(any(k.lower() in t.lower() for k in kws)))

    df["origins_detected"] = df["combined_text"].apply(lambda t: ",".join(detect_keywords(t, ORIGIN_PATTERNS)) or "Unspecified/Blend")
    df["process_detected"] = df["combined_text"].apply(lambda t: ",".join(detect_keywords(t, PROCESS_PATTERNS)) or "Unspecified")
    df["is_single_origin"] = df["origins_detected"].apply(lambda s: int("," not in s and s != "Unspecified/Blend"))

    df["weight_g"] = pd.to_numeric(df["weight_g"], errors="coerce")
    df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
    df["price_per_100g"] = np.where(
        (df["price_krw"] > 0) & (df["weight_g"] > 0),
        (df["price_krw"] / df["weight_g"] * 100).round(0),
        np.nan,
    )

    sensory_dims = [f"dim_{d}" for d in FLAVOR_CODEBOOK if d != "감성적·추상적"]
    df["sensory_dim_count"] = df[sensory_dims].sum(axis=1)
    df["abstract_flag"] = df["dim_감성적·추상적"]

    df.to_csv(PROCESSED_BRAND_DIR / "official_brand_beans_coded.csv", index=False, encoding="utf-8-sig")

    # Brand-level summary
    dim_cols = [f"dim_{d}" for d in FLAVOR_CODEBOOK]
    agg_dict: dict[str, Any] = {
        "sku_name": "count",
        "price_per_100g": "median",
        "is_single_origin": "mean",
        "sensory_dim_count": "mean",
    }
    for dc in dim_cols:
        agg_dict[dc] = "mean"

    b_sum = df.groupby(["brand_id", "brand_name"], as_index=False).agg(agg_dict)
    b_sum = b_sum.rename(columns={"sku_name": "sku_count", "price_per_100g": "median_price_per_100g"})
    b_sum["single_origin_share_pct"] = (b_sum["is_single_origin"] * 100).round(1)
    b_sum["mean_sensory_dims"] = b_sum["sensory_dim_count"].round(2)
    for dc in dim_cols:
        b_sum[dc.replace("dim_", "pct_")] = (b_sum[dc] * 100).round(1)
        b_sum = b_sum.drop(columns=[dc])
    b_sum = b_sum.drop(columns=["is_single_origin", "sensory_dim_count"])
    b_sum = b_sum.merge(reg[["brand_id", "seoul_districts", "primary_context", "ux_notes"]], on="brand_id", how="left")
    b_sum.to_csv(OUT_DIR / "brand_positioning_summary.csv", index=False, encoding="utf-8-sig")

    overall_dim_rates = {d: round(float(df[f"dim_{d}"].mean() * 100), 1) for d in FLAVOR_CODEBOOK}

    return {
        "brand_count": int(b_sum["brand_id"].nunique()),
        "total_verified_skus": int(len(df)),
        "median_price_per_100g_krw": float(df["price_per_100g"].median()) if df["price_per_100g"].notna().any() else None,
        "overall_flavor_dimension_rates_pct": overall_dim_rates,
        "brand_summary": b_sum[
            ["brand_id", "sku_count", "median_price_per_100g", "single_origin_share_pct", "mean_sensory_dims", "pct_감성적·추상적", "primary_context"]
        ].to_dict(orient="records"),
    }


def main() -> int:
    res = analyze_brand_positioning()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
