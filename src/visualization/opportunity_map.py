"""Interactive Coffee Brand Opportunity Map (Plotly HTML Dashboard).

Combines 4 analytical views into outputs/figures/coffee_opportunity_map.html:
1. Seoul 25-District Choropleth Map (Store change %, 20261 vs 20262, sales/store)
2. Commercial-Area Context Map (n=1,064 matched areas across 4 KMeans clusters)
3. Brand Positioning & Whitespace Map (Emotional/Abstract % vs Sensory Density, sized by price/100g)
4. 9-Dimension Flavor Language Heatmap across verified brands
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "outputs" / "tables"
GEOJSON_PATH = ROOT / "data" / "processed" / "seoul" / "seoul_districts.geojson"
FIG_DIR = ROOT / "outputs" / "figures"

CLUSTER_COLORS = {
    "오피스·점심 집중형": "#d95f02",
    "주말·방문형": "#1b9e77",
    "모닝·복합형": "#2b5c8f",
    "저녁·생활형": "#7570b3",
}

SEGMENT_COLORS = {
    "Global Specialty": "#1f77b4",
    "Specialty Roaster": "#2ca02c",
    "Franchise Reference": "#e6550d",
}


def build_opportunity_map() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    geojson = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    dist_261 = pd.read_csv(TABLES_DIR / "seoul_district_summary_20261.csv", dtype={"자치구_코드": str})
    dist_262 = pd.read_csv(TABLES_DIR / "seoul_district_latest_20262.csv", dtype={"자치구_코드": str})
    dist_df = dist_261.merge(
        dist_262[["자치구_코드", "전체_점포_수"]].rename(columns={"전체_점포_수": "전체_점포_수_20262"}),
        on="자치구_코드",
        how="left",
    )

    comm_df = pd.read_csv(TABLES_DIR / "seoul_commercial_clusters_20261.csv", dtype={"상권_코드": str})
    brand_df = pd.read_csv(TABLES_DIR / "brand_positioning_summary.csv")
    reg_df = pd.read_csv(ROOT / "data" / "raw" / "brands" / "official_brand_registry.csv")
    if "brand_segment" not in brand_df.columns and "brand_segment" in reg_df.columns:
        brand_df = brand_df.merge(reg_df[["brand_id", "brand_segment"]], on="brand_id", how="left")

    fig = make_subplots(
        rows=2,
        cols=2,
        specs=[
            [{"type": "choropleth"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "heatmap"}],
        ],
        subplot_titles=(
            "1. 서울 25개 자치구 점포 변화율 (2024Q2→2026Q1, 2026Q2 병기)",
            "2. 상권 소비 맥락 4군집 (n=1,064 | 점포당 매출 vs 주말 비중)",
            "3. 브랜드 향미 언어 포지셔닝 맵 (원 크기=100g당 가격)",
            "4. 브랜드별 9차원 향미 언어 프로필 (%)",
        ),
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    # --- Panel 1: Seoul 25-District Choropleth ---
    hover_dist = [
        (
            f"<b>{r['자치구_코드_명']}</b><br>"
            f"2026Q1 점포: {int(r['전체_점포_수']):,}개 (2026Q2: {int(r['전체_점포_수_20262']):,}개)<br>"
            f"2024Q2→2026Q1 증감률: {r['점포_증감률_pct']:+.2f}%<br>"
            f"점포당 월 매출: {r['점포당_추정매출_억원']*10000:,.0f}만 원<br>"
            f"프랜차이즈 비중: {r['프랜차이즈_비중_pct']:.1f}%"
        )
        for _, r in dist_df.iterrows()
    ]
    fig.add_trace(
        go.Choropleth(
            geojson=geojson,
            locations=dist_df["자치구_코드_명"],
            featureidkey="properties.name",
            z=dist_df["점포_증감률_pct"],
            colorscale="RdYlGn",
            zmid=0,
            colorbar=dict(title="증감률(%)", x=0.45, y=0.78, len=0.35),
            text=hover_dist,
            hoverinfo="text",
            name="자치구",
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        row=1,
        col=1,
    )

    # --- Panel 2: Commercial-Area Context Map ---
    comm_plot = comm_df.copy()
    comm_plot["점포당_매출_만원"] = (comm_plot["점포당_매출_원"] / 10000).clip(upper=12000)
    for clabel, grp in comm_plot.groupby("cluster_label"):
        hover_c = [
            (
                f"<b>{r['상권_코드_명']}</b> ({r['상권_구분_코드_명']})<br>"
                f"군집: {clabel}<br>"
                f"점포 수: {int(r['전체_점포_수'])}개 | 점포당 매출: {r['점포당_매출_원']/10000:,.0f}만 원<br>"
                f"11~14시: {r['시간_11~14_pct']:.1f}% | 주말: {r['주말_비중_pct']:.1f}%"
            )
            for _, r in grp.iterrows()
        ]
        fig.add_trace(
            go.Scatter(
                x=grp["점포당_매출_만원"],
                y=grp["주말_비중_pct"],
                mode="markers",
                name=f"{clabel} (n={len(grp)})",
                marker=dict(
                    size=np.clip(grp["전체_점포_수"] * 0.55 + 4, 5, 22),
                    color=CLUSTER_COLORS.get(clabel, "#666666"),
                    opacity=0.65,
                    line=dict(width=0.5, color="#222222"),
                ),
                text=hover_c,
                hoverinfo="text",
            ),
            row=1,
            col=2,
        )
    fig.update_xaxes(title_text="점포당 월 추정매출 (만 원, 상한 1.2억 표시)", row=1, col=2)
    fig.update_yaxes(title_text="주말 매출 비중 (%)", row=1, col=2)

    # --- Panel 3: Brand Positioning Map ---
    # Shaded BX/CX Opportunity Whitespace: balanced narrative (15-45%) + high sensory clarity (>=2.2 dims)
    fig.add_shape(
        type="rect",
        x0=15,
        x1=45,
        y0=2.2,
        y1=max(3.8, float(brand_df["mean_sensory_dims"].max()) + 0.5),
        fillcolor="rgba(46, 139, 87, 0.12)",
        line=dict(color="rgba(46, 139, 87, 0.6)", dash="dash", width=1.5),
        row=2,
        col=1,
    )
    fig.add_annotation(
        x=30,
        y=max(3.6, float(brand_df["mean_sensory_dims"].max()) + 0.35),
        text="BX/CX 기회 영역<br>(적정 서사 × 고감각 번역)",
        showarrow=False,
        font=dict(size=10.5, color="#1e6b43"),
        row=2,
        col=1,
    )

    for seg, grp in brand_df.groupby("brand_segment"):
        prices = grp["median_price_per_100g"].fillna(9000)
        sizes = np.clip(prices / 450, 14, 42)
        hover_b = []
        for _, r in grp.iterrows():
            price_str = f"{int(r['median_price_per_100g']):,}원" if pd.notna(r["median_price_per_100g"]) else "미표기"
            hover_b.append(
                f"<b>{r['brand_name']}</b> ({seg})<br>"
                f"검증 SKU: {int(r['sku_count'])}개 | 100g당 중앙값: {price_str}<br>"
                f"감성·추상 비중: {r['pct_감성적·추상적']:.1f}% | 평균 감각차원: {r['mean_sensory_dims']:.2f}개<br>"
                f"싱글오리진 비중: {r['single_origin_share_pct']:.1f}%<br>"
                f"서울 입지: {r['seoul_districts']}"
            )
        fig.add_trace(
            go.Scatter(
                x=grp["pct_감성적·추상적"],
                y=grp["mean_sensory_dims"],
                mode="markers+text",
                name=seg,
                text=grp["brand_id"],
                textposition="top center",
                hovertext=hover_b,
                hoverinfo="text",
                marker=dict(
                    size=sizes,
                    color=SEGMENT_COLORS.get(seg, "#555555"),
                    opacity=0.85,
                    line=dict(width=1.2, color="#111111"),
                ),
            ),
            row=2,
            col=1,
        )
    fig.update_xaxes(title_text="감성적·추상적 표현 비중 (%)", range=[-5, 105], row=2, col=1)
    fig.update_yaxes(title_text="평균 감각 어휘 밀도 (차원 수/SKU)", row=2, col=1)

    # --- Panel 4: 9-Dimension Flavor Heatmap ---
    dims = ["과일", "꽃", "초콜릿", "견과류", "카라멜", "산미", "단맛", "바디·질감", "감성적·추상적"]
    pct_cols = [f"pct_{d}" for d in dims]
    z_mat = brand_df[pct_cols].values
    fig.add_trace(
        go.Heatmap(
            z=z_mat,
            x=dims,
            y=brand_df["brand_id"],
            colorscale="YlGnBu",
            text=np.round(z_mat, 1),
            texttemplate="%{text:.0f}%",
            colorbar=dict(title="비중(%)", x=1.02, y=0.22, len=0.35),
            hovertemplate="브랜드: %{y}<br>차원: %{x}<br>언급 비중: %{z:.1f}%<extra></extra>",
            showscale=True,
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        title=dict(
            text="<b>CoffeeGraph: 서울 커피 시장 맥락 & 브랜드 향미 Opportunity Map</b><br>"
            "<sup>출처: 서울 열린데이터광장(OA-22173·22176·15577·15572, 2024Q2~2026Q2) & 공식 브랜드 온라인몰 검증 SKU</sup>",
            x=0.5,
        ),
        height=980,
        width=1360,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.08, xanchor="center", x=0.5),
    )

    out_html = FIG_DIR / "coffee_opportunity_map.html"
    fig.write_html(out_html, include_plotlyjs="cdn")
    return out_html


def main() -> int:
    out = build_opportunity_map()
    print("Generated interactive Opportunity Map:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
