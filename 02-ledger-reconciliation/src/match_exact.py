"""
Task 2: exact matching. Pair each bank line with a GL entry that has the same reference
and the same amount, then save what is left unmatched on each side.

Run from the project folder:
    cd 02-ledger-reconciliation
    python3 src/match_exact.py
"""

from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"

# Step 1. Load both files
bank = pd.read_csv(DATA / "bank_statement.csv", parse_dates=["value_date"])
gl = pd.read_csv(DATA / "general_ledger.csv", parse_dates=["posting_date"])

print(f"Bank lines: {len(bank)}   GL entries: {len(gl)}")

# Step 2. Amounts in cents, so 1250.10 always equals 1250.10
bank["cents"] = (bank["amount"] * 100).round().astype(int)
gl["cents"] = (gl["amount"] * 100).round().astype(int)

# Step 3. Number repeated reference+amount pairs: 0 for the first, 1 for the second...
#         This stops one bank line matching two copies of a duplicated GL entry.
bank["n"] = bank.groupby(["reference", "cents"]).cumcount()
gl["n"] = gl.groupby(["reference", "cents"]).cumcount()

# Step 4. Exact match = an inner join on reference, cents and n
matched = bank.merge(gl, on=["reference", "cents", "n"], suffixes=("_bank", "_gl"))
print(f"Exact matches: {len(matched)}")

# Step 5. What is left on each side (anti-joins)
bank_left = bank[~bank["bank_id"].isin(matched["bank_id"])]
gl_left = gl[~gl["gl_id"].isin(matched["gl_id"])]

print(f"Bank lines not matched: {len(bank_left)}   total EUR {bank_left['amount'].sum():,.2f}")
print(f"GL entries not matched: {len(gl_left)}   total EUR {gl_left['amount'].sum():,.2f}")

print("\nBank lines not matched:")
print(bank_left[["bank_id", "value_date", "description", "reference", "amount"]].to_string(index=False))
print("\nGL entries not matched:")
print(gl_left[["gl_id", "posting_date", "description", "reference", "amount"]].to_string(index=False))

# Step 6. Save the results for the next tasks
OUT.mkdir(exist_ok=True)
matched[["bank_id", "gl_id", "reference", "amount_bank"]].to_csv(OUT / "matched_exact.csv", index=False)
bank_left.drop(columns=["cents", "n"]).to_csv(OUT / "bank_unmatched.csv", index=False)
gl_left.drop(columns=["cents", "n"]).to_csv(OUT / "gl_unmatched.csv", index=False)
print("\nSaved output/matched_exact.csv, output/bank_unmatched.csv, output/gl_unmatched.csv")
