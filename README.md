# Aliheydar Aliyev: Finance Analytics Portfolio

2nd-year BSc Applied Economics student at Corvinus University of Budapest, looking for
finance internships in Budapest (FP&A, audit, revenue management, risk).

Four small projects that each solve a real junior finance task: hotel performance reporting
in SQL, ledger reconciliation, audit analytics, and portfolio risk.

**Skills:** SQL (SQLite) · Python (pandas, matplotlib, statsmodels) · R (data cleaning, OLS, ANOVA) · Excel (pivot tables) · Git

| # | Project | Business question | Key result | Tools | Status |
|---|---------|-------------------|------------|-------|--------|
| 1 | [Hotel KPIs](01-hotel-kpis/) | How is a 130-room Budapest luxury hotel performing by month and channel? | €20.6M room revenue, 78.7% occupancy; Booking.com costs €1.15M a year in commission | SQL, Python, pandas, matplotlib | ✅ Done |
| 2 | [Ledger reconciliation](02-ledger-reconciliation/) | Do the bank statement and general ledger agree, and where is the budget off? | | Python, pandas, Excel export | 🔄 In progress |
| 3 | [Audit analytics](03-audit-analytics/) | Which payments and journal entries look suspicious? | | Python, pandas, Benford's Law | Planned |
| 4 | [Portfolio risk](04-portfolio-risk/) | How risky is a small stock portfolio versus the market? | | Python, statsmodels, yfinance | Planned |

[![Hotel KPIs by month](01-hotel-kpis/output/monthly_kpis.png)](01-hotel-kpis/)

## Run it yourself
Requires Python 3.12+.
```bash
pip install -r requirements.txt