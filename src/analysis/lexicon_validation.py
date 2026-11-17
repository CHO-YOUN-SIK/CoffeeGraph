"""Lexicon Validation & WCR Sensory Mapping Module.

Explicitly documents researcher-defined mapping rules from WCR Sensory Lexicon
categories/attributes to the 7 CoffeeGraph flavor families, Korean lexical
normalization & disambiguation rules, and brand-level detection audits
(including Center Coffee 0% text-detection verification).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
METADATA_DIR = ROOT / "data" / "metadata"
RAW_BEANS_PATH = ROOT / "data" / "raw" / "brands" / "official_brand_beans_raw.csv"

# Researcher-defined mapping from WCR Sensory Lexicon attributes -> 7 Flavor Families.
# Note: These 7 families are a researcher-constructed grouping referencing WCR/SCA,
# NOT an official "WCR 7-category" standard.
WCR_FAMILY_MAPPING_RULES: dict[str, dict[str, Any]] = {
    "Berry": {
        "wcr_category": "Fruity > Berry",
        "wcr_attributes_en": ["Blackberry", "Raspberry", "Blueberry", "Strawberry", "Cherry"],
        "broad": ["베리류", "베리", "berry"],
        "anchors": [
            "스트로베리", "블루베리", "라즈베리", "크랜베리", "블랙베리", "딸기", "체리",
            "strawberry", "blueberry", "raspberry", "blackberry", "cranberry", "cherry",
        ],
        "disambiguation_note": "Standard berry/cherry terms; no Korean homograph collision.",
    },
    "Citrus": {
        "wcr_category": "Fruity > Citrus Fruit",
        "wcr_attributes_en": ["Grapefruit", "Orange", "Lemon", "Lime"],
        "broad": ["시트러스", "감귤류", "citrus"],
        "anchors": [
            "블러드오렌지", "만다린", "오렌지", "감귤", "자몽", "레몬", "라임", "유자", "귤",
            "grapefruit", "mandarin", "orange", "lemon", "lime", "yuzu",
        ],
        "disambiguation_note": "Single-syllable '귤' guarded with Korean boundary regex.",
    },
    "Stone/Other Fruit": {
        "wcr_category": "Fruity > Other Fruit / Dried Fruit",
        "wcr_attributes_en": ["Apple", "Pear", "Peach", "Grape", "Pineapple", "Raisin", "Prune", "Fig"],
        "broad": ["열대과일", "과일향", "과일", "fruity", "fruit", "tropical"],
        "anchors": [
            "패션프루트", "청포도", "청사과", "파인애플", "복숭아", "무화과", "건과일",
            "황도", "백도", "살구", "자두", "사과", "포도", "망고", "석류", "멜론", "배",
            "dried fruit", "pineapple", "apricot", "peach", "apple", "grape", "mango", "plum", "fig", "pear",
        ],
        "disambiguation_note": "'배' strictly guarded to exclude 배송/배전/중약배전/예배/배운/재배; '청포도' consumes span before '포도'.",
    },
    "Floral": {
        "wcr_category": "Floral",
        "wcr_attributes_en": ["Floral", "Jasmine", "Rose", "Chamomile"],
        "broad": ["플로럴", "꽃향", "꽃", "floral"],
        "anchors": [
            "오렌지블라썸", "엘더플라워", "히비스커스", "캐모마일", "베르가못", "아카시아",
            "라벤더", "자스민", "재스민", "장미", "로즈", "허브",
            "chamomile", "bergamot", "lavender", "jasmine", "blossom", "rose",
        ],
        "disambiguation_note": "'꽃' guarded with Korean boundary; bergamot grouped under Floral/citrus-aromatic.",
    },
    "Nutty": {
        "wcr_category": "Nutty/Cocoa > Nutty",
        "wcr_attributes_en": ["Almond", "Hazelnut", "Peanuts"],
        "broad": ["견과류", "견과", "너티", "고소", "nutty", "nut"],
        "anchors": [
            "마카다미아", "피스타치오", "헤이즐넛", "캐슈넛", "아몬드", "호두", "땅콩", "피칸",
            "hazelnut", "almond", "walnut", "peanut", "cashew", "pecan",
        ],
        "disambiguation_note": "'고소' guarded to match adjectival/nominal forms (고소한/고소함) only.",
    },
    "Chocolate/Cocoa": {
        "wcr_category": "Nutty/Cocoa > Cocoa",
        "wcr_attributes_en": ["Cocoa", "Dark Chocolate"],
        "broad": ["초콜릿", "카카오", "코코아", "초코", "chocolate", "cacao", "cocoa"],
        "anchors": [
            "다크초콜릿", "밀크초콜릿", "화이트초콜릿", "카카오닙스", "가나슈", "모카",
            "dark chocolate", "milk chocolate", "white chocolate", "ganache", "mocha",
        ],
        "disambiguation_note": "'모카' strictly excludes '모카포트'; '다크초콜릿' consumes span before '초콜릿'.",
    },
    "Sweet/Caramel": {
        "wcr_category": "Sweet",
        "wcr_attributes_en": ["Brown Sugar", "Molasses", "Maple Syrup", "Caramelized", "Honey", "Vanilla", "Sweet Aromatics"],
        "broad": ["단맛", "달콤", "스윗", "sweetness", "sweet"],
        "anchors": [
            "버터스카치", "브라운슈가", "슈거시럽", "사탕수수", "마시멜로", "흑설탕",
            "카라멜", "캐러멜", "메이플", "달고나", "바닐라", "토피", "당밀", "허니", "꿀",
            "brown sugar", "molasses", "caramel", "vanilla", "toffee", "maple", "honey",
        ],
        "disambiguation_note": "'꿀' guarded with Korean boundary regex.",
    },
}


def export_wcr_lexicon_mapping() -> Path:
    """Export the researcher-defined WCR -> Korean/English lexicon mapping table."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = METADATA_DIR / "wcr_korean_lexicon_mapping.csv"
    rows = []
    for fam, spec in WCR_FAMILY_MAPPING_RULES.items():
        wcr_cat = spec["wcr_category"]
        wcr_attrs = ", ".join(spec["wcr_attributes_en"])
        note = spec["disambiguation_note"]
        for tier in ("broad", "anchors"):
            for term in spec[tier]:
                rows.append(
                    {
                        "flavor_family": fam,
                        "tier": "broad" if tier == "broad" else "anchor",
                        "term": term,
                        "lang": "en" if term.isascii() else "ko",
                        "wcr_reference_category": wcr_cat,
                        "wcr_reference_attributes": wcr_attrs,
                        "korean_disambiguation_rule": note,
                    }
                )
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def audit_center_coffee_zero_detection() -> dict[str, Any]:
    """Verify why Center Coffee (n=7) has 0% flavor-note detection in raw descriptions."""
    raw = pd.read_csv(RAW_BEANS_PATH)
    cc = raw[raw["brand_id"] == "center_coffee"]
    sample_descs = cc["description_raw"].fillna("").tolist()
    all_metadata_only = all(
        ("Capacity" in d or "Whole Bean" in d or "For Filter" in d or "For Espresso" in d)
        for d in sample_descs
    )
    return {
        "brand_id": "center_coffee",
        "sku_count": int(len(cc)),
        "all_descriptions_metadata_only": bool(all_metadata_only),
        "finding": (
            "Center Coffee Imweb product pages provide origin/capacity/brew-type metadata "
            "(.goods_summary) in HTML text without text tasting notes (extended info is absent or in product images)."
        ),
        "sample_description": sample_descs[0] if sample_descs else "",
    }


def main() -> int:
    p = export_wcr_lexicon_mapping()
    audit = audit_center_coffee_zero_detection()
    print("Exported WCR mapping:", p)
    print("Center Coffee audit:", audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
