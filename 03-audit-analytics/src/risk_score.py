"""
Task 6: risk scoring. Combine every flag from Tasks 3-5 into one ranked list, so the auditor
knows what to look at first.

Each test gets a weight (points). A weight reflects how strongly the test points to a real
problem on its own:
    3 points: breaks a control outright (self-approval, duplicate payment, vendor created by the clerk who pays it)
    2 points: suggests someone is avoiding a control (just below a limit, near-duplicate)
    1 point:  unusual but often innocent (weekend, after hours, round amount, rare poster)
Score = sum of the points. Bands: High >= 5, Medium 3-4, Low 1-2.

Second round, the "link rule": auditors don't look at items one by one. Any item connected to a
vendor or user that already has several High items gets +2 ("linked to high-risk party"), because
an entry that is only mildly odd on its own matters more when it involves the same supplier.

Needs Tasks 3-5 first (it reads their output files).

Run from the project folder:
    cd 03-audit-analytics
    python3 src/risk_score.py
"""

from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"

WEIGHTS = {
    # payments
    "duplicate payment (exact)": 3,
    "duplicate payment (near)": 2,
    "self-approved payment": 3,
    "new vendor created by payment clerk": 3,
    "just below payment limit": 2,
    # journal entries
    "self-approved entry": 3,
    "just below review limit": 2,
    "weekend": 1,
    "after hours": 1,
    "round amount": 1,
    "rare poster": 1,
    # second round
    "linked to high-risk party": 2,
}

rows = []  # one dict per (item, flag)

# --- Payments: duplicates (Task 3). Flag the SECOND payment of each pair, the one paid in error.
payments = pd.read_csv(DATA / "payments.csv")
dups = pd.read_csv(OUT / "duplicate_payments.csv")
for _, d in dups.iterrows():
    flag = "duplicate payment (exact)" if d["test"].startswith("A") else "duplicate payment (near)"
    rows.append({"item": d["payment_id_2"], "flag": flag})

# --- Payments: control tests (Task 4). The 'tests' column lists the failed tests, separated by ';'
controls = pd.read_csv(OUT / "payment_control_findings.csv")
TEST_TO_FLAG = {"self-approved": "self-approved payment",
                "new vendor": "new vendor created by payment clerk",
                "just below": "just below payment limit"}
for _, c in controls.iterrows():
    for test in c["tests"].split("; "):
        for keyword, flag in TEST_TO_FLAG.items():
            if keyword in test:
                rows.append({"item": c["payment_id"], "flag": flag})

# --- Journal entries (Task 5). The 'flags' column lists the failed tests, separated by ', '
je_findings = pd.read_csv(OUT / "journal_entry_findings.csv")
JE_TO_FLAG = {"weekend": "weekend", "after_hours": "after hours", "round_amount": "round amount",
              "below_limit": "just below review limit", "self_approved": "self-approved entry",
              "rare_poster": "rare poster"}
for _, j in je_findings.iterrows():
    for test in j["flags"].split(", "):
        rows.append({"item": j["je_id"], "flag": JE_TO_FLAG[test]})

# --- Details for every payment and journal entry: date, who, counterparty, amount
pay = payments.rename(columns={"payment_id": "item", "payment_date": "date", "vendor_name": "counterparty",
                               "entered_by": "user"})[["item", "date", "user", "counterparty", "amount"]]
pay["type"] = "Payment"
je = pd.read_csv(DATA / "journal_entries.csv").rename(columns={"je_id": "item", "posting_date": "date",
                                                               "posted_by": "user"})
# "Consulting fees: Adjustment", but don't repeat the account name if the description starts with it
je["counterparty"] = [d if d.startswith(a) else f"{a}: {d}" for a, d in zip(je["debit_name"], je["description"])]
je = je[["item", "date", "user", "counterparty", "amount"]].assign(type="Journal entry")
details = pd.concat([pay, je], ignore_index=True)


def build_register(rows):
    """Score every flagged item and add its details. Returns one row per item, highest risk first."""
    flags = pd.DataFrame(rows).drop_duplicates()
    flags["points"] = flags["flag"].map(WEIGHTS)
    scores = (flags.groupby("item")
                   .agg(score=("points", "sum"), n_flags=("flag", "size"),
                        flags=("flag", lambda f: ", ".join(sorted(f))))
                   .reset_index())
    reg = scores.merge(details, on="item", how="left")
    reg["band"] = pd.cut(reg["score"], bins=[0, 2, 4, 100], labels=["Low", "Medium", "High"])
    return reg.sort_values(["score", "amount"], ascending=False).reset_index(drop=True)


# --- Round 1: score each item on its own flags
first = build_register(rows)

# --- Round 2: the link rule. Vendors and users with 3+ High items are "high-risk parties".
high = first[first["band"] == "High"]
risky_vendors = [v for v, n in high[high["type"] == "Payment"]["counterparty"].value_counts().items() if n >= 3]
risky_users = [u for u, n in high["user"].value_counts().items() if n >= 3]
print(f"High-risk parties after round 1: vendors {risky_vendors}, users {risky_users}")

for _, item in first.iterrows():
    mentions_vendor = any(v.split()[0].lower() in item["counterparty"].lower() for v in risky_vendors)
    if mentions_vendor or item["user"] in risky_users:
        rows.append({"item": item["item"], "flag": "linked to high-risk party"})

register = build_register(rows)
moved = register.merge(first[["item", "band"]], on="item", suffixes=("", "_before"))
moved = moved[moved["band"] != moved["band_before"]]
print(f"Items that moved up a band because of the link rule: {len(moved)}")
print(moved[["item", "user", "counterparty", "amount", "band_before", "band"]].to_string(index=False))
print()

register.insert(0, "rank", range(1, len(register) + 1))
register = register[["rank", "band", "score", "type", "item", "date", "user", "counterparty", "amount",
                     "n_flags", "flags"]]

# --- Report
print(f"Items flagged: {len(register)} ({(register['type'] == 'Payment').sum()} payments, "
      f"{(register['type'] == 'Journal entry').sum()} journal entries), EUR {register['amount'].sum():,.2f}\n")
summary = register.groupby("band", observed=True).agg(items=("item", "size"), amount=("amount", "sum"))
print(summary.round(2).to_string())

print("\nTop 15 items to review:")
top = register.head(15).copy()
top["counterparty"] = top["counterparty"].str[:38]
print(top[["rank", "band", "score", "type", "item", "date", "user", "counterparty", "amount"]]
      .to_string(index=False))

# Concentration: who is behind the high-risk items?
high = register[register["band"] == "High"]
print(f"\nHigh-risk items by user: {high['user'].value_counts().to_dict()}")
print(f"High-risk amount: EUR {high['amount'].sum():,.2f}")

register.to_csv(OUT / "risk_register.csv", index=False)
print("\nSaved output/risk_register.csv")
