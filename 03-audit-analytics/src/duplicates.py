"""
Task 3: duplicate payments. Did the hotel pay the same invoice twice?

Two tests, from strict to loose (the same idea as the matching passes in Project 2):
    A. exact duplicates:  same vendor, same invoice number, same amount
    B. near duplicates:   same vendor, same amount, DIFFERENT invoice number,
                          paid within 30 days of each other (the invoice number was retyped)

Test B can also catch legitimate repeat purchases (the same weekly delivery at the same price),
so every hit needs a human check. The invoice-number similarity score helps: a retyped number
(40512 vs 40521) is very similar, a genuinely different invoice usually isn't.

Run from the project folder:
    cd 03-audit-analytics
    python3 src/duplicates.py
"""

from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"
OUT.mkdir(exist_ok=True)
WINDOW_DAYS = 30

payments = pd.read_csv(DATA / "payments.csv", parse_dates=["payment_date"])
payments["cents"] = (payments["amount"] * 100).round().astype(int)   # exact money comparison
print(f"Payments: {len(payments):,}")

# ---------------------------------------------------------------------------
# Test A: exact duplicates
#   keep=False marks EVERY row of a duplicated group (the original and the copy),
#   like duplicated(x) | duplicated(x, fromLast = TRUE) in R.
# ---------------------------------------------------------------------------
key = ["vendor_id", "invoice_no", "cents"]
exact = payments[payments.duplicated(key, keep=False)].sort_values(key + ["payment_date"])
exact_pairs = exact.groupby(key).agg(first_payment=("payment_id", "first"),
                                     second_payment=("payment_id", "last"),
                                     vendor_name=("vendor_name", "first"),
                                     amount=("amount", "first"),
                                     first_date=("payment_date", "min"),
                                     second_date=("payment_date", "max")).reset_index()
exact_pairs["days_apart"] = (exact_pairs["second_date"] - exact_pairs["first_date"]).dt.days
exact_pairs["test"] = "A: exact duplicate"
print(f"\nTest A, exact duplicates: {len(exact_pairs)} pairs, EUR {exact_pairs['amount'].sum():,.2f} paid twice")
print(exact_pairs[["vendor_name", "invoice_no", "amount", "first_date", "second_date", "days_apart"]]
      .to_string(index=False))

# ---------------------------------------------------------------------------
# Test B: near duplicates
#   A self-join: merge the table with itself on vendor + amount, which gives every pair of
#   payments with the same vendor and amount (like inner_join(payments, payments, by = ...) in R).
# ---------------------------------------------------------------------------
cols = ["payment_id", "vendor_id", "vendor_name", "invoice_no", "cents", "amount", "payment_date"]
pairs = payments[cols].merge(payments[cols], on=["vendor_id", "vendor_name", "cents", "amount"],
                             suffixes=("_1", "_2"))
pairs = pairs[pairs["payment_id_1"] < pairs["payment_id_2"]]          # each pair once, not with itself
pairs = pairs[pairs["invoice_no_1"] != pairs["invoice_no_2"]]          # exact duplicates were test A
pairs["days_apart"] = (pairs["payment_date_2"] - pairs["payment_date_1"]).dt.days.abs()
near = pairs[pairs["days_apart"] <= WINDOW_DAYS].copy()


def similarity(a, b):
    """0 = completely different text, 1 = identical (share of matching characters)."""
    return round(SequenceMatcher(None, a, b).ratio(), 2)


near["invoice_similarity"] = [similarity(a, b) for a, b in zip(near["invoice_no_1"], near["invoice_no_2"])]
near["test"] = "B: near duplicate"
print(f"\nTest B, near duplicates (same vendor and amount, different invoice no., <= {WINDOW_DAYS} days): "
      f"{len(near)} pairs, EUR {near['amount'].sum():,.2f}")
print(near[["vendor_name", "invoice_no_1", "invoice_no_2", "amount", "days_apart", "invoice_similarity"]]
      .to_string(index=False))

# ---------------------------------------------------------------------------
# Summary and save
# ---------------------------------------------------------------------------
results = pd.concat([
    exact_pairs.rename(columns={"first_payment": "payment_id_1", "second_payment": "payment_id_2",
                                "invoice_no": "invoice_no_1", "first_date": "payment_date_1",
                                "second_date": "payment_date_2"})
               .assign(invoice_no_2=lambda d: d["invoice_no_1"], invoice_similarity=1.0),
    near,
], ignore_index=True)[["test", "vendor_name", "payment_id_1", "payment_id_2", "invoice_no_1", "invoice_no_2",
                       "invoice_similarity", "amount", "payment_date_1", "payment_date_2", "days_apart"]]

total = results["amount"].sum()
print(f"\nTotal possible overpayment: {len(results)} payments, EUR {total:,.2f}")
print("Action: ask each vendor for a refund or a credit note, and check why the AP system "
      "didn't block a repeated invoice number.")
results.to_csv(OUT / "duplicate_payments.csv", index=False, date_format="%Y-%m-%d")
print("\nSaved output/duplicate_payments.csv")
