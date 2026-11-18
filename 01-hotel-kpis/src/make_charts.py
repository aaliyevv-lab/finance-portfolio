"""
Turn the SQL results into charts for the README.

Runs the queries saved in sql/*.sql (so the SQL files stay the single source of truth),
loads each result into a pandas DataFrame, and saves 4 PNG charts to output/.

Usage (from the 01-hotel-kpis folder):
    python3 src/make_charts.py
"""

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter

from run_sql import DB_PATH, split_queries  # reuse the helper from Task 2

PROJECT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT / "sql"
OUT_DIR = PROJECT / "output"

# --- Style: one consistent look for every chart -------------------------------
BLUE = "#2a78d6"     # main series
ORANGE = "#eb6834"   # second series (commission)
INK = "#0b0b0b"      # titles
INK_2 = "#52514e"    # labels, ticks
GRID = "#e4e3df"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_2,
    "axes.titlecolor": INK,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "font.size": 10,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})

euro = FuncFormatter(lambda x, _: f"€{x:,.0f}")
euro_m = FuncFormatter(lambda x, _: f"€{x / 1e6:.1f}M")


def query(sql_file, number):
    """Run query number `number` (1, 2, 3...) from a .sql file and return a DataFrame.
    Like reading a CSV in R, except the data comes from SQL."""
    queries = split_queries((SQL_DIR / sql_file).read_text())
    title, sql = queries[number - 1]
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql(sql, con)


def month_labels(months):
    """'2025-11' -> 'Nov 25'"""
    return pd.to_datetime(months).dt.strftime("%b %y")


# --- Chart 1: monthly KPI dashboard (the README chart) ------------------------
def chart_monthly_kpis():
    df = query("03_adr_revpar.sql", 1)          # month, occupancy_pct, adr_eur, revpar_eur
    x = month_labels(df["month"])

    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    panels = [
        ("occupancy_pct", "Occupancy", PercentFormatter(decimals=0), (0, 100), "{:.0f}%"),
        ("adr_eur", "ADR (average daily rate)", euro, (0, 800), "€{:,.0f}"),
        ("revpar_eur", "RevPAR (revenue per available room)", euro, (0, 700), "€{:,.0f}"),
    ]
    for ax, (col, title, fmt, ylim, label_fmt) in zip(axes, panels):
        ax.bar(x, df[col], color=BLUE, width=0.6)
        ax.set_title(title)
        ax.yaxis.set_major_formatter(fmt)
        ax.set_ylim(*ylim)
        ax.grid(axis="x", visible=False)
        # label only the highest and lowest month (selective labels, not every bar)
        for i in (df[col].idxmax(), df[col].idxmin()):
            ax.annotate(label_fmt.format(df[col][i]), (i, df[col][i]),
                        ha="center", va="bottom", xytext=(0, 3),
                        textcoords="offset points", color=INK, fontsize=9)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.text(0.06, 0.985, "Hotel KPIs by month, Nov 2025 – Oct 2026",
             fontsize=14, fontweight="bold", color=INK, va="top")
    fig.text(0.06, 0.955, "130-room luxury hotel, Budapest. December leads on RevPAR "
             "thanks to price, not volume.", color=INK_2, va="top")
    fig.savefig(OUT_DIR / "monthly_kpis.png")
    plt.close(fig)


# --- Chart 2: gross revenue split into net + commission, by channel -----------
def chart_channel_revenue():
    df = query("05_channel_revenue.sql", 1).sort_values("gross_revenue_eur")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(df["channel_name"], df["net_revenue_eur"], color=BLUE, height=0.6,
            label="Net revenue (hotel keeps)")
    ax.barh(df["channel_name"], df["commission_eur"], left=df["net_revenue_eur"],
            color=ORANGE, height=0.6, label="Commission paid",
            edgecolor=SURFACE, linewidth=1.5)
    for y, (gross, comm) in enumerate(zip(df["gross_revenue_eur"], df["commission_eur"])):
        text = f"€{gross / 1e6:.2f}M gross" + (f"  ·  €{comm / 1e6:.2f}M commission" if comm else "")
        ax.text(gross + 80_000, y, text, va="center", color=INK_2, fontsize=9)

    ax.xaxis.set_major_formatter(euro_m)
    ax.set_xlim(0, df["gross_revenue_eur"].max() * 1.6)
    ax.grid(axis="y", visible=False)
    ax.set_title("Room revenue by channel: what the hotel keeps vs. pays in commission")
    ax.legend(loc="lower right", frameon=False)
    fig.savefig(OUT_DIR / "channel_revenue.png")
    plt.close(fig)


# --- Chart 3: cancellation rate by channel ------------------------------------
def chart_cancellations():
    df = query("04_cancellations.sql", 1).sort_values("cancel_rate_pct")
    avg = 100 * df["n_cancelled"].sum() / df["n_bookings"].sum()

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(df["channel_name"], df["cancel_rate_pct"], color=BLUE, height=0.6)
    for y, rate in enumerate(df["cancel_rate_pct"]):
        ax.text(rate + 0.5, y, f"{rate:.0f}%", va="center", color=INK, fontsize=9)
    ax.axvline(avg, color=INK_2, linestyle="--", linewidth=1)
    ax.text(avg + 0.3, -0.55, f"Hotel average {avg:.0f}%", color=INK_2, fontsize=9)

    ax.xaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.set_xlim(0, df["cancel_rate_pct"].max() * 1.2)
    ax.grid(axis="y", visible=False)
    ax.set_title("Cancellation rate by booking channel")
    fig.savefig(OUT_DIR / "cancellations.png")
    plt.close(fig)


# --- Chart 4: occupancy weekday vs weekend ------------------------------------
def chart_weekday_weekend():
    df = query("02_occupancy.sql", 3)

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.barh(df["night_type"], df["occupancy_pct"], color=BLUE, height=0.5)
    for y, occ in enumerate(df["occupancy_pct"]):
        ax.text(occ + 1, y, f"{occ:.1f}%", va="center", color=INK, fontsize=9)
    ax.xaxis.set_major_formatter(PercentFormatter(decimals=0))
    ax.set_xlim(0, 100)
    ax.grid(axis="y", visible=False)
    ax.set_title("Occupancy: weekday vs. weekend nights")
    fig.savefig(OUT_DIR / "weekday_weekend.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    chart_monthly_kpis()
    chart_channel_revenue()
    chart_cancellations()
    chart_weekday_weekend()
    for png in sorted(OUT_DIR.glob("*.png")):
        print(f"saved {png.relative_to(PROJECT)}")
