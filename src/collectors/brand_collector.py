"""Phase 5 (M5): Official Brand & Bean SKU Collector (Refined).

Collects verified coffee bean product records directly from official brand
online stores (distinguishing official_online_mall SKUs from store_menu SKUs)
for 7 Seoul specialty roasters + 1 mass/premium franchise reference (Paul Bassett).
"""

from __future__ import annotations

import csv
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
        "brand_name": "블루보틀 코리아 (Blue Bottle)",
        "brand_segment": "Global Specialty",
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
        "brand_segment": "Specialty Roaster",
        "official_url": "https://fritz.co.kr",
        "catalog_url": "https://fritz.co.kr/product/list.html?cate_no=24",
        "extra_catalog_urls": "https://fritz.co.kr/product/list.html?cate_no=25",
        "seoul_districts": "마포구,종로구,서초구",
        "primary_context": "주말·방문형 / 모닝·복합형",
        "platform": "cafe24_list",
        "default_weight_g": 200,
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "원두 상세 내 컵노트·산지·가공법·배전도 서술 및 캐릭터 브랜딩 중심",
    },
    {
        "brand_id": "anthracite",
        "brand_name": "앤트러사이트 (Anthracite)",
        "brand_segment": "Specialty Roaster",
        "official_url": "https://www.anthracitecoffee.com",
        "catalog_url": "https://www.anthracitecoffee.com/shop",
        "seoul_districts": "마포구,용산구,서대문구",
        "primary_context": "주말·방문형 / 감성·복합형",
        "platform": "imweb",
        "default_weight_g": 200,
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "문학적·감성적 제품명(공기와 꿈, 나쓰메 소세키 등)과 공간 서사 결합",
    },
    {
        "brand_id": "center_coffee",
        "brand_name": "센터커피 (Center Coffee)",
        "brand_segment": "Specialty Roaster",
        "official_url": "https://centercoffee.co.kr",
        "catalog_url": "https://centercoffee.co.kr/shop",
        "seoul_districts": "성동구,강남구,중구",
        "primary_context": "오피스·점심 집중형 / 주말·방문형",
        "platform": "imweb",
        "default_weight_g": 200,
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "산지·품종·가공법·커핑 노트 중심의 스페셜티 스펙 제시",
    },
    {
        "brand_id": "coffee_libre",
        "brand_name": "커피리브레 (Coffee Libre)",
        "brand_segment": "Specialty Roaster",
        "official_url": "https://www.coffeelibre.kr",
        "catalog_url": "https://www.coffeelibre.kr/product/list.html?cate_no=47",
        "seoul_districts": "마포구,영등포구,중구",
        "primary_context": "오피스·점심 집중형 / 주말·방문형",
        "platform": "cafe24_list",
        "default_weight_g": 200,
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "싱글오리진·블렌드·디카페인 세분화 및 농장·가공법·배전도 상세 제공",
    },
    {
        "brand_id": "felt_coffee",
        "brand_name": "펠트커피 (FELT Coffee)",
        "brand_segment": "Specialty Roaster",
        "official_url": "https://feltcoffee.com",
        "catalog_url": "https://feltcoffee.com/category/shop/30/",
        "seoul_districts": "종로구,강남구,서대문구",
        "primary_context": "오피스·점심 집중형 / 모닝·복합형",
        "platform": "cafe24_list",
        "default_weight_g": 200,
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "게이샤·마이크로랏 등 하이엔드 싱글오리진 및 간결한 영문 테이스팅 노트",
    },
    {
        "brand_id": "terarosa",
        "brand_name": "테라로사 (Terarosa)",
        "brand_segment": "Specialty Roaster",
        "official_url": "https://www.terarosa.com",
        "catalog_url": "https://www.terarosa.com/product/list/?category=79",
        "seoul_districts": "종로구,강남구,서초구",
        "primary_context": "오피스·점심 집중형 / 복합형",
        "platform": "terarosa_list",
        "default_weight_g": 250,
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "산지·가공·향미 노트 및 추출 레시피 기반 탐색 구조",
    },
    {
        "brand_id": "paul_bassett",
        "brand_name": "폴바셋 (Paul Bassett)",
        "brand_segment": "Franchise Reference",
        "official_url": "https://www.baristapaulbassett.co.kr",
        "catalog_url": "https://www.baristapaulbassett.co.kr/menu/List.pb?cid1=E",
        "seoul_districts": "강남구,서초구,종로구,중구,영등포구,마포구,용산구,송파구",
        "primary_context": "오피스·점심 집중형 / 복합형",
        "platform": "paul_bassett",
        "default_weight_g": 200,
        "operational_status": "ACTIVE_VERIFIED",
        "ux_notes": "시그니처 블렌드·스틱/캡슐·드립백 중심의 직관적 대중 탐색 구조",
    },
]


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_price(text: str) -> int | None:
    prices = [int(m.replace(",", "")) for m in re.findall(r"(\d{1,3}(?:,\d{3})+|\d{4,6})\s*원", text or "")]
    valid = [p for p in prices if 4000 <= p <= 200000]
    return valid[0] if valid else None


def extract_weight_g(text: str) -> int | None:
    m_kg = re.search(r"(\d+(?:\.\d+)?)\s*kg", text or "", re.I)
    if m_kg:
        w = int(float(m_kg.group(1)) * 1000)
        return w if 50 <= w <= 5000 else None
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
        "캡슐", "인스턴트", "콜드브루", "파우치", "케이스", "스푼", "에스프레소 잔",
        "보온", "컵", "아이스", "라떼베이스",
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
        if is_non_bean_item(title):
            continue
        if "원두" not in ptype and "Coffee" not in ptype and "블렌드" not in title and "싱글" not in title and "디카페인" not in title:
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


def collect_cafe24_list(brand: dict[str, Any], ts: str) -> list[dict[str, Any]]:
    urls = [brand["catalog_url"]]
    if brand.get("extra_catalog_urls"):
        urls.extend([u.strip() for u in brand["extra_catalog_urls"].split(",") if u.strip()])

    rows: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for cat_url in urls:
        r = requests.get(cat_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select('li[id^="anchorBoxId_"], .prdList > li')
        for it in items:
            raw_txt = clean_text(it.get_text(" ", strip=True))
            # Extract Korean product name if Cafe24 labels exist, else anchor text
            name_el = it.select_one(".name a, .prdName a, strong.name a, p.name a")
            title = clean_text(name_el.get_text(" ", strip=True)) if name_el else ""
            title = re.sub(r"^상품명\s*:\s*", "", title).strip()
            if not title or len(title) < 2:
                m_name = re.search(r"상품명\s*:\s*([^판매가]+?)(?:판매가|상품간략설명|$)", raw_txt)
                if m_name:
                    title = clean_text(m_name.group(1))
            if not title or is_non_bean_item(title) or title in seen_titles:
                continue
            seen_titles.add(title)

            a_el = it.find("a", href=True)
            prod_url = urljoin(brand["official_url"], a_el["href"]) if a_el else cat_url
            price = extract_price(raw_txt)
            weight_g = extract_weight_g(title + " " + raw_txt) or brand.get("default_weight_g", 200)
            rows.append(
                {
                    "brand_id": brand["brand_id"],
                    "brand_name": brand["brand_name"],
                    "channel_type": "official_online_mall",
                    "sku_name": title,
                    "product_url": prod_url,
                    "price_krw": price,
                    "weight_g": weight_g,
                    "description_raw": raw_txt[:800],
                    "tags_raw": "",
                    "collected_at_utc": ts,
                }
            )
    return rows


def collect_terarosa_list(brand: dict[str, Any], ts: str, max_items: int = 25) -> list[dict[str, Any]]:
    r = requests.get(brand["catalog_url"], headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rows: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for a in soup.find_all("a", href=True):
        if "ItemCode=" not in a["href"]:
            continue
        title = clean_text(a.get_text(" ", strip=True))
        if not title or len(title) < 3 or is_non_bean_item(title) or title in seen_titles:
            continue
        seen_titles.add(title)
        prod_url = urljoin(brand["official_url"], a["href"])
        parent_txt = clean_text(a.parent.parent.get_text(" ", strip=True)) if a.parent and a.parent.parent else title
        price = extract_price(parent_txt)
        weight_g = extract_weight_g(title + " " + parent_txt) or brand.get("default_weight_g", 250)

        # Fetch detail page using ItemCode if needed for tasting notes
        desc = parent_txt
        try:
            dr = requests.get(prod_url, headers=HEADERS, timeout=8)
            if dr.status_code == 200:
                ds = BeautifulSoup(dr.text, "html.parser")
                dtxt = clean_text(ds.get_text(" ", strip=True))
                if price is None:
                    price = extract_price(dtxt[:4000])
                desc = f"{title} {dtxt[:1200]}"
        except requests.RequestException:
            pass

        rows.append(
            {
                "brand_id": brand["brand_id"],
                "brand_name": brand["brand_name"],
                "channel_type": "official_online_mall",
                "sku_name": title,
                "product_url": prod_url,
                "price_krw": price,
                "weight_g": weight_g,
                "description_raw": clean_text(desc)[:800],
                "tags_raw": "",
                "collected_at_utc": ts,
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def collect_imweb_brand(brand: dict[str, Any], ts: str, max_items: int = 20) -> list[dict[str, Any]]:
    r = requests.get(brand["catalog_url"], headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for a in soup.find_all("a", href=True):
        if "/shop/?idx=" not in a["href"]:
            continue
        full = urljoin(brand["official_url"], a["href"])
        if full not in seen_urls:
            seen_urls.add(full)
            links.append((full, clean_text(a.get_text(" ", strip=True))))

    rows: list[dict[str, Any]] = []
    for url, link_title in links[:max_items]:
        try:
            pr = requests.get(url, headers=HEADERS, timeout=10)
            if pr.status_code != 200:
                continue
            psoup = BeautifulSoup(pr.text, "html.parser")
            og_title = psoup.find("meta", property="og:title")
            title = clean_text(og_title["content"]) if og_title and og_title.get("content") else link_title
            title = re.sub(r"\s*[-|:]\s*(앤트러사이트|센터커피).*$", "", title).strip() or link_title
            if not title or is_non_bean_item(title):
                continue
            og_desc = psoup.find("meta", property="og:description")
            meta_desc = clean_text(og_desc["content"]) if og_desc and og_desc.get("content") else ""
            body_text = clean_text(psoup.get_text(" ", strip=True))
            price = extract_price(body_text[:4000])
            weight_g = extract_weight_g(title + " " + meta_desc + " " + body_text[:2500]) or brand.get("default_weight_g", 200)
            rows.append(
                {
                    "brand_id": brand["brand_id"],
                    "brand_name": brand["brand_name"],
                    "channel_type": "official_online_mall",
                    "sku_name": title,
                    "product_url": url,
                    "price_krw": price,
                    "weight_g": weight_g,
                    "description_raw": clean_text(f"{meta_desc} {body_text[:1200]}")[:800],
                    "tags_raw": "",
                    "collected_at_utc": ts,
                }
            )
        except requests.RequestException:
            continue
    return rows


def collect_paul_bassett(brand: dict[str, Any], ts: str, max_items: int = 20) -> list[dict[str, Any]]:
    r = requests.get(brand["catalog_url"], headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for a in soup.select("ul.listStyleA li a, .menuList li a, .list li a"):
        title = clean_text(a.get_text(" ", strip=True))
        if not title or title in seen or len(title) < 3:
            continue
        if any(k in title.lower() for k in ["스틱", "텀블러", "머그", "보온"]):
            continue
        seen.add(title)
        prod_url = urljoin(brand["official_url"], a.get("href", ""))
        desc = title
        if "View.pb" in prod_url:
            try:
                dr = requests.get(prod_url, headers=HEADERS, timeout=8)
                if dr.status_code == 200:
                    ds = BeautifulSoup(dr.text, "html.parser")
                    desc = clean_text(ds.get_text(" ", strip=True))[:800]
            except requests.RequestException:
                pass
        rows.append(
            {
                "brand_id": brand["brand_id"],
                "brand_name": brand["brand_name"],
                "channel_type": "official_online_catalog",
                "sku_name": title,
                "product_url": prod_url,
                "price_krw": extract_price(desc),
                "weight_g": extract_weight_g(title + " " + desc) or 200,
                "description_raw": desc[:800],
                "tags_raw": "FranchiseReference",
                "collected_at_utc": ts,
            }
        )
        if len(rows) >= max_items:
            break
    return rows


def collect_all_brands() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    RAW_BRAND_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    all_rows: list[dict[str, Any]] = []

    for brand in BRAND_REGISTRY:
        print(f"[brand_collector] Collecting {brand['brand_id']}...", flush=True)
        try:
            plat = brand["platform"]
            if plat == "shopify":
                rows = collect_blue_bottle(brand, ts)
            elif plat == "cafe24_list":
                rows = collect_cafe24_list(brand, ts)
            elif plat == "terarosa_list":
                rows = collect_terarosa_list(brand, ts)
            elif plat == "imweb":
                rows = collect_imweb_brand(brand, ts)
            elif plat == "paul_bassett":
                rows = collect_paul_bassett(brand, ts)
            else:
                rows = []
            print(f"[brand_collector] OK {brand['brand_id']}: {len(rows)} bean SKUs", flush=True)
            all_rows.extend(rows)
        except Exception as exc:
            print(f"[brand_collector] WARN {brand['brand_id']}: {exc}", flush=True)

    reg_fields = [
        "brand_id",
        "brand_name",
        "brand_segment",
        "official_url",
        "catalog_url",
        "seoul_districts",
        "primary_context",
        "platform",
        "operational_status",
        "ux_notes",
    ]
    reg_path = RAW_BRAND_DIR / "official_brand_registry.csv"
    with reg_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reg_fields)
        writer.writeheader()
        for b in BRAND_REGISTRY:
            writer.writerow({k: b.get(k, "") for k in reg_fields})

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
