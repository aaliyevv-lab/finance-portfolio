"""
Task 4: payment control tests. Is anyone getting around the approval rules?

The hotel's rules for supplier payments:
    R1  payments of EUR 10,000 or more must be approved by the financial controller
    R2  nobody may approve a payment they entered themselves (four-eyes principle)
    R3  whoever pays suppliers should not also create new suppliers (segregation of duties)

Tests:
    1. approval limit: are all payments >= EUR 10,000 approved by the controller?
    2. just below the limit: which vendors get unusually many payments of EUR 9,000-9,999?
    3. self-approval: payments where entered_by == approved_by
    4. new vendors: vendors created this year, who created them, and what they were paid
    5. split payments: two or more large payments to one vendor within 3 days that together pass the limit

Run from the project folder:
    cd 03-audit-analytics
    python3 src/payment_controls.py
"""

from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"
OUT.mkdir(exist_ok=True)

LIMIT = 10_000
BAND_LOW = 9_000             # "just below the limit" = EUR 9,000 - 9,999.99
CONTROLLER = "mtoth"
YEAR_START = pd.Timestamp("2025-11-01")

payments = pd.read_csv(DATA / "payments.csv", parse_dates=["payment_date"])
vendors = pd.read_csv(DATA / "vendors.csv", parse_dates=["created_date"])
findings = []   # one dict per flagged payment, collected from every test


def flag(rows, test):
    """Add every row of a DataFrame to the findings list under one test name."""
    for _, r in rows.iterrows():
        findings.append({"test": test, "payment_id": r["payment_id"], "vendor_name": r["vendor_name"],
                         "payment_date": r["payment_date"], "amount": r["amount"],
                         "entered_by": r["entered_by"], "approved_by": r["approved_by"]})


# Test 1. R1: payments at or above the limit need the controller
big = payments[payments["amount"] >= LIMIT]
not_by_controller = big[big["approved_by"] != CONTROLLER]
print(f"Test 1, approval limit: {len(big)} payments of EUR {LIMIT:,}+; "
      f"{len(not_by_controller)} not approved by the controller")
flag(not_by_controller, "1: over limit without controller approval")

# Test 2. Just below the limit, by vendor.
#         A few payments in the band are normal for big suppliers. A vendor with a HIGH SHARE of
#         its payments in the band is not.
payments["in_band"] = payments["amount"].between(BAND_LOW, LIMIT - 0.01)
band = (payments.groupby("vendor_name")
                .agg(payments=("amount", "size"), in_band=("in_band", "sum"), total_paid=("amount", "sum"))
                .reset_index())
band["share_in_band"] = band["in_band"] / band["payments"]
band = band[band["in_band"] > 0].sort_values("share_in_band", ascending=False)
print(f"\nTest 2, just below the limit (EUR {BAND_LOW:,}-{LIMIT - 0.01:,.2f}): "
      f"{int(payments['in_band'].sum())} payments")
print(band.assign(share_in_band=(band["share_in_band"] * 100).round(1),
                  total_paid=band["total_paid"].round(0)).head(6).to_string(index=False))
suspicious_vendors = band.loc[(band["share_in_band"] >= 0.25) & (band["in_band"] >= 3), "vendor_name"]
print(f"Vendors with >= 25% of payments just below the limit: {list(suspicious_vendors)}")
flag(payments[payments["in_band"] & payments["vendor_name"].isin(suspicious_vendors)],
     "2: just below approval limit")

# Test 3. R2: self-approval
self_approved = payments[payments["entered_by"] == payments["approved_by"]]
print(f"\nTest 3, self-approved payments: {len(self_approved)}, EUR {self_approved['amount'].sum():,.2f}")
print(self_approved.groupby(["entered_by", "vendor_name"])["amount"].agg(["count", "sum"])
      .round(2).to_string())
flag(self_approved, "3: self-approved")

# Test 4. R3: vendors created during the year
new = vendors[vendors["created_date"] >= YEAR_START].copy()
paid = payments.groupby("vendor_id")["amount"].agg(n_payments="size", total_paid="sum")
new = new.join(paid, on="vendor_id")
new["creator_also_enters_payments"] = new["created_by"].isin(payments["entered_by"])
print(f"\nTest 4, vendors created this year: {len(new)}")
print(new.to_string(index=False))
flag(payments[payments["vendor_id"].isin(new.loc[new["creator_also_enters_payments"], "vendor_id"])],
     "4: new vendor created by a payment clerk")

# Test 5. Split payments: one purchase cut into two smaller payments to stay under the limit.
#         Look for 2+ payments to the same vendor within 3 days, EACH at least half the limit
#         (EUR 5,000-9,999.99) and TOGETHER at or above it. Requiring each part to be large keeps
#         out the many small, normal deliveries from food suppliers.
mid = payments[payments["amount"].between(LIMIT / 2, LIMIT - 0.01)].sort_values("payment_date")
mid = mid.set_index("payment_date")
mid["sum_3d"] = mid.groupby("vendor_name")["amount"].transform(lambda s: s.rolling("3D").sum())
mid["count_3d"] = mid.groupby("vendor_name")["amount"].transform(lambda s: s.rolling("3D").count())
ends = mid[(mid["count_3d"] >= 2) & (mid["sum_3d"] >= LIMIT)].reset_index()
print(f"\nTest 5, possible split payments (2+ payments of EUR {LIMIT / 2:,.0f}-{LIMIT - 0.01:,.2f} "
      f"to one vendor within 3 days, together >= EUR {LIMIT:,}): {len(ends)} cases")
# Raw counts favour big suppliers (more payments = more chances). Compare cases per 100 payments.
split_rate = (ends.groupby("vendor_name").size().rename("split_cases").to_frame()
                  .join(payments.groupby("vendor_name").size().rename("payments")))
split_rate["cases_per_100_payments"] = (100 * split_rate["split_cases"] / split_rate["payments"]).round(1)
print(split_rate.sort_values("cases_per_100_payments", ascending=False).to_string())

# Summary: which payments are flagged by more than one test?
f = pd.DataFrame(findings)
per_payment = (f.groupby(["payment_id", "vendor_name", "amount"])["test"]
                .agg(n_tests="size", tests=lambda t: "; ".join(sorted(t))).reset_index()
                .sort_values(["n_tests", "amount"], ascending=False))
print(f"\nPayments flagged by tests 1-4: {len(per_payment)}, EUR {per_payment['amount'].sum():,.2f}")
print(per_payment["vendor_name"].value_counts().to_string())

per_payment.to_csv(OUT / "payment_control_findings.csv", index=False)
print("\nSaved output/payment_control_findings.csv")
