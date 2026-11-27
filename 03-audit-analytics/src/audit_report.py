"""
Task 7: the audit report. Collects the results of Tasks 2-6 into one formatted Excel workbook
for the audit manager, then (finally!) opens the answer key to check whether the tests found
every planted problem, and how many false positives they raised.

Needs Tasks 2-6 first (it reads their output files).

Run from the project folder:
    cd 03-audit-analytics
    python3 src/audit_report.py
"""

from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"

payments = pd.read_csv(DATA / "payments.csv")
journals = pd.read_csv(DATA / "journal_entries.csv")
benford = pd.read_csv(OUT / "benford_first_digit.csv")
dups = pd.read_csv(OUT / "duplicate_payments.csv")
controls = pd.read_csv(OUT / "payment_control_findings.csv")
je_findings = pd.read_csv(OUT / "journal_entry_findings.csv")
register = pd.read_csv(OUT / "risk_register.csv")

# ---------------------------------------------------------------------------
# 1. Summary sheet: one line per test, the way an audit manager reads it
# ---------------------------------------------------------------------------
digit9 = benford[benford["digit"] == 9].iloc[0]
high = register[register["band"] == "High"]
summary = pd.DataFrame([
    ("Population", "Supplier payments", len(payments), payments["amount"].sum(), "Nov 2025 - Oct 2026"),
    ("Population", "Journal entries (manual)", (journals["source"] == "MANUAL").sum(),
     journals.loc[journals["source"] == "MANUAL", "amount"].sum(), "automatic entries excluded from JE tests"),
    ("Benford", "First digit 9", int(digit9["count"]), None,
     f"{digit9['observed_pct']:.1%} vs {digit9['expected_pct']:.1%} expected (z = {digit9['z']:.1f}); "
     "caused by Pannon Advisory Kft"),
    ("Duplicates", "Paid twice (exact + near)", len(dups), dups["amount"].sum(),
     "recover from vendors; AP system does not block repeated invoice numbers"),
    ("Payment controls", "Payments failing a control", len(controls), controls["amount"].sum(),
     "18 to Pannon Advisory: new vendor, just below EUR 10,000, self-approved by kszabo"),
    ("Journal entries", "Manual entries with a flag", len(je_findings), je_findings["amount"].sum(),
     "JE01716: Sat 31 Oct 23:41, EUR 49,900, self-approved, 5 of 6 tests"),
    ("Risk register", "High-risk items", len(high), high["amount"].sum(),
     f"all {len(high)} linked to user {high['user'].mode()[0]}; refer for fraud investigation"),
    ("Risk register", "All flagged items", len(register), register["amount"].sum(),
     f"{len(register)} of {len(payments) + len(journals):,} transactions "
     f"({len(register) / (len(payments) + len(journals)):.1%})"),
], columns=["area", "test", "items", "amount_eur", "conclusion"])
print(summary.drop(columns="conclusion").to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

# ---------------------------------------------------------------------------
# 2. Check against the answer key: did we find every planted problem?
# ---------------------------------------------------------------------------
key = pd.read_csv(DATA / "answer_key.csv")
flagged_payments = set(register.loc[register["type"] == "Payment", "item"])
flagged_jes = set(je_findings["je_id"])
pannon_ids = set(payments.loc[payments["vendor_name"] == "Pannon Advisory Kft", "payment_id"])


def found(row):
    """True if our tests flagged this planted problem."""
    if row["dataset"] == "journal_entries":
        return row["key"] in flagged_jes
    if row["issue"] == "duplicate_exact":
        return row["key"] in set(dups["invoice_no_1"])
    if row["issue"] == "duplicate_near":
        first, second = row["key"].split(" / ")
        return ((dups["invoice_no_1"] == first) & (dups["invoice_no_2"] == second)).any()
    if row["issue"] == "below_limit_scheme":
        return pannon_ids <= flagged_payments          # <= on sets: "all of these are in that"
    return False


key["found"] = key.apply(found, axis=1)
check = key.groupby("issue").agg(planted=("found", "size"), found=("found", "sum")).reset_index()
check["missed"] = check["planted"] - check["found"]
print(f"\nAnswer key check: found {key['found'].sum()} of {len(key)} planted problems")
print(check.to_string(index=False))

# False positives: flagged items that were NOT planted
planted_items = set(key.loc[key["dataset"] == "journal_entries", "key"]) | pannon_ids
dup_ids = set(dups["payment_id_2"])
false_pos = register[~register["item"].isin(planted_items | dup_ids)]
print(f"\nFalse positives (flagged but not planted): {len(false_pos)}, all in band "
      f"{sorted(false_pos['band'].unique())}")
print(false_pos[["item", "counterparty", "amount", "flags"]].to_string(index=False))

# ---------------------------------------------------------------------------
# 3. Excel workbook
# ---------------------------------------------------------------------------
SHEETS = [
    ("Summary", summary, {"area": "Area", "test": "Test", "items": "Items", "amount_eur": "Amount (EUR)",
                          "conclusion": "Conclusion"}),
    ("Risk register", register, {"rank": "Rank", "band": "Risk", "score": "Score", "type": "Type",
                                 "item": "ID", "date": "Date", "user": "User", "counterparty": "Counterparty",
                                 "amount": "Amount (EUR)", "n_flags": "Flags", "flags": "Flagged by"}),
    ("Duplicates", dups, {"test": "Test", "vendor_name": "Vendor", "payment_id_1": "Original",
                          "payment_id_2": "Duplicate", "invoice_no_1": "Invoice (original)",
                          "invoice_no_2": "Invoice (duplicate)", "invoice_similarity": "Similarity",
                          "amount": "Amount (EUR)", "payment_date_1": "Paid", "payment_date_2": "Paid again",
                          "days_apart": "Days apart"}),
    ("Payment controls", controls, {"payment_id": "Payment", "vendor_name": "Vendor", "amount": "Amount (EUR)",
                                    "n_tests": "Tests failed", "tests": "Which tests"}),
    ("Journal entries", je_findings.drop(columns=["debit_account", "credit_account"]),
     {"je_id": "Entry", "posting_date": "Date", "posting_time": "Time", "posted_by": "Posted by",
      "approved_by": "Approved by", "debit_name": "Debit", "credit_name": "Credit", "amount": "Amount (EUR)",
      "description": "Description", "n_flags": "Flags", "flags": "Flagged by"}),
    ("Benford", benford, {"digit": "First digit", "expected_pct": "Expected share", "count": "Count",
                          "observed_pct": "Observed share", "expected_count": "Expected count", "z": "z",
                          "significant": "Significant"}),
]
HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
BAND_FILL = {"High": PatternFill("solid", fgColor="FBE3D6"), "Medium": PatternFill("solid", fgColor="FFF2CC")}
EUR = "#,##0.00;(#,##0.00)"

report = OUT / "audit_report_fy2026.xlsx"
with pd.ExcelWriter(report, engine="openpyxl") as xl:
    for name, table, headers in SHEETS:
        table.rename(columns=headers).to_excel(xl, sheet_name=name, index=False)
        ws = xl.sheets[name]
        for cell in ws[1]:
            cell.font, cell.fill = HEADER_FONT, HEADER_FILL
            cell.alignment = Alignment(vertical="center")
        for col in ws.columns:
            width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 70)
            header = col[0].value
            for cell in col[1:]:
                if header == "Amount (EUR)":
                    cell.number_format = EUR
                elif header in ("Expected share", "Observed share"):
                    cell.number_format = "0.0%"
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions           # filter arrows on the header row

    # Colour the risk register by band
    ws = xl.sheets["Risk register"]
    for row in ws.iter_rows(min_row=2):
        fill = BAND_FILL.get(row[1].value)
        if fill:
            for cell in row:
                cell.fill = fill

print(f"\nSaved {report.relative_to(PROJECT)}")
