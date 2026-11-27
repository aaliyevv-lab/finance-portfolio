"""
Task 6: budget vs actual for October 2026, using the CORRECTED general ledger.

1. Apply the corrections found in the reconciliation (remove duplicates, fix wrong amounts,
   add the bank-only items), so the actual figures are right.
2. Group the corrected ledger into budget categories.
3. Compare with the budget: variance in EUR and %, favourable or unfavourable.
4. Flag variances that are big enough to explain to management.

Sign convention: money in is positive, money out is negative (as in the ledger), so
variance = actual - budget is POSITIVE when it is good news for the hotel, for both
income and costs.

Needs Tasks 2-5 first and data/budget_oct2026.csv.

Run from the project folder:
    cd 02-ledger-reconciliation
    python3 src/budget_vs_actual.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"

# A variance is worth explaining only if it is big in % AND in EUR (materiality)
FLAG_PCT = 0.05     # 5%
FLAG_EUR = 5_000    # EUR 5,000

# Step 1. Load the ledger, the exceptions from Task 4 and the budget
gl = pd.read_csv(DATA / "general_ledger.csv")
exc = pd.read_csv(OUT / "exceptions.csv")
budget = pd.read_csv(DATA / "budget_oct2026.csv")

# Step 2. Correct the ledger
# 2a. Remove the duplicate postings
duplicates = exc.loc[exc["category"] == "Duplicate GL posting", "id"]
gl = gl[~gl["gl_id"].isin(duplicates)].copy()

# 2b. Fix the wrong amounts: take the bank amount for the same reference
bank_amounts = exc[(exc["category"] == "GL amount error") & (exc["side"] == "Bank")]
for _, b in bank_amounts.iterrows():
    gl.loc[gl["reference"] == b["reference"], "amount"] = b["amount"]

# 2c. Add the items that were only on the bank statement
bank_only = exc[exc["category"].isin(["Bank fee not booked", "Interest not booked", "Unidentified receipt"])]
extra = pd.DataFrame({"gl_id": "NEW-" + bank_only["id"], "posting_date": bank_only["date"],
                      "account": 1100, "source": "Bank", "description": bank_only["description"],
                      "reference": bank_only["reference"], "amount": bank_only["amount"]})
gl = pd.concat([gl, extra], ignore_index=True)
print(f"Corrected ledger: {len(gl)} entries, net cash flow EUR {gl['amount'].sum():,.2f}")

# Step 3. Put every ledger line into a budget category
SUPPLIER_CATEGORY = {
    "Metro": "Food and beverage suppliers", "Fresh Produce": "Food and beverage suppliers",
    "Coffee Bean": "Food and beverage suppliers", "Wine Cellar": "Food and beverage suppliers",
    "Fish Market": "Food and beverage suppliers", "Zwack": "Food and beverage suppliers",
    "Linen": "Housekeeping and laundry", "Laundry": "Housekeeping and laundry",
    "Cleaning": "Housekeeping and laundry",
    "Elektro": "Utilities", "Electricity": "Utilities", "Water": "Utilities",
    "IT Systems": "IT and other suppliers", "Florist": "IT and other suppliers",
}


def budget_category(row):
    """Which budget line does this ledger entry belong to? (like case_when in R)"""
    text = row["description"]
    if row["source"] == "POS":
        return "Card takings"
    if row["source"] == "AR" or "TRANSFER IN" in text:
        return "Guest and corporate receipts"
    if row["source"] == "Payroll":
        return "Payroll and taxes"
    if "FEE" in text:
        return "Bank charges"
    if "INTEREST" in text:
        return "Interest income"
    for keyword, category in SUPPLIER_CATEGORY.items():
        if keyword in text:
            return category
    return "Uncategorised"


gl["category"] = gl.apply(budget_category, axis=1)  # run the function on every row
assert (gl["category"] != "Uncategorised").all(), "Some ledger lines have no budget category"

# Step 4. Actual vs budget
actual = gl.groupby("category")["amount"].sum().rename("actual_eur").reset_index()
bva = budget.merge(actual, on="category", how="left")      # left_join(budget, actual)
bva["variance_eur"] = bva["actual_eur"] - bva["budget_eur"]
bva["variance_pct"] = bva["variance_eur"] / bva["budget_eur"].abs()
bva["result"] = bva["variance_eur"].apply(lambda v: "Favourable" if v >= 0 else "Unfavourable")
bva["explain"] = (bva["variance_pct"].abs() >= FLAG_PCT) & (bva["variance_eur"].abs() >= FLAG_EUR)

total = pd.DataFrame([{"category": "NET CASH FLOW", "budget_eur": bva["budget_eur"].sum(),
                       "actual_eur": bva["actual_eur"].sum()}])
total["variance_eur"] = total["actual_eur"] - total["budget_eur"]
total["variance_pct"] = total["variance_eur"] / total["budget_eur"].abs()
total["result"] = "Favourable" if total["variance_eur"].iloc[0] >= 0 else "Unfavourable"
total["explain"] = False
bva = pd.concat([bva, total], ignore_index=True)

show = bva.copy()
for col in ["budget_eur", "actual_eur", "variance_eur"]:
    show[col] = show[col].map(lambda x: f"{x:,.0f}")
show["variance_pct"] = show["variance_pct"].map(lambda x: f"{x:+.1%}")
print("\n" + show.to_string(index=False))
print(f"\nTo explain to management (>= {FLAG_PCT:.0%} and >= EUR {FLAG_EUR:,}): "
      f"{', '.join(bva.loc[bva['explain'], 'category'])}")

# Step 5. Save the table and the corrected ledger
bva.round(4).to_csv(OUT / "budget_vs_actual.csv", index=False)
gl.to_csv(OUT / "general_ledger_corrected.csv", index=False)

# Step 6. Chart: variance by category, green = favourable, red = unfavourable
lines = bva[bva["category"] != "NET CASH FLOW"].sort_values("variance_eur")
colors = ["#2e7d32" if v >= 0 else "#c62828" for v in lines["variance_eur"]]
fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(lines["category"], lines["variance_eur"] / 1000, color=colors)
ax.axvline(0, color="#333333", linewidth=0.8)
ax.set_title("October 2026: budget vs actual (cash), variance by category")
ax.set_xlabel("Variance vs budget (EUR thousand, + = favourable)")
for y, v in enumerate(lines["variance_eur"] / 1000):
    ax.text(v + (0.6 if v >= 0 else -0.6), y, f"{v:+,.1f}k", va="center",
            ha="left" if v >= 0 else "right", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlim(min(lines["variance_eur"].min() / 1000 * 1.35, -5), max(lines["variance_eur"].max() / 1000 * 1.35, 5))
fig.tight_layout()
fig.savefig(OUT / "budget_variance.png", dpi=150)
print("Saved output/budget_vs_actual.csv, output/general_ledger_corrected.csv, output/budget_variance.png")