"""Two Focused Core Visualizations for Coffee Flavor Language Map:
  Visualization A — Brand Language Landscape (129 SKU Scatter)
  Visualization B — Flavor Language Fingerprint (Brand x SCA/WCR Flavor Family)

Strictly uses candidate SCA-inspired color palette for flavor_family encoding,
with explicit separation between observed copy composition and sensory intensity.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[2]
CODED_SKU_PATH = ROOT / "data" / "processed" / "brands" / "sku_flavor_language_coded.csv"
FINGERPRINT_PATH = ROOT / "outputs" / "tables" / "brand_flavor_fingerprint.csv"
FIG_DIR = ROOT / "outputs" / "figures"

# Candidate Design Palette (inspired by SCA Coffee Taster's Flavor Wheel; subject to matching validation)
FAMILY_COLORS = {
    "Berry": "#C0392B",
    "Citrus": "#E67E22",
    "Stone/Other Fruit": "#E84393",
    "Floral": "#8E44AD",
    "Nutty": "#A67C52",
    "Chocolate/Cocoa": "#5D4037",
    "Sweet/Caramel": "#D4AC0D",
    "Unspecified": "#95A5A6",
}

FAMILIES = [
    "Berry",
    "Citrus",
    "Stone/Other Fruit",
    "Floral",
    "Nutty",
    "Chocolate/Cocoa",
    "Sweet/Caramel",
]


def configure_korean_font() -> None:
    preferred = ["Noto Sans CJK KR", "NanumGothic", "Malgun Gothic", "AppleGothic"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font in preferred:
        if font in available:
            plt.rcParams["font.family"] = font
            break
    plt.rcParams["axes.unicode_minus"] = False


def build_interactive_flavor_map() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    skus = pd.read_csv(CODED_SKU_PATH)
    fp = pd.read_csv(FINGERPRINT_PATH)

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.56, 0.44],
        subplot_titles=(
            "Visualization A — Brand Language Landscape (n=129 SKUs)",
            "Visualization B — Flavor Language Fingerprint (Term Share %)",
        ),
        horizontal_spacing=0.10,
    )

    # Slight deterministic jitter on discrete X so overlapping SKUs are legible
    rng = np.random.default_rng(42)
    skus["x_plot"] = skus["sensory_specificity"] + rng.uniform(-0.18, 0.18, size=len(skus))
    skus["y_plot"] = skus["narrative_density"] + rng.uniform(-0.04, 0.04, size=len(skus))

    # Trace group 1: Visualization A (1 trace per flavor_family for clean legend & brand filtering)
    a_trace_indices = []
    for fam in list(FAMILY_COLORS.keys()):
        sub = skus[skus["dominant_flavor_family"] == fam]
        if sub.empty:
            continue
        prices = sub["price_per_100g"].fillna(10000)
        sizes = np.clip(prices / 650, 8, 26)
        hover_txt = []
        for _, r in sub.iterrows():
            p_str = f"{int(r['price_per_100g']):,}원/100g" if pd.notna(r["price_per_100g"]) else "가격 미표기"
            anchors = r["extracted_anchors"] if pd.notna(r["extracted_anchors"]) and r["extracted_anchors"] else "없음"
            narr = r["extracted_narrative"] if pd.notna(r["extracted_narrative"]) and r["extracted_narrative"] else "없음"
            hover_txt.append(
                f"<b>{r['sku_name']}</b><br>"
                f"브랜드: {r['brand_id']} | {p_str}<br>"
                f"계열(Hue): {fam} | 구체성(X): {r['sensory_specificity']:.1f} ({r['specificity_tier']})<br>"
                f"서사밀도(Y): {r['narrative_density']:.2f}/100자 (텍스트 {int(r['text_length'])}자)<br>"
                f"추출 감각 앵커: {anchors}<br>"
                f"추출 감성 어휘: {narr}"
            )
        fig.add_trace(
            go.Scatter(
                x=sub["x_plot"],
                y=sub["y_plot"],
                mode="markers",
                name=f"{fam} (n={len(sub)})",
                legendgroup=fam,
                customdata=sub["brand_id"].tolist(),
                marker=dict(
                    size=sizes,
                    color=FAMILY_COLORS[fam],
                    opacity=0.82,
                    line=dict(width=1.0, color="#222222"),
                ),
                text=hover_txt,
                hoverinfo="text",
            ),
            row=1,
            col=1,
        )
        a_trace_indices.append((fam, sub["brand_id"].tolist()))

    # Trace group 2: Visualization B (Stacked Horizontal Bar of Term Share % per brand)
    fp_sorted = fp.sort_values("mean_sensory_specificity", ascending=True)
    for fam in FAMILIES:
        col_name = f"term_share_{fam}"
        fig.add_trace(
            go.Bar(
                y=fp_sorted["brand_id"],
                x=fp_sorted[col_name],
                name=fam,
                orientation="h",
                legendgroup=fam,
                showlegend=False,
                marker=dict(color=FAMILY_COLORS[fam], opacity=0.88),
                hovertemplate=f"브랜드: %{{y}}<br>계열: {fam}<br>어휘 구성비: %{{x:.1f}}%<extra></extra>",
            ),
            row=1,
            col=2,
        )

    # Interactive Brand Highlight Dropdown (updates marker opacity in Visualization A)
    brands = sorted(skus["brand_id"].unique().tolist())
    buttons = [
        dict(
            label="전체 브랜드 보기 (All 8 Brands)",
            method="restyle",
            args=[
                {"marker.opacity": [0.82] * len(a_trace_indices)},
                list(range(len(a_trace_indices))),
            ],
        )
    ]
    for b in brands:
        opacities = []
        for _, trace_brands in a_trace_indices:
            opacities.append([0.95 if tb == b else 0.12 for tb in trace_brands])
        buttons.append(
            dict(
                label=f"강조: {b}",
                method="restyle",
                args=[
                    {"marker.opacity": opacities},
                    list(range(len(a_trace_indices))),
                ],
            )
        )

    fig.update_layout(
        title=dict(
            text="<b>Coffee Flavor Language Map</b> — 브랜드별 원두 향미 언어 구조와 시각적 문법<br>"
            "<sup>표본: 공식 온라인몰 8개 브랜드 129개 SKU | 색상=SCA/WCR 후보 팔레트(타당성 검증 대상) | 비율은 감각 강도가 아닌 언어 구성비</sup>",
            x=0.5,
        ),
        barmode="stack",
        height=640,
        width=1360,
        template="plotly_white",
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.15,
                yanchor="top",
            )
        ],
        legend=dict(orientation="h", yanchor="bottom", y=-0.20, xanchor="center", x=0.5),
    )
    fig.update_xaxes(title_text="sensory_specificity (광의=1, 구체적 앵커=2 합산)", row=1, col=1)
    fig.update_yaxes(title_text="narrative_density (100자당 감성·추상 표현 수)", row=1, col=1)
    fig.update_xaxes(title_text="향미 어휘 구성비 (% of Flavor Mentions)", range=[0, 100], row=1, col=2)

    out_html = FIG_DIR / "coffee_flavor_language_map.html"
    fig.write_html(out_html, include_plotlyjs="cdn")
    return out_html


def build_static_flavor_map() -> Path:
    configure_korean_font()
    skus = pd.read_csv(CODED_SKU_PATH)
    fp = pd.read_csv(FINGERPRINT_PATH).sort_values("mean_sensory_specificity", ascending=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.8), dpi=150, gridspec_kw={"width_ratios": [1.15, 1.0]})

    rng = np.random.default_rng(42)
    x_j = skus["sensory_specificity"] + rng.uniform(-0.18, 0.18, size=len(skus))
    y_j = skus["narrative_density"] + rng.uniform(-0.04, 0.04, size=len(skus))

    for fam, color in FAMILY_COLORS.items():
        mask = skus["dominant_flavor_family"] == fam
        if not mask.any():
            continue
        sizes = np.clip(skus.loc[mask, "price_per_100g"].fillna(10000) / 110, 28, 160)
        ax1.scatter(
            x_j[mask],
            y_j[mask],
            s=sizes,
            c=color,
            alpha=0.8,
            edgecolors="#222222",
            linewidths=0.6,
            label=f"{fam} ({mask.sum()})",
        )

    ax1.set_xlabel("sensory_specificity (감각 표현 구체성)", fontsize=10.5)
    ax1.set_ylabel("narrative_density (100자당 감성·추상 표현)", fontsize=10.5)
    ax1.set_title("A. Brand Language Landscape (n=129 SKUs)", fontsize=11.5)
    ax1.grid(True, linestyle="--", alpha=0.35)
    ax1.legend(loc="upper right", fontsize=8, frameon=True, ncol=2)

    left = np.zeros(len(fp))
    y_pos = np.arange(len(fp))
    for fam in FAMILIES:
        vals = fp[f"term_share_{fam}"].values
        ax2.barh(y_pos, vals, left=left, color=FAMILY_COLORS[fam], alpha=0.88, label=fam)
        left += vals

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([f"{r['brand_id']} (n={int(r['sku_count'])})" for _, r in fp.iterrows()], fontsize=9.5)
    ax2.set_xlabel("향미 어휘 구성비 (%)", fontsize=10.5)
    ax2.set_xlim(0, 100)
    ax2.set_title("B. Flavor Language Fingerprint (어휘 구성비)", fontsize=11.5)
    ax2.grid(axis="x", linestyle="--", alpha=0.35)

    fig.text(
        0.01,
        0.01,
        "출처: 8개 브랜드 공식 온라인몰 129 SKU | 색상=SCA/WCR 후보 팔레트 | 비율은 감각 강도가 아닌 설명문 내 어휘 구성비임",
        fontsize=8.5,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out_png = FIG_DIR / "fig05_flavor_language_map.png"
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return out_png


def main() -> int:
    h = build_interactive_flavor_map()
    p = build_static_flavor_map()
    print("Generated:", h)
    print("Generated:", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
