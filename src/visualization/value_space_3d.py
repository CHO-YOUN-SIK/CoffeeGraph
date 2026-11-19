"""Track C Visualization: 3D Brand Value Space Art & Research Prototype.

Generates:
  1. Interactive 3D HTML (`outputs/figures/coffee_value_space_3d.html`) via Plotly
  2. Static 4-panel PNG (`outputs/figures/fig07_brand_value_space_3d.png`) via Matplotlib

Strictly enforces `Visual Juxtaposition — Not Consumer-Brand Fit` and separates
`Minimal / Unstated` web disclosure from absence of brand philosophy.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[2]
IN_BRANDS_CSV = ROOT / "outputs" / "tables" / "value_space_brands.csv"
OUT_HTML = ROOT / "outputs" / "figures" / "coffee_value_space_3d.html"
OUT_PNG = ROOT / "outputs" / "figures" / "fig07_brand_value_space_3d.png"

TIER_COLORS = {
    "Rich Disclosure": "#1B6B5C",
    "Moderate Disclosure": "#C86D3B",
    "Minimal / Unstated": "#6E7885",
}

SHORT_LABELS = {
    "coffee_libre": "Coffee Libre",
    "blue_bottle_kr": "Blue Bottle KR",
    "paul_bassett": "Paul Bassett",
    "felt_coffee": "FELT Coffee",
    "fritz": "Fritz",
    "anthracite": "Anthracite",
    "terarosa": "Terarosa",
    "center_coffee": "Center Coffee",
}


def build_plotly_3d(df: pd.DataFrame) -> go.Figure:
    """Create interactive 3D Value Space HTML figure."""
    fig = go.Figure()

    # 1. Translucent Consumer Field Reference Placeholder (awaiting KREI 2025 / Opensurvey 2025)
    u = np.linspace(0, 2 * np.pi, 24)
    v = np.linspace(0, np.pi, 16)
    cx, cy, cz = 58.0, 52.0, 38.0
    rx, ry, rz = 26.0, 24.0, 22.0
    xs = cx + rx * np.outer(np.cos(u), np.sin(v))
    ys = cy + ry * np.outer(np.sin(u), np.sin(v))
    zs = cz + rz * np.outer(np.ones_like(u), np.cos(v))

    fig.add_trace(
        go.Surface(
            x=xs,
            y=ys,
            z=zs,
            opacity=0.12,
            showscale=False,
            colorscale=[[0, "#B89B72"], [1, "#B89B72"]],
            name="Consumer Field (Placeholder: Awaiting KREI/Opensurvey 2025)",
            hoverinfo="skip",
            showlegend=True,
        )
    )

    # 2. Sculptural floor drop-lines & origin vectors for 3D spatial depth
    for _, row in df.iterrows():
        color = TIER_COLORS.get(row["z_disclosure_tier"], "#6E7885")
        x, y, z = row["x_practical"], row["y_sensory"], row["z_philosophical"]
        # Drop-line to XY floor (z=0)
        fig.add_trace(
            go.Scatter3d(
                x=[x, x],
                y=[y, y],
                z=[0, z],
                mode="lines",
                line=dict(color=color, width=2, dash="dot"),
                opacity=0.45,
                showlegend=False,
                hoverinfo="skip",
            )
        )
        # Origin identity vector
        fig.add_trace(
            go.Scatter3d(
                x=[0, x],
                y=[0, y],
                z=[0, z],
                mode="lines",
                line=dict(color=color, width=1.5),
                opacity=0.22,
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # 3. Brand Identity nodes grouped by z_disclosure_tier
    for tier, grp in df.groupby("z_disclosure_tier", sort=False):
        color = TIER_COLORS.get(tier, "#6E7885")
        labels = [SHORT_LABELS.get(b, b) for b in grp["brand_id"]]
        hover_texts = [
            (
                f"<b>{r['brand_name']}</b><br>"
                f"Segment: {r['brand_segment']}<br>"
                f"Disclosure Tier: {r['z_disclosure_tier']}<br>"
                f"X (Practical): {r['x_practical']:.1f} | Convenience SKUs: {r['convenience_sku_pct']:.1f}%<br>"
                f"Y (Sensory): {r['y_sensory']:.1f} | Specificity: {r['mean_sensory_specificity']:.2f}<br>"
                f"Z (Philosophical): {r['z_philosophical']:.1f} | Clean Text: {int(r['philosophy_clean_length'])} chars<br>"
                f"SKUs: {int(r['sku_count'])}"
            )
            for _, r in grp.iterrows()
        ]
        sizes = np.clip(grp["sku_count"].astype(float) * 0.9 + 9.0, 11, 32)
        fig.add_trace(
            go.Scatter3d(
                x=grp["x_practical"],
                y=grp["y_sensory"],
                z=grp["z_philosophical"],
                mode="markers+text",
                name=f"Brand Z-Tier: {tier}",
                text=labels,
                textposition="top center",
                textfont=dict(size=11, color="#1F242B"),
                hovertext=hover_texts,
                hoverinfo="text",
                marker=dict(
                    size=sizes,
                    color=color,
                    opacity=0.92,
                    line=dict(color="#FFFFFF", width=1.5),
                ),
            )
        )

    fig.update_layout(
        title=dict(
            text=(
                "CoffeeGraph Track C: 3D Brand Value Space Prototype<br>"
                "<sup>Practical (X) × Sensory (Y) × Philosophical (Z) · "
                "Visual Juxtaposition — Not Consumer-Brand Fit</sup>"
            ),
            x=0.5,
            font=dict(size=18, color="#1F242B"),
        ),
        paper_bgcolor="#F8F6F2",
        plot_bgcolor="#F8F6F2",
        scene=dict(
            xaxis=dict(
                title="X · Practical Value (Convenience & Price Access)",
                range=[0, 105],
                backgroundcolor="#F3EFE8",
                gridcolor="#D8D2C7",
                zerolinecolor="#B8B0A2",
            ),
            yaxis=dict(
                title="Y · Sensory Value (Specificity & Flavor Narrative)",
                range=[0, 105],
                backgroundcolor="#F3EFE8",
                gridcolor="#D8D2C7",
                zerolinecolor="#B8B0A2",
            ),
            zaxis=dict(
                title="Z · Philosophical Value (Official Sustainability & Craft)",
                range=[0, 105],
                backgroundcolor="#EFEAE0",
                gridcolor="#D8D2C7",
                zerolinecolor="#B8B0A2",
            ),
            camera=dict(eye=dict(x=1.45, y=1.45, z=1.1)),
        ),
        legend=dict(
            x=0.01,
            y=0.98,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#D8D2C7",
            borderwidth=1,
            font=dict(size=11),
        ),
        margin=dict(l=10, r=10, t=75, b=20),
    )
    return fig


def build_static_png(df: pd.DataFrame) -> None:
    """Create 4-panel static overview (3D isometric + 3 orthogonal projections)."""
    plt.rcParams["font.family"] = "DejaVu Sans"
    fig = plt.figure(figsize=(15, 11), facecolor="#F8F6F2")
    fig.suptitle(
        "CoffeeGraph Track C: 3D Brand Value Space (Practical × Sensory × Philosophical)",
        fontsize=15,
        fontweight="bold",
        color="#1F242B",
        y=0.97,
    )
    fig.text(
        0.5,
        0.935,
        "Brand Identity coordinates from SKU data (n=129) & official brand pages (n=8) · "
        "Minimal/Unstated Z = low public web disclosure · Visual Juxtaposition — Not Consumer Fit",
        ha="center",
        fontsize=9.5,
        color="#4B525C",
    )

    # Panel 1: 3D Isometric View
    ax3d = fig.add_subplot(2, 2, 1, projection="3d", facecolor="#F8F6F2")
    for _, row in df.iterrows():
        c = TIER_COLORS.get(row["z_disclosure_tier"], "#6E7885")
        x, y, z = row["x_practical"], row["y_sensory"], row["z_philosophical"]
        ax3d.plot([x, x], [y, y], [0, z], linestyle=":", color=c, alpha=0.55, linewidth=1.2)
        ax3d.scatter(
            x,
            y,
            z,
            s=row["sku_count"] * 7 + 55,
            color=c,
            edgecolors="#FFFFFF",
            linewidths=1.0,
            alpha=0.92,
            zorder=5,
        )
        lbl = SHORT_LABELS.get(row["brand_id"], row["brand_id"])
        dz = 3.0
        if row["brand_id"] == "center_coffee":
            dz = -7.0
        elif row["brand_id"] == "anthracite":
            dz = 6.0
        ax3d.text(x + 2, y + 2, z + dz, lbl, fontsize=7.8, color="#1F242B")

    ax3d.set_xlim(0, 105)
    ax3d.set_ylim(0, 105)
    ax3d.set_zlim(0, 105)
    ax3d.set_xlabel("X: Practical", fontsize=8.5, labelpad=6)
    ax3d.set_ylabel("Y: Sensory", fontsize=8.5, labelpad=6)
    ax3d.set_zlabel("Z: Philosophical", fontsize=8.5, labelpad=6)
    ax3d.set_title("A. 3D Brand Value Space", fontsize=11, fontweight="bold", pad=10)
    ax3d.view_init(elev=22, azim=40)

    # Panels 2-4: Orthogonal 2D projections
    projections = [
        (2, "x_practical", "y_sensory", "X · Practical Value", "Y · Sensory Value", "B. Practical vs. Sensory (X–Y)"),
        (3, "x_practical", "z_philosophical", "X · Practical Value", "Z · Philosophical Value", "C. Practical vs. Philosophical (X–Z)"),
        (4, "y_sensory", "z_philosophical", "Y · Sensory Value", "Z · Philosophical Value", "D. Sensory vs. Philosophical (Y–Z)"),
    ]

    for idx, xcol, ycol, xlabel, ylabel, title in projections:
        ax = fig.add_subplot(2, 2, idx, facecolor="#FFFFFF")
        ax.grid(True, linestyle="--", alpha=0.35, color="#C8C0B4")
        ax.axhline(50, color="#B8B0A2", linewidth=0.9, linestyle="-.")
        ax.axvline(50, color="#B8B0A2", linewidth=0.9, linestyle="-.")

        for _, row in df.iterrows():
            c = TIER_COLORS.get(row["z_disclosure_tier"], "#6E7885")
            ax.scatter(
                row[xcol],
                row[ycol],
                s=row["sku_count"] * 7 + 60,
                color=c,
                edgecolors="#FFFFFF",
                linewidths=1.1,
                alpha=0.9,
                zorder=4,
            )
            lbl = SHORT_LABELS.get(row["brand_id"], row["brand_id"])
            dx, dy = (2.2, 2.0)
            if row[xcol] > 82:
                dx = -16.0
            if row[ycol] > 92:
                dy = -5.5
            ax.annotate(
                lbl,
                (row[xcol], row[ycol]),
                xytext=(row[xcol] + dx, row[ycol] + dy),
                fontsize=8.2,
                color="#1F242B",
            )

        ax.set_xlim(-5, 108)
        ax.set_ylim(-5, 108)
        ax.set_xlabel(xlabel, fontsize=9.5, color="#2D333B")
        ax.set_ylabel(ylabel, fontsize=9.5, color="#2D333B")
        ax.set_title(title, fontsize=11, fontweight="bold", color="#1F242B", pad=8)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)

    # Shared Legend
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", label=f"Z-Tier: {tier}", markerfacecolor=col, markersize=9)
        for tier, col in TIER_COLORS.items()
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=3,
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#D8D2C7",
        fontsize=9.5,
        bbox_to_anchor=(0.5, 0.015),
    )

    plt.tight_layout(rect=[0.01, 0.05, 0.99, 0.92])
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=200)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(IN_BRANDS_CSV)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)

    fig = build_plotly_3d(df)
    fig.write_html(str(OUT_HTML), include_plotlyjs="cdn")
    build_static_png(df)

    print(f"Saved {OUT_HTML}")
    print(f"Saved {OUT_PNG}")


if __name__ == "__main__":
    main()
