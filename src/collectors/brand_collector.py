"""Phase 5 (M5): Official Brand & Bean SKU Collector.

Collects verified coffee bean product records directly from official brand
online stores (distinguishing official_online_mall SKUs from store_menu SKUs)
for brands operating in Seoul's key market contexts.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

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

BRAND_REGISTRY = [
    {
        "brand_id": "blue_bottle_kr",
        "brand_name": "블루보틀 코리아 (Blue Bottle Korea)",
        "official_url": "https://kr.bluebottlecoffee.com",
        "catalog_url": "https://kr.bluebottlecoffee.com/products.json?limit=250",
        "seoul_districts": "성동구,종로구,강남구,용산구,영등포구",
        "primary_context": "주말·방문형 / 오피스·복합형",
        "platform": "shopify",
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "블렌드/싱글오리진 분류, 로스트·향미·산미 필터 및 브루잉 가이드 제공",
    },
    {
        "brand_id": "fritz",
        "brand_name": "프릳츠 커피 컴퍼니 (Fritz)",
        "official_url": "https://fritz.co.kr",
        "catalog_url": "https://fritz.co.kr/product/list.html?cate_no=24",
        "seoul_districts": "마포구,종로구,서초구",
        "primary_context": "주말·방문형 / 모닝·복합형",
        "platform": "cafe24",
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "원두 상세 내 컵노트·산지·가공법·배전도 서술 및 캐릭터 브랜딩 중심",
    },
    {
        "brand_id": "anthracite",
        "brand_name": "앤트러사이트 (Anthracite)",
        "official_url": "https://www.anthracitecoffee.com",
        "catalog_url": "https://www.anthracitecoffee.com/shop",
        "seoul_districts": "마포구,용산구,서대문구",
        "primary_context": "주말·방문형 / 감성·복합형",
        "platform": "imweb",
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "문학적·감성적 제품명(공기와 꿈, 나쓰메 소세키 등)과 공간 서사 결합",
    },
    {
        "brand_id": "center_coffee",
        "brand_name": "센터커피 (Center Coffee)",
        "official_url": "https://centercoffee.co.kr",
        "catalog_url": "https://centercoffee.co.kr/shop",
        "seoul_districts": "성동구,강남구,중구",
        "primary_context": "오피스·점심 집중형 / 주말·방문형",
        "platform": "imweb",
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "산지·품종·가공법·커핑 노트 중심의 스페셜티 스펙 제시",
    },
    {
        "brand_id": "coffee_libre",
        "brand_name": "커피리브레 (Coffee Libre)",
        "official_url": "https://www.coffeelibre.kr",
        "catalog_url": "https://www.coffeelibre.kr/product/list.html?cate_no=48",
        "seoul_districts": "마포구,영등포구,중구",
        "primary_context": "오피스·점심 집중형 / 주말·방문형",
        "platform": "cafe24",
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "싱글오리진·블렌드·디카페인 세분화 및 농장·가공법 정보 상세 제공",
    },
    {
        "brand_id": "felt_coffee",
        "brand_name": "펠트커피 (FELT Coffee)",
        "official_url": "https://feltcoffee.com",
        "catalog_url": "https://feltcoffee.com/category/shop/30/",
        "seoul_districts": "종로구,강남구,서대문구",
        "primary_context": "오피스·점심 집중형 / 모닝·복합형",
        "platform": "cafe24",
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "게이샤·마이크로랏 등 하이엔드 싱글오리진 및 간결한 테이스팅 노트",
    },
    {
        "brand_id": "terarosa",
        "brand_name": "테라로사 (Terarosa)",
        "official_url": "https://www.terarosa.com",
        "catalog_url": "https://www.terarosa.com/product/list/?category=79",
        "seoul_districts": "종로구,강남구,서초구",
        "primary_context": "오피스·점심 집중형 / 복합형",
        "platform": "terarosa",
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "산지·가공·향미 노트 및 추출 레시피 기반 탐색 구조",
    },
]


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_price(text: str) -> int | None:
    m = re.search(r"(\d{1,3}(?:,\d{3})+|\d{4,6})\s*원?", text or "")
    if not m:
        return None
    val = int(m.group(1).replace(",", ""))
    return val if 3000 <= val <= 500000 else None


def extract_weight_g(text: str) -> int | None:
    m_kg = re.search(r"(\d+(?:\.\d+)?)\s*kg", text or "", re.I)
    if m_kg:
        return int(float(m_kg.group(1)) * 1000)
    m_g = re.search(r"(\d{2,4})\s*g\b", text or "", re.I)
    if m_g:
        w = int(m_g.group(1))
        return w if 50 <= w <= 5000 else None
    return None


def is_non_bean_item(title: str) -> bool:
    skip_kw = [
        "머그", "텀블러", "드리퍼", "필터", "서버", "그라인더", "글라스", "에코백",
        "티셔츠", "굿즈", "스티커", "책", "도서", "포스터", "케틀", "포트", "gift",
        "mug", "tumbler", "dripper", "filter", "bag", "tote", "glass", "초콜릿",
        "쿠키", "그래놀라", "우유", "시럽", "선물세트", "배송", "정기구독", "티백",
    ]
    tl = title.lower()
    return any(k in tl for k in skip_kw)


def collect_blue_bottle(brand: dict[str, Any], ts: str) -> list[dict[str, Any]]:
    r = requests.get(brand["catalog_url"], headers=HEADERS, timeout=15)
    r.raise_for_status()
    products = r.json().get("products", [])
    rows: list[dict[str, Any]] = []
    for p in products:
        title = clean_text(p.get("title", ""))
        ptype = clean_text(p.get("product_type", ""))
        tags = ",".join(p.get("tags", [])) if isinstance(p.get("tags"), list) else str(p.get("tags", ""))
        if is_non_bean_item(title) or ("원두" not in ptype and "Coffee" not in ptype and "커피" not in title and "g" not in title.lower()):
            if "원두" not in tags and "블렌드" not in title and "싱글" not in title and "디카페인" not in title:
                continue
        body = BeautifulSoup(p.get("body_html") or "", "html.parser").get_text(" ", strip=True)
        variants = p.get("variants", [])
        price = None
        weight_g = extract_weight_g(title + " " + body)
        if variants:
            try:
                price = int(float(variants[0].get("price", 0)))
            except (ValueError, TypeError):
                price = None
            if weight_g is None and variants[0].get("grams"):
                g_val = int(variants[0]["grams"])
                if 50 <= g_val <= 5000:
                    weight_g = g_val
        rows.append(
            {
                "brand_id": brand["brand_id"],
                "brand_name": brand["brand_name"],
                "channel_type": "official_online_mall",
                "sku_name": title,
                "product_url": f"https://kr.bluebottlecoffee.com/products/{p.get('handle', '')}",
                "price_krw": price,
                "weight_g": weight_g or 200,
                "description_raw": clean_text(body)[:800],
                "tags_raw": tags,
                "collected_at_utc": ts,
            }
        )
    return rows


def collect_html_brand(brand: dict[str, Any], ts: str, max_items: int = 22) -> list[dict[str, Any]]:
    r = requests.get(brand["catalog_url"], headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(pat in href for pat in ["product/detail.html", "/product/", "/shop/?idx="]):
            if "board" in href or "cart" in href:
                continue
            full = urljoin(brand["official_url"], href)
            if full not in seen_urls:
                seen_urls.add(full)
                txt = clean_text(a.get_text(" ", strip=True))
                if not txt:
                    img = a.find("img", alt=True)
                    if img:
                        txt = clean_text(img["alt"])
                links.append((full, txt))

    rows: list[dict[str, Any]] = []
    for url, link_title in links[:max_items]:
        try:
            pr = requests.get(url, headers=HEADERS, timeout=10)
            if pr.status_code != 200:
                continue
            psoup = BeautifulSoup(pr.text, "html.parser")
            og_title = psoup.find("meta", property="og:title")
            title = clean_text(og_title["content"]) if og_title and og_title.get("content") else clean_text(psoup.title.get_text() if psoup.title else "")
            title = re.sub(r"\s*[-|:]\s*(프릳츠|앤트러사이트|센터커피|커피리브레|펠트|테라로사).*$", "", title).strip()
            generic_names = {"프릳츠커피컴퍼니", "펠트커피", "펠트", "테라로사", "커피리브레", "앤트러사이트", "센터커피", ""}
            if title in generic_names or len(title) < 2:
                title = link_title
            if not title or is_non_bean_item(title):
                continue

            og_desc = psoup.find("meta", property="og:description")
            meta_desc = clean_text(og_desc["content"]) if og_desc and og_desc.get("content") else ""
            # Extract main text snippet
            body_text = clean_text(psoup.get_text(" ", strip=True))
            price = extract_price(body_text[:4000])
            weight_g = extract_weight_g(title + " " + meta_desc + " " + body_text[:2500])

            # Keep meaningful snippet around tasting notes / origin if available
            desc_combined = clean_text(f"{meta_desc} {body_text[:1200]}")[:800]
            rows.append(
                {
                    "brand_id": brand["brand_id"],
                    "brand_name": brand["brand_name"],
                    "channel_type": "official_online_mall",
                    "sku_name": title,
                    "product_url": url,
                    "price_krw": price,
                    "weight_g": weight_g,
                    "description_raw": desc_combined,
                    "tags_raw": "",
                    "collected_at_utc": ts,
                }
            )
        except requests.RequestException:
            continue
    return rows


def collect_all_brands() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    RAW_BRAND_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    all_rows: list[dict[str, Any]] = []

    for brand in BRAND_REGISTRY:
        print(f"[brand_collector] Collecting {brand['brand_id']}...")
        try:
            if brand["platform"] == "shopify":
                rows = collect_blue_bottle(brand, ts)
            else:
                rows = collect_html_brand(brand, ts)
            print(f"[brand_collector] OK {brand['brand_id']}: {len(rows)} bean SKUs")
            all_rows.extend(rows)
        except Exception as exc:
            print(f"[brand_collector] WARN {brand['brand_id']}: {exc}")

    # Save brand registry
    reg_path = RAW_BRAND_DIR / "official_brand_registry.csv"
    with reg_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(BRAND_REGISTRY[0].keys()))
        writer.writeheader()
        writer.writerows(BRAND_REGISTRY)

    # Save raw bean SKUs
    raw_path = RAW_BRAND_DIR / "official_brand_beans_raw.csv"
    if all_rows:
        with raw_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)

    return BRAND_REGISTRY, all_rows


def main() -> int:
    _, rows = collect_all_brands()
    print(f"Total official bean SKUs collected: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
