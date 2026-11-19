"""Track C: 3D Brand Value Space (Practical x Sensory x Philosophical).

Computes brand-level X/Y/Z coordinates from:
  - Track A coded SKU data (`data/processed/brands/sku_flavor_language_coded.csv`)
  - Track A brand flavor fingerprint (`outputs/tables/brand_flavor_fingerprint.csv`)
  - Official brand philosophy/about/CSR pages (`data/raw/brands/official_brand_philosophy_raw.csv`)

Also exports `data/metadata/consumer_value_schema.json` defining the ingestion
schema for future Consumer Field overlays (KREI 2025, Opensurvey 2025) under
strict `Visual Juxtaposition — Not Consumer Fit` separation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PHILOSOPHY_RAW_PATH = ROOT / "data" / "raw" / "brands" / "official_brand_philosophy_raw.csv"
SKU_CODED_PATH = ROOT / "data" / "processed" / "brands" / "sku_flavor_language_coded.csv"
FINGERPRINT_PATH = ROOT / "outputs" / "tables" / "brand_flavor_fingerprint.csv"

OUT_BRANDS_CSV = ROOT / "outputs" / "tables" / "value_space_brands.csv"
OUT_SUMMARY_JSON = ROOT / "outputs" / "tables" / "value_space_summary.json"
OUT_CONSUMER_SCHEMA_JSON = ROOT / "data" / "metadata" / "consumer_value_schema.json"

CONVENIENCE_TYPES = {"drip_bag", "capsule", "subscription"}

PRACTICAL_KEYWORDS = [
    "편의", "일상", "스틱", "캡슐", "드립백", "정기구독", "구독",
    "디카페인", "가성비", "매일", "합리적", "간편", "누구나", "편하게",
]

SENSORY_KEYWORDS = [
    "향미", "산미", "로스팅", "커핑", "풍미", "테이스팅", "추출",
    "스페셜티", "품질", "바디", "단맛", "플레이버", "아로마", "에스프레소", "싱글오리진",
]

PHILOSOPHY_KEYWORDS = [
    "직거래", "다이렉트 트레이드", "direct trade", "농장", "산지", "생산자",
    "지속가능", "지속 가능", "친환경", "윤리", "공정", "철학", "장인",
    "사회공헌", "csr", "탄소", "기후", "재활용", "생두", "비콥", "b corp",
    "후원", "상생", "재생", "지역사회", "공간재생", "가치", "책임",
]

# Boilerplate patterns observed in scraped e-commerce/nav pages so Z reflects
# actual brand narrative/CSR disclosure rather than shopping cart/footer text.
BOILERPLATE_PATTERNS = [
    r"Size infomation.*?닫기",
    r"고액결제의 경우.*?결제 완료 될 때 까지 닫지 마시기 바랍니다\.",
    r"로그인\s+회원가입\s+주문확인.*?APP 다운 안드로이드 iOS",
    r"SHOP\s+COFFEE\s+ESPRESSO.*?English\s+닫기",
    r"본문 바로가기\s+메뉴 바로가기.*?납품문의",
    r"개인정보처리방침.*?All rights reserved\.\s*페이스북\s*인스타그램\s*유튜브",
    r"현재 위치\s+홈\s+회사소개",
    r"선택을 누르면 전체 페이지가 새로 고쳐집니다\.\s*새 창에서 열립니다\.\s*0?",
    r"\{#html\}.*?DIRECT TRADE \(해외배송 가능상품\)\s*0\s*0\.00\s*QUANTITY\s*BUY NOW\s*ADD TO CART\s*SOLD OUT",
    r"©\s*20\d{2}.*?(?:ALL RIGHT RESERVED\.|All rights reserved\.)",
]


def clean_philosophy_text(raw: str) -> str:
    """Strip common e-commerce/navigation boilerplate from scraped official pages."""
    if not isinstance(raw, str):
        return ""
    text = raw
    for pat in BOILERPLATE_PATTERNS:
        text = re.sub(pat, " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_keyword_hits(text: str, keywords: list[str]) -> tuple[int, list[str]]:
    """Count distinct keyword matches (case-insensitive) and return matched list."""
    if not text:
        return 0, []
    lower = text.lower()
    matched = [kw for kw in keywords if kw.lower() in lower]
    return len(matched), matched


def minmax_scale(series: pd.Series, invert: bool = False) -> pd.Series:
    """Min-max scale a numeric series to [0, 100], preserving NaNs."""
    valid = series.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=series.index)
    lo, hi = float(valid.min()), float(valid.max())
    if np.isclose(hi, lo):
        scaled = pd.Series(50.0, index=series.index)
        scaled[series.isna()] = np.nan
        return scaled
    scaled = (series - lo) / (hi - lo) * 100.0
    if invert:
        scaled = 100.0 - scaled
    return scaled


def classify_z_disclosure(clean_len: int, phil_hits: int) -> str:
    """Explicitly separate disclosure richness from philosophical absence."""
    if clean_len >= 1000 and phil_hits >= 8:
        return "Rich Disclosure"
    if clean_len >= 400 and phil_hits >= 2:
        return "Moderate Disclosure"
    return "Minimal / Unstated"


def build_consumer_value_schema() -> dict[str, Any]:
    """Define ingestion schema for future KREI 2025 & Opensurvey 2025 overlays."""
    return {
        "schema_version": "1.0.0",
        "purpose": "Track C Consumer Field X/Y/Z overlay specification",
        "epistemological_rule": "Visual Juxtaposition Only — Not Consumer-Brand Fit",
        "dimensions": {
            "x_practical": {
                "label": "Practical Value (실용적 가치)",
                "krei_2025_indicators": [
                    "가격/가성비 중시 응답 비중",
                    "구매 편의성·접근성 중시 응답 비중",
                    "RTD/캡슐/스틱/드립백 등 간편형 커피 구매 빈도",
                ],
                "opensurvey_2025_indicators": [
                    "가성비·프로모션·쿠폰 기반 브랜드 선택 비중",
                    "접근성·주문 편의성(사이렌오더/배달/DT) 이용률",
                ],
                "scale": "[0, 100] normalized composite",
            },
            "y_sensory": {
                "label": "Sensory Value (감각적 가치)",
                "krei_2025_indicators": [
                    "맛·향·품질 중시 응답 비중",
                    "원두/스페셜티 커피 선호 비중",
                ],
                "opensurvey_2025_indicators": [
                    "원두/산미/디카페인 등 커스터마이징 이용률 (2025 공개 요약: 80%)",
                    "커피 맛·향미 전문성 기반 브랜드 선택 비중",
                ],
                "scale": "[0, 100] normalized composite",
            },
            "z_philosophical": {
                "label": "Philosophical Value (철학적·윤리적 가치)",
                "krei_2025_indicators": [
                    "친환경·윤리적 소비·공정무역 고려 비중",
                    "원산지/생산이력 확인 비중",
                ],
                "opensurvey_2025_indicators": [
                    "브랜드 철학·지속가능성·친환경 캠페인 공감/선택 비중",
                ],
                "scale": "[0, 100] normalized composite",
            },
        },
        "source_registry": [
            {
                "source_id": "krei_food_survey_2025",
                "name": "KREI 식품소비행태조사 2025",
                "access_mode": "manual_excel_download",
                "url": "https://www.krei.re.kr/foodSurvey/page/460?cmd=view&pst=505133",
                "license_restriction": "Non-commercial / No-derivative; do not redistribute raw microdata",
                "status": "awaiting_local_excel_drop",
                "expected_drop_path": "data/external/krei_2025/",
            },
            {
                "source_id": "opensurvey_cafe_trend_2025",
                "name": "오픈서베이 카페 트렌드 리포트 2025",
                "access_mode": "public_summary_and_gated_pdf",
                "url": "https://blog.opensurvey.co.kr/trendreport/cafe-2025/",
                "sample_note": "n=2,000 national (20-59) + 200x6 franchise users (Nov 2025)",
                "license_restriction": "No redistribution of full report/raw tables; cite aggregate metrics only",
                "status": "public_summary_audited",
            },
        ],
    }


def compute_brand_value_space() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compute X/Y/Z Brand Identity coordinates for all 8 CoffeeGraph brands."""
    phil_df = pd.read_csv(PHILOSOPHY_RAW_PATH)
    sku_df = pd.read_csv(SKU_CODED_PATH)
    fp_df = pd.read_csv(FINGERPRINT_PATH)

    # 1. Aggregate SKU-level practical indicators per brand
    sku_agg_rows: list[dict[str, Any]] = []
    for brand_id, grp in sku_df.groupby("brand_id"):
        total = len(grp)
        conv_cnt = int(grp["product_type_std"].isin(CONVENIENCE_TYPES).sum())
        conv_pct = round(conv_cnt / total * 100.0, 2) if total else 0.0
        sku_text = " ".join(
            grp["sku_name"].fillna("").astype(str)
            + " "
            + grp["description_raw"].fillna("").astype(str)
            + " "
            + grp["tags_raw"].fillna("").astype(str)
        )
        sku_prac_hits, sku_prac_kw = count_keyword_hits(sku_text, PRACTICAL_KEYWORDS)
        sku_agg_rows.append(
            {
                "brand_id": brand_id,
                "convenience_sku_count": conv_cnt,
                "convenience_sku_pct": conv_pct,
                "sku_practical_hits": sku_prac_hits,
                "sku_practical_keywords": ", ".join(sku_prac_kw),
            }
        )
    sku_agg = pd.DataFrame(sku_agg_rows)

    # 2. Merge fingerprint + philosophy + SKU aggregates
    df = fp_df[
        [
            "brand_id",
            "brand_name",
            "brand_segment",
            "sku_count",
            "whole_bean_count",
            "flavor_detected_pct",
            "median_whole_bean_price_per_100g",
            "mean_sensory_specificity",
        ]
    ].merge(phil_df[["brand_id", "page_type", "source_urls", "text_length", "philosophy_text_raw"]], on="brand_id", how="left")
    df = df.merge(sku_agg, on="brand_id", how="left")

    # 3. Clean philosophy text & count domain keywords
    df["philosophy_clean_text"] = df["philosophy_text_raw"].fillna("").map(clean_philosophy_text)
    df["philosophy_clean_length"] = df["philosophy_clean_text"].str.len()

    prac_phil_hits, sens_phil_hits, phil_hits, phil_kw_lists = [], [], [], []
    for txt in df["philosophy_clean_text"]:
        p_cnt, _ = count_keyword_hits(txt, PRACTICAL_KEYWORDS)
        s_cnt, _ = count_keyword_hits(txt, SENSORY_KEYWORDS)
        z_cnt, z_kws = count_keyword_hits(txt, PHILOSOPHY_KEYWORDS)
        prac_phil_hits.append(p_cnt)
        sens_phil_hits.append(s_cnt)
        phil_hits.append(z_cnt)
        phil_kw_lists.append(", ".join(z_kws))

    df["phil_practical_hits"] = prac_phil_hits
    df["phil_sensory_hits"] = sens_phil_hits
    df["philosophy_keyword_hits"] = phil_hits
    df["philosophy_keywords_matched"] = phil_kw_lists
    df["total_practical_hits"] = df["sku_practical_hits"].fillna(0) + df["phil_practical_hits"]

    # 4. Compute normalized X (Practical), Y (Sensory), Z (Philosophical)
    # X: 50% convenience SKU share + 30% price accessibility (inverted 100g price) + 20% practical keywords
    x_conv = minmax_scale(df["convenience_sku_pct"])
    x_price = minmax_scale(df["median_whole_bean_price_per_100g"], invert=True)
    x_kw = minmax_scale(df["total_practical_hits"].astype(float))

    # If whole-bean price is undisclosed (e.g. Paul Bassett), reweight remaining X components cleanly
    x_scores = []
    for idx in df.index:
        if pd.isna(x_price.loc[idx]):
            score = (0.50 * x_conv.loc[idx] + 0.20 * x_kw.loc[idx]) / 0.70
        else:
            score = 0.50 * x_conv.loc[idx] + 0.30 * x_price.loc[idx] + 0.20 * x_kw.loc[idx]
        x_scores.append(round(float(score), 2))
    df["x_practical"] = x_scores
    df["price_disclosed"] = df["median_whole_bean_price_per_100g"].notna()

    # Y: 50% mean_sensory_specificity + 30% flavor_detected_pct + 20% official sensory keywords
    y_spec = minmax_scale(df["mean_sensory_specificity"])
    y_det = minmax_scale(df["flavor_detected_pct"])
    y_kw = minmax_scale(df["phil_sensory_hits"].astype(float))
    df["y_sensory"] = (0.50 * y_spec + 0.30 * y_det + 0.20 * y_kw).round(2)

    # Z: 60% philosophy keyword hits + 40% log-scaled clean philosophy text length
    z_kw = minmax_scale(df["philosophy_keyword_hits"].astype(float))
    z_len = minmax_scale(np.log1p(df["philosophy_clean_length"].astype(float)))
    df["z_philosophical"] = (0.60 * z_kw + 0.40 * z_len).round(2)

    df["z_disclosure_tier"] = [
        classify_z_disclosure(int(cl), int(kh))
        for cl, kh in zip(df["philosophy_clean_length"], df["philosophy_keyword_hits"])
    ]

    # Select clean output columns (omit huge raw text blob in table)
    out_cols = [
        "brand_id",
        "brand_name",
        "brand_segment",
        "sku_count",
        "whole_bean_count",
        "convenience_sku_count",
        "convenience_sku_pct",
        "median_whole_bean_price_per_100g",
        "price_disclosed",
        "mean_sensory_specificity",
        "flavor_detected_pct",
        "text_length",
        "philosophy_clean_length",
        "total_practical_hits",
        "phil_sensory_hits",
        "philosophy_keyword_hits",
        "z_disclosure_tier",
        "x_practical",
        "y_sensory",
        "z_philosophical",
        "philosophy_keywords_matched",
        "source_urls",
    ]
    out_df = df[out_cols].sort_values("z_philosophical", ascending=False).reset_index(drop=True)

    summary = {
        "track": "Track C — 3D Brand Value Space",
        "brand_count": int(len(out_df)),
        "axes": {
            "x_practical": "Practical Value (convenience SKU share, price accessibility, practical language)",
            "y_sensory": "Sensory Value (Track A sensory specificity, flavor detection rate, sensory narrative)",
            "z_philosophical": "Philosophical Value (official sustainability/direct-trade/craft disclosure & keywords)",
        },
        "disclosure_tiers": out_df["z_disclosure_tier"].value_counts().to_dict(),
        "epistemological_note": (
            "Brand Identity coordinates reflect publicly disclosed product & official page signals only. "
            "Minimal/Unstated Z tiers indicate low public web disclosure, not absence of brand philosophy. "
            "Future Consumer Field overlays (KREI 2025 / Opensurvey 2025) represent Visual Juxtaposition only."
        ),
        "brands": out_df[
            ["brand_id", "brand_name", "x_practical", "y_sensory", "z_philosophical", "z_disclosure_tier"]
        ].to_dict(orient="records"),
    }
    return out_df, summary


def main() -> None:
    OUT_BRANDS_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_CONSUMER_SCHEMA_JSON.parent.mkdir(parents=True, exist_ok=True)

    out_df, summary = compute_brand_value_space()
    out_df.to_csv(OUT_BRANDS_CSV, index=False, encoding="utf-8-sig")
    OUT_SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_CONSUMER_SCHEMA_JSON.write_text(
        json.dumps(build_consumer_value_schema(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Saved {OUT_BRANDS_CSV} ({len(out_df)} brands)")
    print(f"Saved {OUT_SUMMARY_JSON}")
    print(f"Saved {OUT_CONSUMER_SCHEMA_JSON}")
    print(
        out_df[
            ["brand_id", "x_practical", "y_sensory", "z_philosophical", "z_disclosure_tier"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
