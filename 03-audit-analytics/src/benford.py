"""
Task 2: Benford's Law test on supplier payment amounts.

Benford's Law: in many real-world sets of numbers (invoices, payments, populations), the
FIRST digit is not equally likely. 1 is the first digit about 30% of the time, 9 only about 5%:
    expected share of first digit d = log10(1 + 1/d)
People who invent numbers tend to spread digits evenly or repeat the same few, so a digit that
appears much more (or less) often than Benford predicts is a reason to look closer.

Steps:
    1. first digit of every payment of EUR 10 or more (tiny amounts are usually excluded)
    2. observed vs expected share for digits 1-9
    3. z-test per digit: which digits deviate significantly?
    4. MAD (mean absolute deviation): how well does the whole set conform? (Nigrini's thresholds)
    5. drill down: which vendors cause the deviation?

Run from the project folder:
    cd 03-audit-analytics
    python3 src/benford.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"
OUT.mkdir(exist_ok=True)

BLUE, ORANGE, INK, INK_2, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"

# Step 1. First digit of each payment
payments = pd.read_csv(DATA / "payments.csv")
tested = payments[payments["amount"] >= 10].copy()
tested["first_digit"] = tested["amount"].astype(int).astype(str).str[0].astype(int)  # 9471.20 -> "9471" -> 9
n = len(tested)
print(f"Payments tested: {n:,} (amounts of EUR 10 or more)")

# Step 2. Observed vs expected
digits = pd.DataFrame({"digit": range(1, 10)})
digits["expected_pct"] = np.log10(1 + 1 / digits["digit"])
counts = tested["first_digit"].value_counts()             # like table() in R
digits["count"] = digits["digit"].map(counts).fillna(0).astype(int)
digits["observed_pct"] = digits["count"] / n
digits["expected_count"] = digits["expected_pct"] * n

# Step 3. z-statistic per digit (with continuity correction, as in Nigrini's audit textbook).
#         |z| > 1.96 means the deviation is significant at the 5% level.
p_o, p_e = digits["observed_pct"], digits["expected_pct"]
digits["z"] = (np.abs(p_o - p_e) - 1 / (2 * n)) / np.sqrt(p_e * (1 - p_e) / n)
digits["significant"] = digits["z"] > 1.96

# Step 4. MAD: average distance between observed and expected shares.
#         Nigrini's first-digit thresholds: < 0.006 close, < 0.012 acceptable,
#         < 0.015 marginally acceptable, above that nonconformity.
mad = np.abs(p_o - p_e).mean()
if mad < 0.006:
    verdict = "close conformity"
elif mad < 0.012:
    verdict = "acceptable conformity"
elif mad < 0.015:
    verdict = "marginally acceptable conformity"
else:
    verdict = "nonconformity"

show = digits.assign(expected_pct=(p_e * 100).round(1), observed_pct=(p_o * 100).round(1),
                     expected_count=digits["expected_count"].round(0).astype(int), z=digits["z"].round(2))
print("\n" + show[["digit", "count", "expected_count", "observed_pct", "expected_pct", "z", "significant"]]
      .to_string(index=False))
print(f"\nMAD = {mad:.4f} -> {verdict}")
suspicious = digits.loc[digits["significant"] & (p_o > p_e), "digit"].tolist()
print(f"Digits that appear significantly MORE often than expected: {suspicious}")

# Step 5. Drill down: for each suspicious digit, which vendors have more of it than Benford predicts?
for d in suspicious:
    expected_share = np.log10(1 + 1 / d)
    by_vendor = (tested.groupby("vendor_name")
                       .agg(payments=("amount", "size"),
                            with_digit=("first_digit", lambda s: (s == d).sum()))
                       .reset_index())
    by_vendor["expected"] = by_vendor["payments"] * expected_share
    by_vendor["excess"] = by_vendor["with_digit"] - by_vendor["expected"]
    top = by_vendor.sort_values("excess", ascending=False).head(5)
    print(f"\nVendors with the most excess first digit {d} (expected {expected_share:.1%} of their payments):")
    print(top.assign(expected=top["expected"].round(1), excess=top["excess"].round(1)).to_string(index=False))

# Without the top vendor: does the rest of the data conform?
if suspicious:
    worst = by_vendor.sort_values("excess", ascending=False).iloc[0]["vendor_name"]
    rest = tested[tested["vendor_name"] != worst]
    rest_pct = rest["first_digit"].value_counts(normalize=True).reindex(range(1, 10), fill_value=0)
    rest_mad = np.abs(rest_pct.values - p_e.values).mean()
    print(f"\nMAD without {worst}: {rest_mad:.4f} (was {mad:.4f})")

# Save the table and the chart
digits.round(4).to_csv(OUT / "benford_first_digit.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 4.5))
colors = [ORANGE if (sig and obs > exp) else BLUE
          for sig, obs, exp in zip(digits["significant"], p_o, p_e)]
ax.bar(digits["digit"], p_o * 100, color=colors, width=0.6, label="Observed")
ax.plot(digits["digit"], p_e * 100, color=INK, marker="o", markersize=5, linewidth=1.5,
        label="Expected (Benford)")
for d, obs, sig in zip(digits["digit"], p_o * 100, digits["significant"]):
    if sig:
        ax.annotate(f"{obs:.1f}%", (d, obs), xytext=(0, 4), textcoords="offset points",
                    ha="center", color=INK, fontsize=9)
ax.set_xticks(range(1, 10))
ax.set_xlabel("First digit of payment amount", color=INK_2)
ax.set_ylabel("Share of payments (%)", color=INK_2)
ax.set_title(f"Benford's Law: first digits of {n:,} supplier payments (MAD {mad:.4f}, {verdict})",
             loc="left", fontweight="bold", color=INK)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(colors=INK_2)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT / "benford_first_digit.png", dpi=150)
print("\nSaved output/benford_first_digit.csv, output/benford_first_digit.png")
