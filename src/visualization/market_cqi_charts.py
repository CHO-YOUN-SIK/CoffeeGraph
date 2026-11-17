"""Generate publication-grade Korean figures for Phase 3 (Seoul Market) & Phase 4 (CQI)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"


def configure_korean_font() -> None:
    preferred = ["Noto Sans CJK KR", "NanumGothic", "Malgun Gothic", "AppleGothic"]
    available = {f.name for f in fm.fontManager.ttflist}
    for font in preferred:
        if font in available:
            plt.rcParams["font.family"] = font
            break
    plt.rcParams["axes.unicode_minus"] = False


def plot_seoul_quarterly_trend() -> Path:
    df = pd.read_csv(TABLES_DIR / "seoul_market_quarterly.csv", dtype={"기준_년분기_코드": str})
    df = df[df["기준_년분기_코드"] >= "20241"].copy()

    fig, ax1 = plt.subplots(figsize=(10, 5.2), dpi=150)
    x = np.arange(len(df))
    ax1.plot(x, df["전체_점포_수"], marker="o", linewidth=2.2, color="#1f4e79", label="전체 점포 수")
    ax1.set_ylabel("전체 점포 수 (개)", color="#1f4e79", fontsize=11)
    ax1.tick_params(axis="y", labelcolor="#1f4e79")
    ax1.set_xticks(x)
    ax1.set_xticklabels(df["기준_년분기_코드"], rotation=0)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    for xi, val in zip(x, df["전체_점포_수"]):
        ax1.annotate(f"{int(val):,}", (xi, val), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8.5)

    ax2 = ax1.twinx()
    ax2.bar(x - 0.15, df["개업_점포_수"], width=0.3, alpha=0.55, color="#2e8b57", label="개업 점포 수")
    ax2.bar(x + 0.15, df["폐업_점포_수"], width=0.3, alpha=0.55, color="#c0392b", label="폐업 점포 수")
    ax2.set_ylabel("개업 / 폐업 점포 수 (개)", fontsize=11)

    plt.title("서울시 커피·음료(CS100010) 분기별 점포 수 및 개·폐업 추이 (2024Q1~2026Q2)", fontsize=12.5, pad=14)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", frameon=True)

    fig.text(
        0.01,
        0.01,
        "출처: 서울 열린데이터광장 OA-22173 (점포-자치구) | 업종: CS100010(커피-음료) | 기간: 20241~20262 (서울 25개 자치구 합계)",
        fontsize=8.5,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = FIG_DIR / "fig01_seoul_quarterly_trend.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_district_store_change_vs_sales() -> Path:
    df = pd.read_csv(TABLES_DIR / "seoul_district_summary_20261.csv", dtype={"자치구_코드": str})

    fig, ax = plt.subplots(figsize=(9.5, 6), dpi=150)
    sc = ax.scatter(
        df["점포당_추정매출_억원"],
        df["점포_증감률_pct"],
        s=df["전체_점포_수"] * 0.18,
        c=df["프랜차이즈_비중_pct"],
        cmap="viridis",
        alpha=0.85,
        edgecolors="#222222",
        linewidths=0.6,
    )
    m, b = np.polyfit(df["점포당_추정매출_억원"], df["점포_증감률_pct"], 1)
    xs = np.linspace(df["점포당_추정매출_억원"].min(), df["점포당_추정매출_억원"].max(), 100)
    ax.plot(xs, m * xs + b, linestyle="--", color="#c0392b", linewidth=1.6, label="선형 추세선 (r=0.5641, p=0.0033)")
    ax.axhline(0, color="#666666", linewidth=0.9, linestyle=":")

    for _, r in df.iterrows():
        ax.annotate(
            r["자치구_코드_명"],
            (r["점포당_추정매출_억원"], r["점포_증감률_pct"]),
            textcoords="offset points",
            xytext=(5, 3),
            fontsize=8.5,
        )

    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label("프랜차이즈 비중 (%)")
    ax.set_xlabel("2026Q1 점포당 월 추정매출 (억원)", fontsize=11)
    ax.set_ylabel("점포 수 변화율 (2024Q2 → 2026Q1, %)", fontsize=11)
    ax.set_title("자치구별 점포당 추정매출과 점포 변화율 관계 (원 크기=전체 점포 수)", fontsize=12.5, pad=12)
    ax.legend(loc="lower right")
    ax.grid(True, linestyle="--", alpha=0.35)

    fig.text(
        0.01,
        0.01,
        "출처: 서울 열린데이터광장 OA-22173·OA-22176 | 업종: CS100010 | 표본: 서울 25개 자치구 (2024Q2 vs 2026Q1)",
        fontsize=8.5,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = FIG_DIR / "fig02_district_store_change_vs_sales.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_commercial_context_clusters() -> Path:
    prof = pd.read_csv(TABLES_DIR / "seoul_commercial_cluster_profiles.csv")
    metrics = ["주말_비중_pct", "시간_06~11_pct", "시간_11~14_pct", "시간_17~21_pct"]
    metric_labels = ["주말 비중(%)", "06~11시(%)", "11~14시(%)", "17~21시(%)"]

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    x = np.arange(len(metrics))
    width = 0.19
    colors = ["#2b5c8f", "#d95f02", "#7570b3", "#1b9e77"]

    for i, (_, row) in enumerate(prof.iterrows()):
        vals = [row[m] for m in metrics]
        label = f"{row['cluster_label']} (n={int(row['commercial_area_count'])})"
        bars = ax.bar(x + (i - 1.5) * width, vals, width=width, label=label, color=colors[i % len(colors)])
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.1f}", (bar.get_x() + bar.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, fontsize=10.5)
    ax.set_ylabel("매출 비중 (%)", fontsize=11)
    ax.set_title("서울 상권별 커피·음료 소비 맥락 군집 프로파일 (2026Q1, KMeans k=4)", fontsize=12.5, pad=12)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    fig.text(
        0.01,
        0.01,
        "출처: 서울 열린데이터광장 OA-15577·OA-15572 | 업종: CS100010 | 표본: 2026Q1 매칭 상권 n=1,064",
        fontsize=8.5,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = FIG_DIR / "fig03_commercial_context_clusters.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_cqi_processing_and_country() -> Path:
    proc = pd.read_csv(TABLES_DIR / "cqi_processing_summary.csv")
    proc_top = proc[proc["count"] >= 20].copy()
    country = pd.read_csv(TABLES_DIR / "cqi_country_summary.csv").head(10)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.2), dpi=150)

    # Left: Processing method mean + 95% CI
    y1 = np.arange(len(proc_top))
    err1 = [proc_top["mean_cup_points"] - proc_top["ci95_low"], proc_top["ci95_high"] - proc_top["mean_cup_points"]]
    ax1.errorbar(proc_top["mean_cup_points"], y1, xerr=err1, fmt="o", color="#1f4e79", capsize=4)
    ax1.set_yticks(y1)
    ax1.set_yticklabels([f"{r['Processing.Method']} (n={int(r['count'])})" for _, r in proc_top.iterrows()], fontsize=9.5)
    ax1.set_xlabel("Total Cup Points 평균 (95% CI)", fontsize=10.5)
    ax1.set_title("가공법별 CQI 커핑 점수 (n≥20)", fontsize=11.5)
    ax1.grid(axis="x", linestyle="--", alpha=0.4)

    # Right: Top 10 countries sample count
    y2 = np.arange(len(country))[::-1]
    ax2.barh(y2, country["count"], color="#2e8b57", alpha=0.85)
    ax2.set_yticks(y2)
    ax2.set_yticklabels(country["Country.of.Origin"], fontsize=9.5)
    for yi, cnt in zip(y2, country["count"]):
        ax2.annotate(f"{int(cnt)}", (cnt, yi), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8.5)
    ax2.set_xlabel("표본 수 (건)", fontsize=10.5)
    ax2.set_title("상위 10개 산지별 표본 편중 (상위 5개국=61.6%)", fontsize=11.5)
    ax2.grid(axis="x", linestyle="--", alpha=0.4)

    fig.text(
        0.01,
        0.01,
        "출처: CQI Coffee Quality Database (jldbc) | 유효 Arabica n=1,310 (0점 이상치 1건 제외; 전체 1,339건 중 Robusta 28건 별도)",
        fontsize=8.5,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    out = FIG_DIR / "fig04_cqi_processing_and_country.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def generate_all_figures() -> list[Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    configure_korean_font()
    return [
        plot_seoul_quarterly_trend(),
        plot_district_store_change_vs_sales(),
        plot_commercial_context_clusters(),
        plot_cqi_processing_and_country(),
    ]


if __name__ == "__main__":
    paths = generate_all_figures()
    for p in paths:
        print("Generated:", p)
