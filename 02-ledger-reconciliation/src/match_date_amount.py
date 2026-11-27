"""
Task 3: second-pass matching. Some lines didn't match in Task 2 because the reference was
typed wrongly. Here we match what is left on the same DATE and the same AMOUNT instead.

Needs the Task 2 output first (python3 src/match_exact.py).

Run from the project folder:
    cd 02-ledger-reconciliation
    python3 src/match_date_amount.py
"""

from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "output"

# Step 1. Load what Task 2 could not match
bank = pd.read_csv(OUT / "bank_unmatched.csv", parse_dates=["value_date"])
gl = pd.read_csv(OUT / "gl_unmatched.csv", parse_dates=["posting_date"])
print(f"Left after Task 2:  bank {len(bank)}   GL {len(gl)}")

# Step 2. Same helper columns as Task 2: amount in cents, and a counter for repeats
bank["cents"] = (bank["amount"] * 100).round().astype(int)
gl["cents"] = (gl["amount"] * 100).round().astype(int)

# The join needs the same column name for the date on both sides
bank["date"] = bank["value_date"]
gl["date"] = gl["posting_date"]

bank["n"] = bank.groupby(["date", "cents"]).cumcount()
gl["n"] = gl.groupby(["date", "cents"]).cumcount()

# Step 3. Second pass = inner join on date, cents and n (reference is ignored)
matched = bank.merge(gl, on=["date", "cents", "n"], suffixes=("_bank", "_gl"))
print(f"Matched on date and amount: {len(matched)}")
print(matched[["bank_id", "gl_id", "date", "amount_bank", "reference_bank", "reference_gl"]]
      .to_string(index=False))

# Step 4. What is still left on each side
bank_left = bank[~bank["bank_id"].isin(matched["bank_id"])]
gl_left = gl[~gl["gl_id"].isin(matched["gl_id"])]
print(f"\nStill not matched:  bank {len(bank_left)} (EUR {bank_left['amount'].sum():,.2f})"
      f"   GL {len(gl_left)} (EUR {gl_left['amount'].sum():,.2f})")

# Step 5. Save. These matches need a GL correction: the reference must be fixed.
matched["action"] = "Correct GL reference to match bank"
matched[["bank_id", "gl_id", "date", "amount_bank", "reference_bank", "reference_gl", "action"]] \
    .to_csv(OUT / "matched_date_amount.csv", index=False, date_format="%Y-%m-%d")
cols = ["cents", "n", "date"]
bank_left.drop(columns=cols).to_csv(OUT / "bank_unmatched_2.csv", index=False, date_format="%Y-%m-%d")
gl_left.drop(columns=cols).to_csv(OUT / "gl_unmatched_2.csv", index=False, date_format="%Y-%m-%d")
print("\nSaved output/matched_date_amount.csv, output/bank_unmatched_2.csv, output/gl_unmatched_2.csv")