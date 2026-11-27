"""
Task 5: the bank reconciliation statement and an Excel report for the finance manager.

A reconciliation statement adjusts BOTH balances:
    bank balance  + deposits in transit - outstanding payments          = adjusted bank balance
    GL balance    - duplicates +/- amount corrections + unbooked items  = adjusted GL balance
If the work is right, the two adjusted balances are equal.

Needs Tasks 2-4 first.

Run from the project folder:
    cd 02-ledger-reconciliation
    python3 src/reconciliation_report.py
"""

from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"
OPENING_BALANCE = 850_000.00  # EUR on 1 October, the same in bank and GL

# Step 1. Load the closing balances and the exception list
bank = pd.read_csv(DATA / "bank_statement.csv")
gl = pd.read_csv(DATA / "general_ledger.csv")
exc = pd.read_csv(OUT / "exceptions.csv")

bank_balance = bank["balance"].iloc[-1]                  # last running balance on the statement
gl_balance = OPENING_BALANCE + gl["amount"].sum()        # opening + everything booked


def total(category, side):
    """Sum of the amounts in one category on one side."""
    rows = exc[(exc["category"] == category) & (exc["side"] == side)]
    return rows["amount"].sum()


# Step 2. Bank side: add what the bank hasn't received or paid yet
deposits_in_transit = total("Deposit in transit", "GL")
outstanding_payments = total("Outstanding payment", "GL")      # already negative
adjusted_bank = bank_balance + deposits_in_transit + outstanding_payments

# Step 3. GL side: fix the errors and book what is missing
duplicates = -total("Duplicate GL posting", "GL")              # reverse the extra copies
amount_corrections = total("GL amount error", "Bank") - total("GL amount error", "GL")
bank_fees = total("Bank fee not booked", "Bank")
interest = total("Interest not booked", "Bank")
unidentified = total("Unidentified receipt", "Bank")
adjusted_gl = gl_balance + duplicates + amount_corrections + bank_fees + interest + unidentified

# Step 4. The statement as a table (one row per line, like a tibble)
statement = pd.DataFrame([
    ("BANK", "Balance per bank statement, 31 Oct 2026", bank_balance),
    ("BANK", "Add: deposits in transit", deposits_in_transit),
    ("BANK", "Less: outstanding payments", outstanding_payments),
    ("BANK", "Adjusted bank balance", adjusted_bank),
    ("GL", "Balance per general ledger (account 1100)", gl_balance),
    ("GL", "Less: duplicate postings reversed", duplicates),
    ("GL", "Add/less: amount corrections", amount_corrections),
    ("GL", "Less: bank fees not booked", bank_fees),
    ("GL", "Add: interest not booked", interest),
    ("GL", "Add: unidentified receipt (to investigate)", unidentified),
    ("GL", "Adjusted GL balance", adjusted_gl),
    ("CHECK", "Difference (must be 0.00)", round(adjusted_bank - adjusted_gl, 2) + 0.0),  # + 0.0 turns -0.00 into 0.00
], columns=["section", "line", "amount_eur"])

print(statement.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
assert abs(adjusted_bank - adjusted_gl) < 0.01, "Reconciliation does not balance!"
print("\nReconciled: adjusted bank = adjusted GL")

# Step 5. The correcting journal entries the GL needs (timing items need none)
gl_errors = (exc["side"] == "GL") & exc["category"].isin(["Duplicate GL posting", "GL amount error"])
not_booked = (exc["side"] == "Bank") & exc["category"].isin(["Bank fee not booked", "Interest not booked",
                                                             "Unidentified receipt"])
to_book = exc[gl_errors | not_booked]  # | means OR, like in R
print(f"Correcting entries to book: {len(to_book)}")

# Step 6. Write one Excel file with four sheets
matched = pd.concat([pd.read_csv(OUT / "matched_exact.csv").assign(match_pass="1: reference + amount"),
                     pd.read_csv(OUT / "matched_date_amount.csv").assign(match_pass="2: date + amount")])
report = OUT / "reconciliation_oct2026.xlsx"
with pd.ExcelWriter(report, engine="openpyxl") as xl:
    statement.to_excel(xl, sheet_name="Reconciliation", index=False)
    exc.to_excel(xl, sheet_name="Exceptions", index=False)
    to_book.to_excel(xl, sheet_name="Entries to book", index=False)
    matched.to_excel(xl, sheet_name="Matched", index=False)

    # Make it readable: wider columns, amounts with thousands separators
    for ws in xl.book.worksheets:
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = max(12, max(len(str(c.value or "")) for c in col) + 2)
            for cell in col[1:]:
                if isinstance(cell.value, float):
                    cell.number_format = "#,##0.00;(#,##0.00)"
        ws.freeze_panes = "A2"

print(f"Saved {report.relative_to(PROJECT)}")