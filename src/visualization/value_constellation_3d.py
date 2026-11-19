"""Optional CoffeeGraph generative 3D artwork: observed brand communication, not fit.

This is a spatial sculpture, not a chart of consumer attitudes. Coordinates
come from Track C heuristic brand disclosure proxies. Geometry is deterministic
and varies with recorded SKU count and the X/Y/Z proxy values.
Unknown philosophy coordinates are unplaced, not invented.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[2]
BRAND_TABLE = ROOT / "outputs" / "tables" / "value_space_brands.csv"
CONSUMER_EVIDENCE = ROOT / "outputs" / "tables" / "consumer_value_evidence.json"
OUT_HTML = ROOT / "outputs" / "figures" / "coffee_value_constellation_3d.html"

PALETTE = ["#F5B89A", "#A6D2D7", "#B4A4DB", "#E5BE7A", "#DDA3B9", "#A3BBA4", "#91B4DD", "#D9C6B8"]


def build_constellation(df: pd.DataFrame, consumer: dict | None = None) -> go.Figure:
    valid = df[df["z_philosophical"].notna()].copy().sort_values("brand_id")
    missing = df.loc[df["z_philosophical"].isna(), "brand_name"].tolist()
    fig = go.Figure()
    for i, (_, brand) in enumerate(valid.iterrows()):
        x0 = float(brand["x_practical"])
        y0 = float(brand["y_sensory"])
        z0 = float(brand["z_philosophical"])
        sku = int(brand["sku_count"])
        color = PALETTE[i % len(PALETTE)]
        strands = 6 + min(7, round(y0 / 18))
        width = 2.1 + min(4.6, sku / 13)
        # The published source density affects the final orb scale, not a claim of ethics.
        for k in range(strands):
            theta = np.linspace(0, 2 * np.pi * (1.3 + k * 0.032), 150)
            phi = 2 * np.pi * k / strands
            radius = (width + k * .11) * (0.8 + .25 * np.sin(theta * 3 + phi))
            bend = (.35 + x0 / 180) * np.sin(theta * 2.2 + phi)
            xs = x0 + radius * np.cos(theta + phi) + 1.8 * bend
            ys = y0 + radius * np.sin(theta + phi) + 1.0 * np.cos(theta * 1.8 + phi)
            zs = z0 + 2.5 * np.sin(theta * 2 + phi) + .5 * (k - strands / 2) + bend
            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=zs, mode="lines", name=str(brand["brand_id"]),
                legendgroup=str(brand["brand_id"]), showlegend=False,
                line=dict(color=color, width=2 + (k % 3)), opacity=.48,
                hoverinfo="skip",
            ))

        hover = (
            f"<b>{brand['brand_name']}</b><br>"
            f"X Practical publication proxy: {x0:.1f}<br>"
            f"Y Sensory language proxy: {y0:.1f}<br>"
            f"Z Philosophy disclosure proxy: {z0:.1f}<br>"
            f"Observed SKU rows: {sku}<br>"
            f"Disclosure coverage: {brand['z_disclosure_tier']}<br>"
            "<i>Not an attitude survey or brand-preference score</i>"
        )
        fig.add_trace(go.Scatter3d(
            x=[x0], y=[y0], z=[z0], mode="markers+text",
            name=str(brand["brand_name"]), legendgroup=str(brand["brand_id"]),
            showlegend=True, text=[str(brand["brand_name"]).split(" (")[0]],
            textposition="top center", textfont=dict(color="#EDE8E3", size=11),
            marker=dict(size=5.5, color=color, line=dict(color="#FFFFFF", width=1)),
            hovertext=[hover], hoverinfo="text",
        ))
    survey_note = "Consumer evidence unavailable"
    if consumer and consumer.get("status") == "PUBLIC_AGGREGATES_ONLY":
        rows = {x["metric_id"]: x["percent"] for x in consumer.get("metrics", [])}
        if {"customization_ever", "premium_coffee_quality", "premium_atmosphere"} <= set(rows):
            survey_note = (
                f"Consumer survey (separate national evidence): "
                f"personalization ever {rows['customization_ever']:.1f}%"
                f" · premium quality {rows['premium_coffee_quality']:.1f}%"
                f" · atmosphere {rows['premium_atmosphere']:.1f}%"
            )
    fig.update_layout(
        title=dict(text=(
            "COFFEEGRAPH / VALUE CONSTELLATION"
            "<br><sup>Generative brand communication sculpture · evidence is not brand identity or consumer-brand fit</sup>"
        ), x=.05, font=dict(size=20, color="#ECE7E2")),
        paper_bgcolor="#070F1D",
        scene=dict(
            xaxis=dict(title="Practical · proxy", range=[-10, 110], showbackground=False, gridcolor="#273548",
                       tickfont=dict(color="#A3B0C1"), titlefont=dict(color="#A3B0C1")),
            yaxis=dict(title="Sensory · proxy", range=[-10, 110], showbackground=False, gridcolor="#273548",
                       tickfont=dict(color="#A3B0C1"), titlefont=dict(color="#A3B0C1")),
            zaxis=dict(title="Published philosophy · proxy", range=[-10, 110], showbackground=False, gridcolor="#273548",
                       tickfont=dict(color="#A3B0C1"), titlefont=dict(color="#A3B0C1")),
            bgcolor="#070F1D",
            aspectmode="cube",
            camera=dict(eye=dict(x=1.7, y=1.4, z=1.05)),
        ),
        margin=dict(l=0, r=0, t=105, b=125),
        legend=dict(
            orientation="h", x=.5, y=-.015, xanchor="center",
            font=dict(color="#B8C9D8", size=10), bgcolor="rgba(7,15,29,.75)",
            groupclick="togglegroup",
        ),
        annotations=[
            dict(x=.5, y=-.10, xref="paper", yref="paper",
                 text=survey_note, showarrow=False, xanchor="center",
                 font=dict(color="#E4BFA7", size=11)),
            dict(x=.5, y=-.15, xref="paper", yref="paper",
                 text="No consumer XYZ available; survey items are not aligned with 8 brand signals.",
                 showarrow=False, xanchor="center", font=dict(color="#889CB1", size=10)),
            dict(x=.5, y=-.20, xref="paper", yref="paper",
                 text="Unplaced (missing website Z): " + (", ".join(missing) if missing else "none"),
                 showarrow=False, xanchor="center", font=dict(color="#C7979A", size=10)),
        ],
    )
    return fig


def main() -> None:
    df = pd.read_csv(BRAND_TABLE)
    consumer = json.loads(CONSUMER_EVIDENCE.read_text(encoding="utf-8")) if CONSUMER_EVIDENCE.exists() else {}
    fig = build_constellation(df, consumer)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs="cdn")
    print(f"Rendered 3D Value Constellation: {OUT_HTML}")


if __name__ == "__main__":
    main()
