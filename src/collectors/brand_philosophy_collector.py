"""Official Brand Philosophy & Sustainability Page Collector (Track C: 3D Value Space).

Collects official About, Story, Company, and Sustainability pages for the 8 CoffeeGraph
brands to measure Brand Identity along Z (Philosophical Value) and X/Y copy cues,
strictly separating nav/footer boilerplate from main body content.
"""

from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
RAW_BRAND_DIR = ROOT / "data" / "raw" / "brands"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}

BRAND_PHILOSOPHY_URLS: list[dict[str, str]] = [
    {
        "brand_id": "blue_bottle_kr",
        "brand_name": "블루보틀 코리아 (Blue Bottle)",
        "page_type": "about_and_sustainability",
        "url": "https://kr.bluebottlecoffee.com/pages/about-us",
        "extra_url": "https://kr.bluebottlecoffee.com/pages/blue-bottle-sustainability",
    },
    {
        "brand_id": "fritz",
        "brand_name": "프릳츠 커피 컴퍼니 (Fritz)",
        "page_type": "about_and_blend",
        "url": "https://fritz.co.kr/about.html?product_no=78&cate_no=46&display_group=1",
        "extra_url": "https://fritz.co.kr/about_blend.html?cate_no=45",
    },
    {
        "brand_id": "anthracite",
        "brand_name": "앤트러사이트 (Anthracite)",
        "page_type": "about",
        "url": "https://www.anthracitecoffee.com/about",
        "extra_url": "",
    },
    {
        "brand_id": "center_coffee",
        "brand_name": "센터커피 (Center Coffee)",
        "page_type": "company",
        "url": "https://centercoffee.co.kr/company",
        "extra_url": "",
    },
    {
        "brand_id": "coffee_libre",
        "brand_name": "커피리브레 (Coffee Libre)",
        "page_type": "company_and_about",
        "url": "https://www.coffeelibre.kr/shopinfo/company.html",
        "extra_url": "https://www.coffeelibre.kr/about/us.html",
    },
    {
        "brand_id": "felt_coffee",
        "brand_name": "펠트커피 (FELT Coffee)",
        "page_type": "about",
        "url": "https://feltcoffee.com/about.html",
        "extra_url": "",
    },
    {
        "brand_id": "terarosa",
        "brand_name": "테라로사 (Terarosa)",
        "page_type": "story",
        "url": "https://www.terarosa.com/contents/story/",
        "extra_url": "",
    },
    {
        "brand_id": "paul_bassett",
        "brand_name": "폴바셋 (Paul Bassett)",
        "page_type": "brand_and_csr",
        "url": "https://www.baristapaulbassett.co.kr/aboutus/brand/Identity.pb",
        "extra_url": "https://www.baristapaulbassett.co.kr/aboutus/contribution/Contribution.pb",
    },
]


def _clean_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("script, style, nav, header, footer, noscript, .cart-drawer, #CartDrawer, .drawer"):
        tag.decompose()
    main = soup.select_one("#MainContent, main, article, #contents, .contents, .sub_contents, .page-width")
    main_txt = re.sub(r"\s+", " ", main.get_text(" ", strip=True)).strip() if main else ""
    body_txt = re.sub(r"\s+", " ", (soup.body or soup).get_text(" ", strip=True)).strip()
    txt = main_txt if len(main_txt) >= 150 else body_txt
    txt = re.sub(r"^.*?로그인이 필요합니다\.\s*로그인\s*", "", txt)
    txt = re.sub(r"^.*?무료 배송 \(제주도 별도\)\s*", "", txt)
    return txt


def collect_brand_philosophy() -> list[dict[str, Any]]:
    RAW_BRAND_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []

    for item in BRAND_PHILOSOPHY_URLS:
        texts: list[str] = []
        statuses: list[int] = []
        used_urls: list[str] = []
        for u in [item["url"], item.get("extra_url", "")]:
            if not u:
                continue
            try:
                r = requests.get(u, headers=HEADERS, timeout=12)
                statuses.append(r.status_code)
                if r.status_code == 200:
                    cleaned = _clean_main_text(r.text)
                    if cleaned:
                        texts.append(cleaned)
                        used_urls.append(u)
            except requests.RequestException:
                statuses.append(0)

        combined = re.sub(r"\s+", " ", " ".join(texts)).strip()[:4000]
        rows.append(
            {
                "brand_id": item["brand_id"],
                "brand_name": item["brand_name"],
                "page_type": item["page_type"],
                "source_urls": " | ".join(used_urls) if used_urls else item["url"],
                "http_statuses": ",".join(str(s) for s in statuses),
                "text_length": len(combined),
                "philosophy_text_raw": combined,
                "collected_at_utc": ts,
            }
        )
        print(f"[philosophy] {item['brand_id']}: {len(combined)} chars (status={statuses})")

    out_path = RAW_BRAND_DIR / "official_brand_philosophy_raw.csv"
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> int:
    collect_brand_philosophy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
