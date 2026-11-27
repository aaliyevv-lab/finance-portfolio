# Ledger reconciliation: does the bank agree with the books?

**Business problem.** At every month-end a hotel finance team checks that the cash account in
the general ledger (GL) agrees with the bank statement. When the balances differ, every
difference has to be found, explained and, where it is an error, corrected.

**What I'm doing.** Reconciling one month (October 2026) of a 130-room Budapest luxury hotel's
operating bank account in Python: matching bank lines to GL entries, flagging exceptions,
exporting an exception report to Excel, then a budget-vs-actual variance analysis.

*Status: in progress (Task 1 of 6 done: data generated).*

## Data (synthetic, `src/generate_data.py`, fixed seed)
| File | Rows | What it is |
|---|---|---|
| `data/general_ledger.csv` | 191 | What the hotel booked in cash account 1100 |
| `data/bank_statement.csv` | 186 | What the bank says happened, with running balance |
| `data/answer_key.csv` | 17 | The planted problems: open only after your own reconciliation |

Both start October at EUR 850,000.00. At 31 October the GL shows **EUR 1,041,914.39** and the
bank **EUR 987,002.82**, so there is **EUR 54,911.57** to explain.

## Plan
1. ✅ Generate the data
2. Exact matching on reference and amount
3. Second-pass matching on date and amount (catches typed-wrong references)
4. Classify what is left: timing differences, missing entries, duplicates, wrong amounts
5. Reconciliation statement + exception report to Excel
6. Budget vs actual variance analysis

## Run it
```bash
cd 02-ledger-reconciliation
python3 src/generate_data.py
```
