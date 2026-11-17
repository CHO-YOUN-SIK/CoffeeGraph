"""Two Focused Core Visualizations for Coffee Flavor Language Map (Audited & Refined):
  Visualization A — Brand Language Landscape (SKU-level Scatter)
  Visualization B — Flavor Language Fingerprint (Brand x Flavor Family SKU Mention Rate %)

Fixes implemented from audit:
- Uniform dot size (no missing-price 10,000 KRW imputation; price shown in hover only for whole_bean)
- Explicit 'None-Stated' (x=0) separation and 'Multi-Family (Tie)' color category
- Fingerprint uses SKU mention rate (%) + explicit detected/total count (k/n) instead of 100% stacked bar
- Interactive HTML includes product_type_std (All vs Whole Bean) and brand_id filters
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
    "Multi-Family (Tie)": "#2C3E50",
    "None-Stated": "#BDC3C7",
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

DOMINANT_ORDER = FAMILIES + ["Multi-Family (Tie)", "None-Stated"]


def _set_korean_font() -> None:
    for f in fm.fontManager.ttflist:
        if "Noto Sans CJK" in f.name or "Nanum" in f.name or "Malgun" in f.name:
            plt.rcParams["font.family"] = f.name
            break
    plt.rcParams["axes.unicode_minus"] = False


def build_interactive_flavor_map() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CODED_SKU_PATH)
    fp = pd.read_csv(FINGERPRINT_PATH)

    rng = np.random.default_rng(42)
    df["x_jit"] = df["sensory_specificity"] + rng.uniform(-0.10, 0.10, size=len(df))
    df["y_jit"] = np.maximum(0.0, df["narrative_density"] + rng.uniform(-0.02, 0.02, size=len(df)))

    fig = make_subplots(
        rows=1,
        cols=2,
        column_widths=[0.54, 0.46],
        subplot_titles=(
            "Visualization A: Brand Language Landscape (향미 설명 좌표)",
            "Visualization B: Flavor Language Fingerprint (계열별 SKU 언급률 %)",
        ),
        horizontal_spacing=0.10,
    )

    scatter_traces_meta: list[tuple[str, str]] = []  # (brand_id, product_type_std)
    for dom_fam in DOMINANT_ORDER:
        sub = df[df["dominant_flavor_family"] == dom_fam]
        if sub.empty:
            continue
        hover_texts = []
        for _, r in sub.iterrows():
            p_str = (
                f"{int(r['price_per_100g']):,}원/100g"
                if pd.notna(r["price_per_100g"]) and r["product_type_std"] == "whole_bean"
                else "미제공 / 비교제외"
            )
            anchors = r["extracted_anchors"] if pd.notna(r["extracted_anchors"]) and r["extracted_anchors"] else "없음"
            hover_texts.append(
                f"<b>{r['sku_name']}</b><br>"
                f"브랜드: {r['brand_name']}<br>"
                f"상품유형: {r['product_type_std']} | 원산지: {r['origin_type']}<br>"
                f"대표 계열: {r['dominant_flavor_family']}<br>"
                f"구체성 점수: {r['sensory_specificity']} ({r['specificity_tier']})<br>"
                f"서사 밀도: {r['narrative_density']:.3f} / 100자<br>"
                f"추출 앵커: {anchors}<br>"
                f"가격(일반원두): {p_str}"
            )
        fig.add_trace(
            go.Scatter(
                x=sub["x_jit"],
                y=sub["y_jit"],
                mode="markers",
                name=f"{dom_fam} ({len(sub)})",
                legendgroup=dom_fam,
                marker=dict(
                    size=10,
                    color=FAMILY_COLORS.get(dom_fam, "#7F8C8D"),
                    opacity=0.84,
                    line=dict(width=1.0, color="#222222"),
                ),
                text=hover_texts,
                hoverinfo="text",
                customdata=np.stack([sub["brand_id"], sub["product_type_std"]], axis=-1),
            ),
            row=1,
            col=1,
        )
        scatter_traces_meta.append((dom_fam, "scatter"))

    # Visualization B: Heatmap of SKU Mention Rate (%) by Brand x Flavor Family
    fp_sorted = fp.sort_values("mean_sensory_specificity", ascending=True).reset_index(drop=True)
    y_labels = [
        f"{r['brand_id']} (검출 {int(r['flavor_detected_count'])}/{int(r['sku_count'])}, {r['flavor_detected_pct']:.0f}%)"
        for _, r in fp_sorted.iterrows()
    ]
    z_vals = fp_sorted[[f"sku_pct_{f}" for f in FAMILIES]].to_numpy()
    text_vals = [[f"{v:.0f}%" for v in row] for row in z_vals]

    fig.add_trace(
        go.Heatmap(
            z=z_vals,
            x=FAMILIES,
            y=y_labels,
            text=text_vals,
            texttemplate="%{text}",
            colorscale="YlGnBu",
            zmin=0,
            zmax=100,
            colorbar=dict(title="언급 SKU %", len=0.85, x=1.02),
            hovertemplate="브랜드: %{y}<br>계열: %{x}<br>언급 SKU 비율: %{z:.1f}%<extra></extra>",
            showscale=True,
        ),
        row=1,
        col=2,
    )

    fig.add_vline(x=0.25, line_dash="dash", line_color="#7F8C8D", row=1, col=1)
    fig.add_annotation(
        x=0.0,
        y=1.04,
        xref="x",
        yref="paper",
        text="← 미검출 (None-Stated)",
        showarrow=False,
        font=dict(size=10, color="#555555"),
    )

    # Interactive Product-Type Filter (All 129 SKUs vs Whole Bean Only)
    n_scatter = len(scatter_traces_meta)
    all_x = []
    all_y = []
    wb_x = []
    wb_y = []
    for dom_fam, _ in scatter_traces_meta:
        sub_all = df[df["dominant_flavor_family"] == dom_fam]
        sub_wb = sub_all[sub_all["product_type_std"] == "whole_bean"]
        all_x.append(sub_all["x_jit"].tolist())
        all_y.append(sub_all["y_jit"].tolist())
        wb_x.append(sub_wb["x_jit"].tolist())
        wb_y.append(sub_wb["y_jit"].tolist())

    scatter_indices = list(range(n_scatter))
    buttons = [
        dict(
            label="전체 SKU (n=129)",
            method="restyle",
            args=[{"x": all_x, "y": all_y}, scatter_indices],
        ),
        dict(
            label="일반 원두만 (whole_bean, n=98)",
            method="restyle",
            args=[{"x": wb_x, "y": wb_y}, scatter_indices],
        ),
    ]

    fig.update_layout(
        title=dict(
            text="Coffee Flavor Language Map — 브랜드 향미 언어 좌표 및 계열별 언급률 (n=129 SKUs)",
            x=0.5,
            font=dict(size=16),
        ),
        template="plotly_white",
        height=640,
        width=1360,
        legend=dict(title="대표 향미 계열 (Hue)", orientation="h", y=-0.20, x=0.0),
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                buttons=buttons,
                x=0.0,
                y=1.13,
                xanchor="left",
                yanchor="top",
            )
        ],
        margin=dict(t=100, b=130, l=70, r=80),
    )
    fig.update_xaxes(title_text="sensory_specificity (0=미검출, 0.5=광의, 1+=고유 구체 앵커 수)", row=1, col=1)
    fig.update_yaxes(title_text="narrative_density (100자당 감성·추상 표현 출현 수)", row=1, col=1)
    fig.update_xaxes(title_text="SCA/WCR 향미 계열 (중복 언급 허용, 합계 ≠ 100%)", tickangle=-25, row=1, col=2)

    out_html = FIG_DIR / "coffee_flavor_language_map.html"
    fig.write_html(out_html, include_plotlyjs="cdn")
    return out_html


def build_static_flavor_map() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    _set_korean_font()
    df = pd.read_csv(CODED_SKU_PATH)
    fp = pd.read_csv(FINGERPRINT_PATH)

    rng = np.random.default_rng(42)
    df["x_jit"] = df["sensory_specificity"] + rng.uniform(-0.10, 0.10, size=len(df))
    df["y_jit"] = np.maximum(0.0, df["narrative_density"] + rng.uniform(-0.02, 0.02, size=len(df)))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 6.4), gridspec_kw={"width_ratios": [1.15, 1.0]})

    # Panel A: Brand Language Landscape (uniform dot size; explicit None-Stated & Multi-Family)
    for dom_fam in DOMINANT_ORDER:
        sub = df[df["dominant_flavor_family"] == dom_fam]
        if sub.empty:
            continue
        ax1.scatter(
            sub["x_jit"],
            sub["y_jit"],
            s=65,
            color=FAMILY_COLORS.get(dom_fam, "#7F8C8D"),
            alpha=0.84,
            edgecolors="#222222",
            linewidth=0.7,
            label=f"{dom_fam} ({len(sub)})",
        )
    ymin, ymax = ax1.get_ylim()
    ax1.set_ylim(ymin, ymax * 1.07)
    ax1.axvline(0.25, color="#7F8C8D", linestyle="--", linewidth=1.0)
    ax1.text(0.0, ymax * 1.01, "미검출", fontsize=8.5, color="#555555", ha="center",
             bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85))
    ax1.set_title("A. Brand Language Landscape (n=129 SKUs, 점 크기 고정)", fontsize=12)
    ax1.set_xlabel("sensory_specificity (0=미검출, 0.5=광의, 1+=고유 구체 앵커 수)")
    ax1.set_ylabel("narrative_density (100자당 감성·추상 표현)")
    ax1.grid(linestyle="--", alpha=0.35)
    ax1.legend(loc="upper right", fontsize=7.5, ncol=2, frameon=True)

    # Panel B: Flavor Language Fingerprint — SKU Mention Rate (%) Heatmap
    fp_sorted = fp.sort_values("mean_sensory_specificity", ascending=False).reset_index(drop=True)
    mat = fp_sorted[[f"sku_pct_{f}" for f in FAMILIES]].to_numpy()
    im = ax2.imshow(mat, cmap="YlGnBu", aspect="auto", vmin=0, vmax=100)

    y_labels = [
        f"{r['brand_id']} ({int(r['flavor_detected_count'])}/{int(r['sku_count'])}, {r['flavor_detected_pct']:.0f}%)"
        for _, r in fp_sorted.iterrows()
    ]
    ax2.set_yticks(np.arange(len(fp_sorted)))
    ax2.set_yticklabels(y_labels, fontsize=9)
    ax2.set_xticks(np.arange(len(FAMILIES)))
    ax2.set_xticklabels(["Berry", "Citrus", "Stone/\nFruit", "Floral", "Nutty", "Choc/\nCocoa", "Sweet/\nCaramel"], fontsize=8.5)
    ax2.set_title("B. Flavor Language Fingerprint (계열별 언급 SKU 비율 %)", fontsize=12)
    ax2.set_xlabel("SCA/WCR 향미 계열 (복수 언급 허용, 합계 ≠ 100%)")

    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = mat[i, j]
            txt_color = "white" if val >= 55 else "#111111"
            ax2.text(j, i, f"{val:.0f}%", ha="center", va="center", color=txt_color, fontsize=8)

    cbar = fig.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    cbar.set_label("언급 SKU %", fontsize=9)

    fig.text(
        0.01,
        0.01,
        "출처: 8개 브랜드 공식몰 129 SKU(정제 본문 기준) | 색상=SCA/WCR 후보 팔레트 | 비율=계열별 언급 SKU %(감각 강도 아님)",
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
