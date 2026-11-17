"""Visualization C — Market Context Validation Map (Seoul Commercial Areas, 2026Q1).

Plots external population validation of the 4 consumer_context.py clusters (n=1,064):
- Panel A (H-M1): log10(1 + Work Population) vs 11-14h Sales Share (%)
- Panel B (H-M2): log10(1 + Resident Population) vs 17-21h Sales Share (%)
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
TABLES_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"

CLUSTER_COLORS = {
    "오피스·점심 집중형": "#E74C3C",
    "주말·방문형": "#3498DB",
    "모닝·복합형": "#2ECC71",
    "저녁·생활형": "#9B59B6",
}


def _set_korean_font() -> None:
    for f in fm.fontManager.ttflist:
        if "Noto Sans CJK" in f.name or "Nanum" in f.name or "Malgun" in f.name:
            plt.rcParams["font.family"] = f.name
            break
    plt.rcParams["axes.unicode_minus"] = False


def build_market_validation_maps() -> tuple[Path, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    _set_korean_font()

    df = pd.read_csv(TABLES_DIR / "seoul_commercial_validated_20261.csv")
    df["log10_work"] = np.log10(1.0 + df["총_직장_인구_수"].fillna(0).clip(lower=0))
    df["log10_res"] = np.log10(1.0 + df["총_상주인구_수"].fillna(0).clip(lower=0))
    df["dot_size"] = np.clip(np.sqrt(df["전체_점포_수"].fillna(1)) * 6.0, 12, 180)

    # Static PNG
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 6.0))
    for cl, color in CLUSTER_COLORS.items():
        sub_w = df[(df["cluster_label"] == cl) & df["총_직장_인구_수"].notna()]
        ax1.scatter(
            sub_w["log10_work"],
            sub_w["시간_11~14_pct"],
            s=sub_w["dot_size"],
            color=color,
            alpha=0.58,
            edgecolors="#222222",
            linewidth=0.4,
            label=f"{cl} (n={len(sub_w)})",
        )
        sub_r = df[(df["cluster_label"] == cl) & df["총_상주인구_수"].notna()]
        ax2.scatter(
            sub_r["log10_res"],
            sub_r["시간_17~21_pct"],
            s=sub_r["dot_size"],
            color=color,
            alpha=0.58,
            edgecolors="#222222",
            linewidth=0.4,
            label=f"{cl} (n={len(sub_r)})",
        )

    ax1.set_title("H-M1: 직장인구 규모 × 11–14시 매출 비중", fontsize=12)
    ax1.set_xlabel("log10(1 + 총 직장인구 수)")
    ax1.set_ylabel("11–14시 매출 비중 (%)")
    ax1.grid(linestyle="--", alpha=0.35)
    ax1.legend(loc="upper left", fontsize=8)

    ax2.set_title("H-M2: 상주인구 규모 × 17–21시 매출 비중", fontsize=12)
    ax2.set_xlabel("log10(1 + 총 상주인구 수)")
    ax2.set_ylabel("17–21시 매출 비중 (%)")
    ax2.grid(linestyle="--", alpha=0.35)
    ax2.legend(loc="upper left", fontsize=8)

    fig.text(
        0.01,
        0.01,
        "출처: 서울 열린데이터광장 2026Q1 (OA-15569 직장인구, OA-15584 상주인구, OA-15572/15577 매칭 1,064개 상권) | 점 크기=점포 수",
        fontsize=8.5,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out_png = FIG_DIR / "fig06_market_context_validation.png"
    fig.savefig(out_png, dpi=150)
    plt.close(fig)

    # Interactive HTML
    pfig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("H-M1: 직장인구 × 11–14시 매출 비중", "H-M2: 상주인구 × 17–21시 매출 비중"),
        horizontal_spacing=0.09,
    )
    for cl, color in CLUSTER_COLORS.items():
        sub_w = df[(df["cluster_label"] == cl) & df["총_직장_인구_수"].notna()]
        hover_w = [
            f"<b>{r['상권_코드_명']}</b> ({r['cluster_label']})<br>"
            f"직장인구: {int(r['총_직장_인구_수']):,}명 | 점포수: {int(r['전체_점포_수'])}개<br>"
            f"11–14시 매출 비중: {r['시간_11~14_pct']:.1f}%"
            for _, r in sub_w.iterrows()
        ]
        pfig.add_trace(
            go.Scatter(
                x=sub_w["log10_work"],
                y=sub_w["시간_11~14_pct"],
                mode="markers",
                name=cl,
                legendgroup=cl,
                marker=dict(size=np.clip(np.sqrt(sub_w["전체_점포_수"]) * 2.5, 6, 20), color=color, opacity=0.65),
                text=hover_w,
                hoverinfo="text",
            ),
            row=1,
            col=1,
        )
        sub_r = df[(df["cluster_label"] == cl) & df["총_상주인구_수"].notna()]
        hover_r = [
            f"<b>{r['상권_코드_명']}</b> ({r['cluster_label']})<br>"
            f"상주인구: {int(r['총_상주인구_수']):,}명 | 점포수: {int(r['전체_점포_수'])}개<br>"
            f"17–21시 매출 비중: {r['시간_17~21_pct']:.1f}%"
            for _, r in sub_r.iterrows()
        ]
        pfig.add_trace(
            go.Scatter(
                x=sub_r["log10_res"],
                y=sub_r["시간_17~21_pct"],
                mode="markers",
                name=cl,
                legendgroup=cl,
                showlegend=False,
                marker=dict(size=np.clip(np.sqrt(sub_r["전체_점포_수"]) * 2.5, 6, 20), color=color, opacity=0.65),
                text=hover_r,
                hoverinfo="text",
            ),
            row=1,
            col=2,
        )

    pfig.update_layout(
        title="Visualization C: 서울 상권 군집 외부 타당성 검증 맵 (n=1,064, 2026Q1)",
        template="plotly_white",
        height=560,
        width=1280,
        legend=dict(orientation="h", y=-0.18),
    )
    pfig.update_xaxes(title_text="log10(1 + 총 직장인구 수)", row=1, col=1)
    pfig.update_yaxes(title_text="11–14시 매출 비중 (%)", row=1, col=1)
    pfig.update_xaxes(title_text="log10(1 + 총 상주인구 수)", row=1, col=2)
    pfig.update_yaxes(title_text="17–21시 매출 비중 (%)", row=1, col=2)

    out_html = FIG_DIR / "market_context_validation.html"
    pfig.write_html(out_html, include_plotlyjs="cdn")
    return out_png, out_html


def main() -> int:
    png, html = build_market_validation_maps()
    print("Generated:", png)
    print("Generated:", html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
