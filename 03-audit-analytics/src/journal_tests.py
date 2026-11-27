"""
Task 5: journal-entry tests. Which manual entries look like management override?

Auditing standards (ISA 240) require auditors to test journal entries, because people who
want to manipulate the accounts usually do it with MANUAL entries: automatic postings come
from systems and are much harder to fake. So every test here looks at manual entries only.

Tests (each adds a True/False column, like mutate(flag = ...) in R):
    1. weekend          posted on a Saturday or Sunday
    2. after_hours      posted between 22:00 and 05:59
    3. round_amount     EUR 10,000 or more and a whole multiple of 1,000
    4. below_limit      EUR 45,000-49,999.99, just under the EUR 50,000 review limit
    5. self_approved    posted_by == approved_by
    6. rare_poster      posted by someone who posts very few manual entries

Then: explain the false positives (recurring entries) and list entries hit by several tests.

Run from the project folder:
    cd 03-audit-analytics
    python3 src/journal_tests.py
"""

from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"
OUT.mkdir(exist_ok=True)

JE_LIMIT = 50_000
TESTS = ["weekend", "after_hours", "round_amount", "below_limit", "self_approved", "rare_poster"]

je = pd.read_csv(DATA / "journal_entries.csv", parse_dates=["posting_date"])
print(f"Journal entries: {len(je):,}  ({(je['source'] == 'AUTO').sum():,} automatic, "
      f"{(je['source'] == 'MANUAL').sum()} manual)")

# Why manual only? Show how many weekend entries there are in each group.
weekend_all = je["posting_date"].dt.dayofweek >= 5          # Monday = 0, Saturday = 5, Sunday = 6
print(f"Weekend entries: {weekend_all.sum()} in total, of which {(weekend_all & (je['source'] == 'MANUAL')).sum()} "
      f"manual. The hotel's systems post every night, so automatic weekend entries are normal.\n")

m = je[je["source"] == "MANUAL"].copy()
hour = m["posting_time"].str[:2].astype(int)                 # "23:41" -> 23

# The six tests
m["weekend"] = m["posting_date"].dt.dayofweek >= 5
m["after_hours"] = (hour >= 22) | (hour < 6)
m["round_amount"] = (m["amount"] >= 10_000) & (m["amount"] % 1_000 == 0)
m["below_limit"] = m["amount"].between(0.9 * JE_LIMIT, JE_LIMIT - 0.01)
m["self_approved"] = m["posted_by"] == m["approved_by"]
posts_per_user = m["posted_by"].value_counts()               # how many manual entries each person posts
m["rare_poster"] = m["posted_by"].map(posts_per_user) < 0.05 * len(m)

print("Manual entries posted per user:")
print(posts_per_user.to_string())
print()
for test in TESTS:
    hits = m[m[test]]
    print(f"{test:<14} {len(hits):>3} entries   EUR {hits['amount'].sum():>12,.2f}")

# False positives: the round-amount test also catches legitimate RECURRING entries, e.g. a
# fixed monthly rent. An entry with the same description and amount in 6+ months is recurring.
same_entry = m.groupby(["description", "amount"])["je_id"].transform("count")
m["recurring"] = same_entry >= 6
explained = m[m["round_amount"] & m["recurring"]]
print(f"\nRound amounts explained as recurring: {len(explained)} entries "
      f"({explained['description'].iloc[0]}, EUR {explained['amount'].iloc[0]:,.2f} a month)")
m.loc[m["recurring"], "round_amount"] = False                # cleared after review

# Count the tests each entry fails, and show the ones that fail more than one
m["n_flags"] = m[TESTS].sum(axis=1)                          # True counts as 1, like rowSums() in R
m["flags"] = m[TESTS].apply(lambda row: ", ".join(t for t in TESTS if row[t]), axis=1)
flagged = m[m["n_flags"] > 0].sort_values(["n_flags", "amount"], ascending=False)

print(f"\nManual entries with at least one flag: {len(flagged)} of {len(m)}")
print(flagged["n_flags"].value_counts().sort_index(ascending=False).rename("entries").to_string())

cols = ["je_id", "posting_date", "posting_time", "posted_by", "approved_by", "debit_name", "amount",
        "description", "flags"]
print("\nEntries with 2 or more flags:")
print(flagged[flagged["n_flags"] >= 2][cols].to_string(index=False))

# Link to the payment tests: which manual entries mention Pannon Advisory?
pannon = m[m["description"].str.contains("Pannon", case=False)]
print(f"\nManual entries mentioning Pannon Advisory: {len(pannon)}, EUR {pannon['amount'].sum():,.2f}, "
      f"posted by {', '.join(sorted(pannon['posted_by'].unique()))}")

flagged[["je_id", "posting_date", "posting_time", "posted_by", "approved_by", "debit_account", "debit_name",
         "credit_account", "credit_name", "amount", "description", "n_flags", "flags"]] \
    .to_csv(OUT / "journal_entry_findings.csv", index=False, date_format="%Y-%m-%d")
print("\nSaved output/journal_entry_findings.csv")
