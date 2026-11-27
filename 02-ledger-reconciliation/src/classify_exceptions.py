"""
Task 4: classify every line that is still unmatched after Tasks 2 and 3, and say what the
finance team should do about it.

Categories:
    GL amount error        same reference on both sides, different amount -> correct the GL
    Duplicate GL posting   GL entry whose reference was already matched -> reverse the copy
    Deposit in transit     money in, booked in the GL at month-end, bank pays it in November -> timing only
    Outstanding payment    money out, booked at month-end, bank clears it in November -> timing only
    Bank fee not booked    on the bank statement only -> book the expense in the GL
    Interest not booked    on the bank statement only -> book the income in the GL
    Unidentified receipt   money in the bank, no GL entry -> find out who paid and why

Needs Tasks 2 and 3 first.

Run from the project folder:
    cd 02-ledger-reconciliation
    python3 src/classify_exceptions.py
"""

from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "output"
MONTH_END = pd.Timestamp("2026-10-31")
TIMING_WINDOW_DAYS = 3  # GL entries this close to month-end can still be "on their way"

# Step 1. Load what is left, plus the Task 2 matches (needed to spot duplicates)
bank = pd.read_csv(OUT / "bank_unmatched_2.csv", parse_dates=["value_date"])
gl = pd.read_csv(OUT / "gl_unmatched_2.csv", parse_dates=["posting_date"])
matched_exact = pd.read_csv(OUT / "matched_exact.csv")
print(f"Lines to classify:  bank {len(bank)}   GL {len(gl)}")

exceptions = []  # one dict per line, like building a list of rows in R


def add(side, row, category, action):
    """Add one line to the exception list."""
    date = row["value_date"] if side == "Bank" else row["posting_date"]
    line_id = row["bank_id"] if side == "Bank" else row["gl_id"]
    exceptions.append({"side": side, "id": line_id, "date": date, "description": row["description"],
                       "reference": row["reference"], "amount": row["amount"],
                       "category": category, "action": action})


# Step 2. GL amount errors: the same reference is left on BOTH sides
same_ref = set(bank["reference"]) & set(gl["reference"])  # & = intersect() in R
for ref in sorted(same_ref):
    b = bank[bank["reference"] == ref].iloc[0]
    g = gl[gl["reference"] == ref].iloc[0]
    diff = g["amount"] - b["amount"]
    add("GL", g, "GL amount error",
        f"Correct GL by {-diff:+,.2f} (bank shows {b['amount']:,.2f})")
    add("Bank", b, "GL amount error", f"Matches {g['gl_id']} once the GL is corrected")

bank = bank[~bank["reference"].isin(same_ref)]
gl = gl[~gl["reference"].isin(same_ref)]

# Step 3. GL-only lines
for _, g in gl.iterrows():
    days_before_end = (MONTH_END - g["posting_date"]).days
    if g["reference"] in set(matched_exact["reference"]):
        add("GL", g, "Duplicate GL posting", "Reverse the second posting")
    elif days_before_end < TIMING_WINDOW_DAYS and g["amount"] > 0:
        add("GL", g, "Deposit in transit", "Timing only: check it arrives in early November")
    elif days_before_end < TIMING_WINDOW_DAYS and g["amount"] < 0:
        add("GL", g, "Outstanding payment", "Timing only: check it clears in early November")
    else:
        add("GL", g, "Investigate", "No bank line found")

# Step 4. Bank-only lines
for _, b in bank.iterrows():
    text = b["description"].upper()
    if "FEE" in text:
        add("Bank", b, "Bank fee not booked", "Book bank charges expense in the GL")
    elif "INTEREST" in text:
        add("Bank", b, "Interest not booked", "Book interest income in the GL")
    elif b["amount"] > 0:
        add("Bank", b, "Unidentified receipt", "Find the guest/booking and book the receipt")
    else:
        add("Bank", b, "Investigate", "Unknown payment out: ask the bank")

# Step 5. Summary by category
exc = pd.DataFrame(exceptions)
summary = (exc.groupby(["category", "side"])
              .agg(lines=("id", "count"), amount=("amount", "sum"))
              .reset_index())
print("\n" + summary.to_string(index=False))
print(f"\nClassified {len(exc)} lines; 'Investigate' left: {(exc['category'] == 'Investigate').sum()}")

# Step 6. Save
exc.sort_values(["category", "side", "date"]).to_csv(OUT / "exceptions.csv", index=False,
                                                     date_format="%Y-%m-%d")
print("Saved output/exceptions.csv")