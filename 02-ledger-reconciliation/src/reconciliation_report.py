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
from openpyxl.styles import Alignment, Font, PatternFill

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

# Step 5. The correcting journal entries (double entry: every entry has a debit and a credit).
#         Timing items need no entry: they clear by themselves in November.
ACCOUNTS = {
    1100: "Bank (operating account)",
    1200: "Trade receivables",
    2000: "Trade payables",
    2450: "Unallocated receipts (suspense)",
    6810: "Bank charges",
    7900: "Interest income",
}


def counter_account(amount):
    """Receipts (money in) were booked against receivables, payments (money out) against payables."""
    return 1200 if amount > 0 else 2000


entries = []  # one dict per journal entry
for _, row in exc.iterrows():
    cat, side, amount = row["category"], row["side"], row["amount"]
    if cat == "Bank fee not booked":
        effect, counter, text = amount, 6810, f"Book bank charge: {row['description'].title()}"
    elif cat == "Interest not booked":
        effect, counter, text = amount, 7900, "Book interest credited by the bank"
    elif cat == "Unidentified receipt":
        effect, counter, text = amount, 2450, f"Park unidentified receipt ({row['reference']}) until the guest is found"
    elif cat == "Duplicate GL posting":
        effect, counter, text = -amount, counter_account(amount), f"Reverse duplicate posting {row['reference']}"
    elif cat == "GL amount error" and side == "GL":
        bank_amount = exc.loc[(exc["reference"] == row["reference"]) & (exc["side"] == "Bank"), "amount"].iloc[0]
        effect = bank_amount - amount
        counter = counter_account(amount)
        text = f"Correct {row['reference']}: booked {amount:,.2f}, bank shows {bank_amount:,.2f}"
    else:
        continue  # timing items, and the bank side of an amount error, need no entry

    # effect = change to the bank account (1100). Money into the bank is a DEBIT to 1100.
    debit, credit = (1100, counter) if effect > 0 else (counter, 1100)
    entries.append({"date": "2026-10-31", "debit_account": f"{debit} {ACCOUNTS[debit]}",
                    "credit_account": f"{credit} {ACCOUNTS[credit]}", "amount": round(abs(effect), 2),
                    "description": text, "source": row["id"], "effect_on_bank_account": round(effect, 2)})

journal = pd.DataFrame(entries)
print(f"Correcting journal entries: {len(journal)}")
print(journal[["debit_account", "credit_account", "amount", "description"]].to_string(index=False))

# The entries must move the GL exactly to the adjusted GL balance
assert abs(journal["effect_on_bank_account"].sum() - (adjusted_gl - gl_balance)) < 0.01, \
    "Journal entries don't add up to the GL adjustments"

# Step 6. One Excel file with four sheets, formatted for a finance manager
matched_1 = pd.read_csv(OUT / "matched_exact.csv")
matched_2 = pd.read_csv(OUT / "matched_date_amount.csv")
matched = pd.concat([
    pd.DataFrame({"bank_id": matched_1["bank_id"], "gl_id": matched_1["gl_id"],
                  "reference_bank": matched_1["reference"], "reference_gl": matched_1["reference"],
                  "amount": matched_1["amount_bank"], "match_pass": "1: reference + amount", "action": ""}),
    pd.DataFrame({"bank_id": matched_2["bank_id"], "gl_id": matched_2["gl_id"],
                  "reference_bank": matched_2["reference_bank"], "reference_gl": matched_2["reference_gl"],
                  "amount": matched_2["amount_bank"], "match_pass": "2: date + amount", "action": matched_2["action"]}),
], ignore_index=True)

SHEETS = [  # (sheet name, table, readable column headers)
    ("Reconciliation", statement, {"section": "Section", "line": "Line", "amount_eur": "Amount (EUR)"}),
    ("Exceptions", exc, {"side": "Side", "id": "ID", "date": "Date", "description": "Description",
                         "reference": "Reference", "amount": "Amount (EUR)", "category": "Category",
                         "action": "Action"}),
    ("Journal entries", journal.drop(columns="effect_on_bank_account"),
     {"date": "Date", "debit_account": "Debit", "credit_account": "Credit", "amount": "Amount (EUR)",
      "description": "Description", "source": "Source line"}),
    ("Matched", matched, {"bank_id": "Bank ID", "gl_id": "GL ID", "reference_bank": "Reference (bank)",
                          "reference_gl": "Reference (GL)", "amount": "Amount (EUR)",
                          "match_pass": "Matched by", "action": "Action"}),
]

HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")   # dark blue header row
TOTAL_FILL = PatternFill("solid", fgColor="DDEBF7")    # light blue for key result lines
EUR = "#,##0.00;(#,##0.00)"                             # 1,234.56 and (1,234.56) for negatives

report = OUT / "reconciliation_oct2026.xlsx"
with pd.ExcelWriter(report, engine="openpyxl") as xl:
    for name, table, headers in SHEETS:
        table.rename(columns=headers).to_excel(xl, sheet_name=name, index=False)
        ws = xl.sheets[name]
        for cell in ws[1]:                                      # header row
            cell.font, cell.fill = HEADER_FONT, HEADER_FILL
            cell.alignment = Alignment(vertical="center")
        for col in ws.columns:                                  # widths and number formats
            width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(12, width + 2), 60)
            if col[0].value == "Amount (EUR)":
                for cell in col[1:]:
                    cell.number_format = EUR
        ws.freeze_panes = "A2"

    # Highlight the result lines on the reconciliation sheet
    ws = xl.sheets["Reconciliation"]
    for row in ws.iter_rows(min_row=2):
        if row[1].value.startswith(("Adjusted", "Difference")):
            for cell in row:
                cell.font, cell.fill = Font(bold=True), TOTAL_FILL

print(f"Saved {report.relative_to(PROJECT)}")
