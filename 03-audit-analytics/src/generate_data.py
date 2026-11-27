"""
Generate 12 months (Nov 2025 - Oct 2026) of fake accounting data for the same 130-room luxury
hotel in Budapest, for an audit-analytics exercise.

Two datasets, the two things auditors test most:
    payments.csv          every supplier payment (accounts payable)
    journal_entries.csv   every journal entry posted to the general ledger
plus
    vendors.csv           the vendor master file (who the hotel is allowed to pay)
    answer_key.csv        the planted problems: DON'T open it until the end!

Most data is normal. A few problems are planted, the kind auditors look for:
    Payments
        duplicate_exact      the same invoice paid twice (same vendor, invoice number and amount)
        duplicate_near       paid twice, but the invoice number was retyped slightly differently
        below_limit_scheme   a new vendor receiving many payments just under the EUR 10,000
                             approval limit, entered and approved by the same clerk
    Journal entries
        weekend_manual       manual entries posted on a Saturday or Sunday
        after_hours          manual entries posted late at night
        round_amount         large manual entries with suspiciously round amounts
        below_je_limit       manual entries just under the EUR 50,000 review limit
        self_approved        the person who posted the entry also approved it

Control rules (what the tests check against):
    payments of EUR 10,000 or more need the financial controller's approval
    manual journal entries of EUR 50,000 or more need the controller's review
    nobody may approve their own payment or journal entry

Run from the project folder:
    cd 03-audit-analytics
    python3 src/generate_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(2026)  # fixed seed -> same data every run (like set.seed() in R)

DATA = Path(__file__).resolve().parent.parent / "data"
START = pd.Timestamp("2025-11-01")
END = pd.Timestamp("2026-10-31")
PAYMENT_LIMIT = 10_000   # EUR: payments at or above this need the controller
JE_LIMIT = 50_000        # EUR: manual journal entries at or above this need the controller

CONTROLLER = "mtoth"                   # financial controller (approves big items)
CLERKS = ["kszabo", "bkovacs"]         # accounts payable clerks (enter payments)
ACCOUNTANTS = ["anagy", "bkovacs"]     # post manual journal entries

answer_key = []  # one dict per planted problem


def business_days(start, end):
    """All Monday-Friday dates between start and end."""
    return pd.bdate_range(start, end)


BDAYS = business_days(START, END)


def random_bday(after=START, before=END):
    days = BDAYS[(BDAYS >= after) & (BDAYS <= before)]
    return days[rng.integers(0, len(days))]


def office_time():
    """A time during normal office hours, 08:00-18:00."""
    return f"{rng.integers(8, 18):02d}:{rng.integers(0, 60):02d}"


# ---------------------------------------------------------------------------
# 1. Vendor master file
# ---------------------------------------------------------------------------
#  name,                         typical payment (EUR), payments per year
VENDOR_PROFILE = [
    ("Metro Kft",                  2_500, 260),
    ("Budapest Fresh Produce",     1_200, 300),
    ("Fish Market Hungary",        1_800, 150),
    ("Wine Cellar Tokaj",          3_500, 80),
    ("Zwack Unicum",               1_500, 60),
    ("Coffee Bean Ltd",              900, 120),
    ("Hungarian Linen Services",   4_000, 100),
    ("Laundry Pro Kft",            2_800, 110),
    ("Cleaning Supplies Kft",        700, 140),
    ("Florist Bp",                 1_100, 90),
    ("Elektro Energia",           18_000, 12),
    ("Fovarosi Vizmuvek",          6_000, 12),
    ("IT Systems Zrt",             4_500, 40),
    ("Opera Hospitality Software", 9_000, 12),
    ("Schindler Lifts",            3_200, 24),
    ("Securitas Hungary",          7_500, 12),
    ("Marketing Partners Kft",     6_500, 30),
    ("Uniform Factory",            2_200, 20),
    ("Pest Plumbing Services",       800, 60),
    ("Spa Products Europe",        2_600, 45),
]
SHELL_VENDOR = "Pannon Advisory Kft"   # created during the year, used by the planted scheme

vendors = []
for i, (name, _, _) in enumerate(VENDOR_PROFILE, start=1):
    vendors.append({"vendor_id": f"V{i:03d}", "vendor_name": name,
                    "created_date": pd.Timestamp("2019-01-15") + pd.Timedelta(days=int(rng.integers(0, 1800))),
                    "created_by": "admin"})
vendors.append({"vendor_id": "V021", "vendor_name": SHELL_VENDOR,
                "created_date": pd.Timestamp("2026-03-09"), "created_by": "kszabo"})
vendors = pd.DataFrame(vendors)
VENDOR_ID = dict(zip(vendors["vendor_name"], vendors["vendor_id"]))

# ---------------------------------------------------------------------------
# 2. Normal supplier payments
#    Amounts follow a log-normal distribution around each vendor's typical size: many small,
#    few large. Natural data like this follows Benford's Law.
# ---------------------------------------------------------------------------
payments = []
invoice_no = 40_000
for name, typical, per_year in VENDOR_PROFILE:
    for _ in range(per_year):
        invoice_no += 1
        amount = round(float(rng.lognormal(np.log(typical), 0.9)), 2)
        pay_date = random_bday()
        entered = CLERKS[rng.integers(0, 2)]
        # control: >= limit -> controller approves; below -> the other clerk approves
        approver = CONTROLLER if amount >= PAYMENT_LIMIT else [c for c in CLERKS if c != entered][0]
        payments.append({"vendor_name": name, "invoice_no": f"INV-{invoice_no}",
                         "invoice_date": pay_date - pd.Timedelta(days=int(rng.integers(5, 30))),
                         "payment_date": pay_date, "amount": amount,
                         "entered_by": entered, "approved_by": approver, "_issue": ""})

# ---------------------------------------------------------------------------
# 3. Plant the payment problems
# ---------------------------------------------------------------------------
# Pick 10 different normal payments to duplicate: 6 exact copies, 4 with a retyped invoice number
picked = rng.choice(len(payments), size=10, replace=False)

# 3a. duplicate_exact: the same invoice paid again 6-20 days later
for idx in picked[:6]:
    original = payments[idx]
    copy = dict(original)
    copy["payment_date"] = original["payment_date"] + pd.Timedelta(days=int(rng.integers(6, 21)))
    copy["_issue"] = "duplicate_exact"
    payments.append(copy)
    answer_key.append({"dataset": "payments", "issue": "duplicate_exact", "key": original["invoice_no"],
                       "amount": original["amount"], "note": f"{original['vendor_name']}: paid twice"})

# 3b. duplicate_near: paid again, invoice number retyped (two digits swapped or a suffix added)
for n, idx in enumerate(picked[6:]):
    original = payments[idx]
    digits = original["invoice_no"][4:]
    retyped = (digits[:-2] + digits[-1] + digits[-2]) if n % 2 == 0 else digits + "A"
    copy = dict(original)
    copy["invoice_no"] = f"INV-{retyped}"
    copy["payment_date"] = original["payment_date"] + pd.Timedelta(days=int(rng.integers(3, 15)))
    copy["_issue"] = "duplicate_near"
    payments.append(copy)
    answer_key.append({"dataset": "payments", "issue": "duplicate_near",
                       "key": f"{original['invoice_no']} / INV-{retyped}", "amount": original["amount"],
                       "note": f"{original['vendor_name']}: paid twice, invoice number retyped"})

# 3c. below_limit_scheme: the new vendor gets 18 payments of EUR 9,400-9,990, all entered AND
#     approved by kszabo (self-approval), always just under the controller's limit
for n in range(18):
    amount = round(float(rng.uniform(9_400, 9_990)), 2)
    pay_date = random_bday(after=pd.Timestamp("2026-03-16"))
    payments.append({"vendor_name": SHELL_VENDOR, "invoice_no": f"PA-{101 + n}",
                     "invoice_date": pay_date - pd.Timedelta(days=2), "payment_date": pay_date,
                     "amount": amount, "entered_by": "kszabo", "approved_by": "kszabo",
                     "_issue": "below_limit_scheme"})
    answer_key.append({"dataset": "payments", "issue": "below_limit_scheme", "key": SHELL_VENDOR,
                       "amount": amount, "note": "new vendor, just under EUR 10,000, self-approved"})

payments = pd.DataFrame(payments)
payments.insert(0, "vendor_id", payments["vendor_name"].map(VENDOR_ID))
payments = payments.sort_values(["payment_date", "vendor_id"]).reset_index(drop=True)
payments.insert(0, "payment_id", [f"P{n:05d}" for n in range(1, len(payments) + 1)])

# ---------------------------------------------------------------------------
# 4. Normal journal entries
#    AUTO entries come from hotel systems (POS, payroll, PMS) every day, weekends included:
#    a hotel trades 7 days a week. MANUAL entries are typed by accountants on weekdays.
# ---------------------------------------------------------------------------
ACCOUNTS = {
    1100: "Bank", 1200: "Trade receivables", 2000: "Trade payables", 2100: "Accrued expenses",
    2300: "VAT payable", 4000: "Rooms revenue", 4100: "Food and beverage revenue",
    4200: "Spa revenue", 5000: "Food and beverage cost", 6000: "Salaries",
    6100: "Utilities", 6200: "Repairs and maintenance", 6300: "Marketing",
    6400: "Consulting fees", 6500: "Rent", 6810: "Bank charges", 7900: "Interest income",
}

jes = []
all_days = pd.date_range(START, END, freq="D")

# 4a. AUTO: daily revenue postings from the PMS/POS, 3 per day, every day
for day in all_days:
    for credit, typical, desc in [(4000, 22_000, "PMS night audit: rooms revenue"),
                                  (4100, 7_000, "POS: food and beverage revenue"),
                                  (4200, 1_500, "POS: spa revenue")]:
        jes.append({"posting_date": day, "posting_time": f"0{rng.integers(2, 4)}:{rng.integers(0, 60):02d}",
                    "source": "AUTO", "posted_by": "system", "approved_by": "system",
                    "debit_account": 1200, "credit_account": credit,
                    "amount": round(float(rng.lognormal(np.log(typical), 0.35)), 2),
                    "description": desc, "_issue": ""})

# 4b. AUTO: payroll twice a month
for month_start in pd.date_range(START, END, freq="MS"):
    for day_of_month in (10, 25):
        day = month_start + pd.Timedelta(days=day_of_month - 1)
        jes.append({"posting_date": day, "posting_time": "06:00", "source": "AUTO", "posted_by": "system",
                    "approved_by": "system", "debit_account": 6000, "credit_account": 1100,
                    "amount": round(float(rng.normal(228_000, 6_000)), 2),
                    "description": "Payroll run", "_issue": ""})

# 4c. MANUAL: accruals, reclassifications, corrections by the accountants, weekdays in office hours
MANUAL_TEMPLATES = [
    (5000, 2100, 6_000, "Accrual: food deliveries not yet invoiced"),
    (6100, 2100, 9_000, "Accrual: utilities estimate"),
    (6200, 2000, 3_500, "Reclass: repairs booked to wrong account"),
    (6300, 2100, 5_000, "Accrual: marketing campaign"),
    (2300, 1100, 40_000, "VAT payment"),
    (6810, 1100, 400, "Bank charges"),
    (1100, 7900, 300, "Interest received"),
    (4000, 1200, 1_200, "Correction: room charge reversed"),
]
for _ in range(560):
    debit, credit, typical, desc = MANUAL_TEMPLATES[rng.integers(0, len(MANUAL_TEMPLATES))]
    amount = round(float(rng.lognormal(np.log(typical), 0.7)), 2)
    posted_by = ACCOUNTANTS[rng.integers(0, 2)]
    jes.append({"posting_date": random_bday(), "posting_time": office_time(), "source": "MANUAL",
                "posted_by": posted_by,
                "approved_by": CONTROLLER if amount >= JE_LIMIT or rng.random() < 0.5
                               else [a for a in ACCOUNTANTS if a != posted_by][0],
                "debit_account": debit, "credit_account": credit, "amount": amount,
                "description": desc, "_issue": ""})

# 4d. MANUAL but legitimate and ROUND: the monthly laundry-facility rent, EUR 12,000.00.
#     A round-amount test will flag these too: a false positive the auditor must clear.
for month_start in pd.date_range(START, END, freq="MS"):
    day = BDAYS[BDAYS >= month_start][0]
    jes.append({"posting_date": day, "posting_time": "09:15", "source": "MANUAL", "posted_by": "anagy",
                "approved_by": CONTROLLER, "debit_account": 6500, "credit_account": 2000,
                "amount": 12_000.00, "description": "Rent: laundry facility (contract L-2019-04)",
                "_issue": ""})

# ---------------------------------------------------------------------------
# 5. Plant the journal-entry problems
# ---------------------------------------------------------------------------
def plant(issue, day, time, posted_by, approved_by, debit, credit, amount, desc):
    jes.append({"posting_date": pd.Timestamp(day), "posting_time": time, "source": "MANUAL",
                "posted_by": posted_by, "approved_by": approved_by, "debit_account": debit,
                "credit_account": credit, "amount": amount, "description": desc, "_issue": issue})


# weekend_manual: manual entries on Saturdays/Sundays (6)
for day, amount, desc in [("2025-12-13", 7_412.60, "Accrual: utilities estimate"),
                          ("2026-01-18", 3_905.10, "Reclass: repairs booked to wrong account"),
                          ("2026-04-04", 15_230.00, "Accrual: marketing campaign"),
                          ("2026-06-21", 2_118.45, "Correction: room charge reversed"),
                          ("2026-08-08", 8_760.90, "Accrual: food deliveries not yet invoiced"),
                          ("2026-09-27", 4_480.25, "Reclass: repairs booked to wrong account")]:
    plant("weekend_manual", day, office_time(), "bkovacs", CONTROLLER, 6200, 2100, amount, desc)

# after_hours: manual entries between 22:00 and 05:00 on weekdays (5)
for day, time, amount in [("2025-11-19", "23:12", 6_340.00), ("2026-02-10", "22:47", 11_905.35),
                          ("2026-05-06", "01:30", 4_212.80), ("2026-07-15", "23:58", 9_031.15),
                          ("2026-10-21", "04:05", 2_786.40)]:
    plant("after_hours", day, time, "anagy", CONTROLLER, 6300, 2100, amount, "Accrual: marketing campaign")

# round_amount: big manual entries with round amounts and vague descriptions (5)
for day, amount, desc in [("2025-12-30", 25_000.00, "Adjustment"), ("2026-03-31", 40_000.00, "Year-end provision"),
                          ("2026-06-30", 30_000.00, "Adjustment per management"),
                          ("2026-09-30", 20_000.00, "Reclass"), ("2026-10-30", 35_000.00, "Adjustment")]:
    plant("round_amount", day, office_time(), "bkovacs", CONTROLLER, 2100, 4000, amount, desc)

# below_je_limit: manual entries just under the EUR 50,000 review limit (4)
for day, amount in [("2026-02-26", 49_850.00), ("2026-05-28", 49_620.40),
                    ("2026-08-27", 49_975.10), ("2026-10-29", 49_700.00)]:
    plant("below_je_limit", day, office_time(), "anagy", "bkovacs", 6400, 2000, amount,
          "Consulting fees: Pannon Advisory")

# self_approved: posted and approved by the same person (4)
for day, amount in [("2026-01-29", 18_340.75), ("2026-04-16", 7_605.00),
                    ("2026-07-09", 26_480.30), ("2026-09-17", 12_150.60)]:
    plant("self_approved", day, office_time(), "kszabo", "kszabo", 6400, 2000, amount,
          "Consulting fees: Pannon Advisory")

# One entry that breaks several rules at once: Saturday, 23:41, just under the limit,
# self-approved, round-ish, to consulting fees. A risk score should rank it first.
plant("multiple_red_flags", "2026-10-31", "23:41", "kszabo", "kszabo", 6400, 2000, 49_900.00,
      "Adjustment")

jes = pd.DataFrame(jes)
jes = jes.sort_values(["posting_date", "posting_time"]).reset_index(drop=True)
jes.insert(0, "je_id", [f"JE{n:05d}" for n in range(1, len(jes) + 1)])
jes.insert(jes.columns.get_loc("debit_account") + 1, "debit_name", jes["debit_account"].map(ACCOUNTS))
jes.insert(jes.columns.get_loc("credit_account") + 1, "credit_name", jes["credit_account"].map(ACCOUNTS))

for _, row in jes[jes["_issue"] != ""].iterrows():
    answer_key.append({"dataset": "journal_entries", "issue": row["_issue"], "key": row["je_id"],
                       "amount": row["amount"], "note": f"{row['posting_date']:%a %d %b} {row['posting_time']}, "
                                                        f"posted by {row['posted_by']}, approved by {row['approved_by']}"})

# ---------------------------------------------------------------------------
# 6. Save (the hidden _issue columns are dropped: the auditor must find the problems)
# ---------------------------------------------------------------------------
DATA.mkdir(exist_ok=True)
vendors.to_csv(DATA / "vendors.csv", index=False, date_format="%Y-%m-%d")
payments.drop(columns="_issue").to_csv(DATA / "payments.csv", index=False, date_format="%Y-%m-%d")
jes.drop(columns="_issue").to_csv(DATA / "journal_entries.csv", index=False, date_format="%Y-%m-%d")
key = pd.DataFrame(answer_key)
key.to_csv(DATA / "answer_key.csv", index=False)

print(f"Vendors:          {len(vendors):>6,}")
print(f"Payments:         {len(payments):>6,}   total EUR {payments['amount'].sum():>14,.2f}")
print(f"Journal entries:  {len(jes):>6,}   ({(jes['source'] == 'MANUAL').sum()} manual, "
      f"{(jes['source'] == 'AUTO').sum()} automatic)")
print(f"Planted problems: {len(key):>6}   (see data/answer_key.csv only at the end)")
