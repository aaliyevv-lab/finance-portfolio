"""
Re-run the base-case DCF in Python and save the summary chart to output/dcf_summary.png.

Why: it is an independent check of the Excel model. If both give the same value per share
(HUF 12,753), the Excel formulas are wired correctly.
The inputs below are copied from the 'Assumptions' and 'Historicals' tabs. If you change
an assumption in Excel, change it here too before re-making the chart.

Run from the project folder:
    cd 05-richter-dcf
    python src/make_chart.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "output"

# ---------------------------------------------------------------------------
# 1. Inputs (HUF millions unless stated)
# ---------------------------------------------------------------------------
REVENUE_2025 = 928_962
EBIT_2025 = 292_851
NWC_2025 = 214_114 + 244_395 - 55_636          # inventories + receivables - payables
NET_CASH_AND_INVESTMENTS = (211_817 + 46_345 + 140_672    # cash, current and non-current fin. assets
                            - 1_209 - 19_936 - 67_429      # borrowings, leases, FV liabilities
                            - 2_495)                       # non-controlling interest
SHARES_M = (186_374_860 - 3_507_006) / 1e6
SHARE_PRICE = 13_600                            # HUF, mid-Nov 2026

ROYALTY_SHARE = 0.27      # Vraylar royalties as % of 2025 revenue
ROYALTY_MARGIN = 0.80     # EBIT margin on royalty revenue
TAX = 0.18
G = 0.03                  # terminal growth

# WACC, same steps as the Assumptions tab
cost_of_equity = 0.068 + 0.75 * 0.05                 # CAPM: risk-free + beta x ERP
cost_of_debt = 0.07 * (1 - TAX)
equity = SHARE_PRICE * SHARES_M                      # market value, HUF m
debt = 1_209 + 19_936                                # borrowings + leases
WACC = equity / (equity + debt) * cost_of_equity + debt / (equity + debt) * cost_of_debt

years = [2026, 2027, 2028, 2029, 2030]
royalty_growth = [0.10, 0.10, 0.08, -0.25, -0.60]   # US generics from ~Sep 2029
core_growth = [0.08, 0.08, 0.07, 0.07, 0.06]
DA_PCT, CAPEX_PCT, NWC_PCT = 0.06, 0.07, 0.43

# The core business margin is backed out of 2025: what is left after the royalties
royalty_2025 = REVENUE_2025 * ROYALTY_SHARE
core_2025 = REVENUE_2025 - royalty_2025
core_margin = (EBIT_2025 - royalty_2025 * ROYALTY_MARGIN) / core_2025

# ---------------------------------------------------------------------------
# 2. Forecast, one row per year (like building a tibble row by row)
# ---------------------------------------------------------------------------
rows = []
royalty, core, nwc_prev = royalty_2025, core_2025, NWC_2025
for t, year in enumerate(years, start=1):
    royalty *= 1 + royalty_growth[t - 1]
    core *= 1 + core_growth[t - 1]
    revenue = royalty + core
    ebit = royalty * ROYALTY_MARGIN + core * core_margin
    nwc = revenue * NWC_PCT
    fcff = ebit * (1 - TAX) + revenue * DA_PCT - revenue * CAPEX_PCT - (nwc - nwc_prev)
    rows.append({"year": year, "royalty": royalty, "core": core, "ebit_margin": ebit / revenue,
                 "fcff": fcff, "pv_fcff": fcff / (1 + WACC) ** t})
    nwc_prev = nwc
df = pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# 3. Valuation
# ---------------------------------------------------------------------------
last = df.iloc[-1]
terminal_fcff = last["fcff"] - last["royalty"] * ROYALTY_MARGIN * (1 - TAX)  # royalties gone after 2030
terminal_value = terminal_fcff * (1 + G) / (WACC - G)
ev = df["pv_fcff"].sum() + terminal_value / (1 + WACC) ** len(years)
value_per_share = (ev + NET_CASH_AND_INVESTMENTS) / SHARES_M

print(df.round(3).to_string(index=False))
print(f"\nCore EBIT margin (2025, implied): {core_margin:.1%}")
print(f"Enterprise value: HUF {ev / 1000:,.0f}bn")
print(f"Value per share:  HUF {value_per_share:,.0f}  (Excel model: HUF 12,753)")
print(f"vs price HUF {SHARE_PRICE:,}: {value_per_share / SHARE_PRICE - 1:+.1%}")

# ---------------------------------------------------------------------------
# 4. Chart: revenue mix on top, free cash flow below (no dual axis)
# ---------------------------------------------------------------------------
hist = pd.DataFrame([{"year": 2025, "royalty": royalty_2025, "core": core_2025}])
rev = pd.concat([hist, df[["year", "royalty", "core"]]])
labels = [f"{y}A" if y == 2025 else f"{y}E" for y in rev["year"]]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7.5), sharex=False)
ax1.bar(labels, rev["core"] / 1000, label="Core business", color="#1F3A5F")
ax1.bar(labels, rev["royalty"] / 1000, bottom=rev["core"] / 1000,
        label="Vraylar royalties", color="#E39B3B")
ax1.set_title("Revenue mix: Vraylar royalties fall after US generics (~Sep 2029)")
ax1.set_ylabel("Revenue (HUF bn)")
ax1.legend(frameon=False)

ax2.bar(labels[1:], df["fcff"] / 1000, color="#4F7CAC")
for x, v in zip(labels[1:], df["fcff"] / 1000):
    ax2.text(x, v + 4, f"{v:,.0f}", ha="center", fontsize=9)
ax2.set_title("Free cash flow to the firm")
ax2.set_ylabel("FCFF (HUF bn)")

for ax in (ax1, ax2):
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle(f"Gedeon Richter DCF: HUF {value_per_share:,.0f} per share vs "
             f"HUF {SHARE_PRICE:,} market price ({value_per_share / SHARE_PRICE - 1:+.0%})",
             fontweight="bold")
fig.tight_layout()
fig.savefig(OUT / "dcf_summary.png", dpi=150)
print(f"\nsaved {OUT / 'dcf_summary.png'}")
