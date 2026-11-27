"""
Generate one month (October 2026) of fake bank and general-ledger (GL) data for the
operating bank account of a 130-room luxury hotel in Budapest.

Most transactions appear in both files and match. A few problems are planted on purpose,
the same kinds a hotel finance team finds at month-end:

    timing_deposit      card takings booked in the GL on 30-31 Oct, but the bank settles them in November
    outstanding_payment supplier payments booked in the GL, not yet cleared by the bank
    bank_fee            bank charges and card-terminal fees: on the bank statement, missing from the GL
    interest            interest credited by the bank, missing from the GL
    unidentified_receipt a guest transfer the bank received that nobody has booked in the GL
    amount_mismatch     same payment, but the GL amount has two digits swapped (e.g. 1,520 vs 1,250)
    duplicate_gl        an entry posted twice in the GL
    reference_typo      same date and amount, but the GL reference was typed wrongly

Output (in data/):
    bank_statement.csv   what the bank says happened
    general_ledger.csv   what the hotel booked (cash account 1100)
    answer_key.csv       the planted problems, so you can check your reconciliation at the end
                         (don't open it until you have built your own matching!)

Run from the project folder:
    cd 02-ledger-reconciliation
    python3 src/generate_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)  # fixed seed -> same data every run (like set.seed(7) in R)

DATA = Path(__file__).resolve().parent.parent / "data"
MONTH_START = pd.Timestamp("2026-10-01")
MONTH_END = pd.Timestamp("2026-10-31")
OPENING_BALANCE = 850_000.00  # EUR, the same in bank and GL on 1 October (last month was reconciled)

SUPPLIERS = ["Metro Kft", "Hungarian Linen Services", "Zwack Unicum", "Budapest Fresh Produce",
             "Elektro Energia", "Laundry Pro Kft", "Coffee Bean Ltd", "Wine Cellar Tokaj",
             "Florist Bp", "IT Systems Zrt", "Cleaning Supplies Kft", "Fish Market Hungary"]
CORPORATES = ["Siemens Hungary", "MOL Group", "Deloitte Budapest", "Audi Hungaria",
              "Richter Gedeon", "OTP Bank", "Telekom HU", "Wizz Air"]


def next_business_day(day):
    """Banks don't settle at weekends: Saturday/Sunday roll to Monday."""
    day = day + pd.Timedelta(days=1)
    while day.weekday() >= 5:  # Monday = 0 ... Saturday = 5, Sunday = 6
        day = day + pd.Timedelta(days=1)
    return day


def money(low, high):
    """Random amount with cents, e.g. 1234.56."""
    return round(float(rng.uniform(low, high)), 2)


# ---------------------------------------------------------------------------
# 1. Build the "true" list of cash movements. Each one has a GL side and a bank side.
#    A row = one transaction; positive = money in, negative = money out.
# ---------------------------------------------------------------------------
pairs = []  # one dict per transaction: gl_date, bank_date, amount, reference, descriptions

days = pd.date_range(MONTH_START, MONTH_END, freq="D")

# 1a. Daily card takings (Visa/Mastercard and Amex), settled by the bank the next business day
for day in days:
    for scheme, low, high in [("VISA/MC", 9_000, 26_000), ("AMEX", 1_500, 7_000)]:
        amount = money(low, high)
        ref = f"CARD-{scheme[:4]}-{day:%m%d}"
        pairs.append({"gl_date": day, "bank_date": next_business_day(day), "amount": amount,
                      "reference": ref, "source": "POS",
                      "gl_desc": f"Card takings {scheme} {day:%d/%m}",
                      "bank_desc": f"WORLDLINE SETTLEMENT {scheme}"})

# 1b. Corporate guests paying invoices by bank transfer (arrive 0-2 days after the GL date)
for i in range(40):
    day = days[rng.integers(0, len(days))]
    company = CORPORATES[rng.integers(0, len(CORPORATES))]
    ref = f"INV-26{1000 + i}"
    lag = int(rng.integers(0, 3))
    if day + pd.Timedelta(days=lag) > MONTH_END:  # keep these inside October; timing items are planted below
        lag = 0
    pairs.append({"gl_date": day, "bank_date": day + pd.Timedelta(days=lag),
                  "amount": money(800, 18_000), "reference": ref, "source": "AR",
                  "gl_desc": f"Receipt {company} {ref}", "bank_desc": f"TRANSFER IN {company.upper()}"})

# 1c. Supplier payments (same day in GL and bank)
for i in range(80):
    day = days[rng.integers(0, len(days) - 3)]  # leave the last 3 days for the planted ones
    supplier = SUPPLIERS[rng.integers(0, len(SUPPLIERS))]
    ref = f"PAY-{5000 + i}"
    pairs.append({"gl_date": day, "bank_date": day, "amount": -money(150, 9_500), "reference": ref,
                  "source": "AP", "gl_desc": f"Payment {supplier}", "bank_desc": f"TRANSFER OUT {supplier.upper()}"})

# 1d. Payroll and tax, utilities by direct debit
pairs += [
    {"gl_date": pd.Timestamp("2026-10-09"), "bank_date": pd.Timestamp("2026-10-09"), "amount": -312_480.55,
     "reference": "PAYROLL-2610", "source": "Payroll", "gl_desc": "Net salaries October",
     "bank_desc": "BULK PAYROLL OCT"},
    {"gl_date": pd.Timestamp("2026-10-12"), "bank_date": pd.Timestamp("2026-10-12"), "amount": -141_206.10,
     "reference": "NAV-2610", "source": "Payroll", "gl_desc": "Payroll taxes and contributions",
     "bank_desc": "NAV TAX PAYMENT"},
    {"gl_date": pd.Timestamp("2026-10-15"), "bank_date": pd.Timestamp("2026-10-15"), "amount": -18_940.00,
     "reference": "DD-ELEC-10", "source": "AP", "gl_desc": "Electricity October",
     "bank_desc": "DIRECT DEBIT ELEKTRO"},
    {"gl_date": pd.Timestamp("2026-10-20"), "bank_date": pd.Timestamp("2026-10-20"), "amount": -6_215.40,
     "reference": "DD-WATER-10", "source": "AP", "gl_desc": "Water and gas October",
     "bank_desc": "DIRECT DEBIT FOVAROSI VIZMUVEK"},
]

# ---------------------------------------------------------------------------
# 2. Plant the problems. answer_key collects what we planted.
# ---------------------------------------------------------------------------
answer_key = []

# 2a. timing_deposit: card takings of 30 and 31 Oct settle on 2 Nov -> GL only in October.
#     (1a already makes their bank_date fall in November, because of next_business_day.)
for p in pairs:
    if p["source"] == "POS" and p["bank_date"] > MONTH_END:
        p["issue"] = "timing_deposit"

# 2b. outstanding_payment: supplier payments booked 29-31 Oct that the bank clears in November
for i, (day, amount) in enumerate([("2026-10-29", -4_380.00), ("2026-10-30", -2_915.75),
                                   ("2026-10-31", -7_640.20)]):
    pairs.append({"gl_date": pd.Timestamp(day), "bank_date": pd.Timestamp("2026-11-02"), "amount": amount,
                  "reference": f"PAY-{5900 + i}", "source": "AP",
                  "gl_desc": f"Payment {SUPPLIERS[i]}", "bank_desc": f"TRANSFER OUT {SUPPLIERS[i].upper()}",
                  "issue": "outstanding_payment"})

# Split into a GL table and a bank table, keeping only what falls in October on each side
gl_rows, bank_rows = [], []
for n, p in enumerate(pairs, start=1):
    if p["gl_date"] <= MONTH_END:
        gl_rows.append({"posting_date": p["gl_date"], "account": 1100, "source": p["source"],
                        "description": p["gl_desc"], "reference": p["reference"], "amount": p["amount"],
                        "_pair": n, "_issue": p.get("issue", "")})
    if p["bank_date"] <= MONTH_END:
        bank_rows.append({"value_date": p["bank_date"], "description": p["bank_desc"],
                          "reference": p["reference"], "amount": p["amount"], "_pair": n})
gl = pd.DataFrame(gl_rows)
bank = pd.DataFrame(bank_rows)

for _, row in gl[gl["_issue"] != ""].iterrows():
    answer_key.append({"issue": row["_issue"], "reference": row["reference"], "amount_gl": row["amount"],
                       "amount_bank": None, "note": "in GL only (clears in November)"})

# 2c. bank_fee and interest: bank only
bank_only = [
    ("2026-10-31", "MONTHLY ACCOUNT FEE", "FEE-2610", -185.00, "bank_fee"),
    ("2026-10-31", "CARD TERMINAL FEES OCT", "FEE-POS-2610", -1_742.36, "bank_fee"),
    ("2026-10-31", "INTEREST CREDIT", "INT-2610", 412.18, "interest"),
    ("2026-10-22", "TRANSFER IN MR J SMITH", "BOOKING 48211", 2_340.00, "unidentified_receipt"),
]
for day, desc, ref, amount, issue in bank_only:
    bank.loc[len(bank)] = {"value_date": pd.Timestamp(day), "description": desc, "reference": ref,
                           "amount": amount, "_pair": 0}
    answer_key.append({"issue": issue, "reference": ref, "amount_gl": None, "amount_bank": amount,
                       "note": "on bank statement only"})

# 2d. amount_mismatch: two digits swapped in the GL
for ref, bank_amount, gl_amount in [("PAY-5011", -1_250.00, -1_520.00), ("INV-261007", 4_380.00, 4_830.00)]:
    i_gl = gl.index[gl["reference"] == ref][0]
    i_bank = bank.index[bank["reference"] == ref][0]
    gl.loc[i_gl, "amount"] = gl_amount
    bank.loc[i_bank, "amount"] = bank_amount
    answer_key.append({"issue": "amount_mismatch", "reference": ref, "amount_gl": gl_amount,
                       "amount_bank": bank_amount, "note": "digits swapped in the GL"})

# 2e. duplicate_gl: two entries posted twice
for ref in ["PAY-5023", "INV-261019"]:
    row = gl[gl["reference"] == ref].iloc[0].copy()
    gl.loc[len(gl)] = row
    answer_key.append({"issue": "duplicate_gl", "reference": ref, "amount_gl": row["amount"],
                       "amount_bank": None, "note": "posted twice in the GL"})

# 2f. reference_typo: right date and amount, wrong reference typed in the GL
for ref, typo in [("PAY-5040", "PAY-5400"), ("INV-261025", "INV-216025")]:
    i_gl = gl.index[gl["reference"] == ref][0]
    gl.loc[i_gl, "reference"] = typo
    answer_key.append({"issue": "reference_typo", "reference": f"{typo} (GL) / {ref} (bank)",
                       "amount_gl": gl.loc[i_gl, "amount"], "amount_bank": gl.loc[i_gl, "amount"],
                       "note": "same amount and date, reference typed wrongly"})

# ---------------------------------------------------------------------------
# 3. Tidy up: sort by date, give each row an ID, add running balances, save
# ---------------------------------------------------------------------------
gl = gl.sort_values(["posting_date", "reference"]).reset_index(drop=True)
gl.insert(0, "gl_id", [f"GL{n:04d}" for n in range(1, len(gl) + 1)])
bank = bank.sort_values(["value_date", "reference"]).reset_index(drop=True)
bank.insert(0, "bank_id", [f"BK{n:04d}" for n in range(1, len(bank) + 1)])
bank["balance"] = (OPENING_BALANCE + bank["amount"].cumsum()).round(2)

gl = gl.drop(columns=["_pair", "_issue"])
bank = bank.drop(columns=["_pair"])

DATA.mkdir(exist_ok=True)
gl.to_csv(DATA / "general_ledger.csv", index=False, date_format="%Y-%m-%d")
bank.to_csv(DATA / "bank_statement.csv", index=False, date_format="%Y-%m-%d")
pd.DataFrame(answer_key).to_csv(DATA / "answer_key.csv", index=False)

# Self-check: the planted problems must explain the whole difference between the two balances
key = pd.DataFrame(answer_key)
explained = (key.loc[key["note"].str.startswith("in GL only"), "amount_gl"].sum()      # GL has it, bank not yet
             + key.loc[key["issue"] == "duplicate_gl", "amount_gl"].sum()             # extra copy in GL
             + (key.loc[key["issue"] == "amount_mismatch", "amount_gl"]
                - key.loc[key["issue"] == "amount_mismatch", "amount_bank"]).sum()    # GL typed wrong
             - key.loc[key["note"] == "on bank statement only", "amount_bank"].sum()) # bank has it, GL not
gl_close = OPENING_BALANCE + gl["amount"].sum()
bank_close = bank["balance"].iloc[-1]
print(f"General ledger: {len(gl)} rows, closing balance EUR {gl_close:,.2f}")
print(f"Bank statement: {len(bank)} rows, closing balance EUR {bank_close:,.2f}")
print(f"Difference to explain: EUR {gl_close - bank_close:,.2f}")
assert abs((gl_close - bank_close) - explained) < 0.01, "planted problems don't explain the difference"
assert gl["reference"].duplicated().sum() == 2, "only the two planted duplicates should repeat"
print(f"Planted problems: {len(answer_key)} (see data/answer_key.csv only at the end)")
