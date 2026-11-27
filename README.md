# Aliheydar Aliyev: Finance Analytics Portfolio

2nd-year BSc Applied Economics student at Corvinus University of Budapest, looking for
finance internships in Budapest (FP&A, audit, revenue management, risk).

Five projects that each solve a real junior finance task: hotel performance reporting
in SQL, ledger reconciliation, audit analytics, portfolio risk, and a DCF valuation of a listed
Hungarian company.

**Skills:** SQL (SQLite) · Python (pandas, matplotlib, statsmodels, scipy) · Risk (volatility, CAPM beta, VaR, Expected Shortfall) · R (data cleaning, OLS, ANOVA) · Excel (DCF modelling, pivot tables) · Git

| # | Project | Business question | Key result | Tools | Status |
|---|---------|-------------------|------------|-------|--------|
| 1 | [Hotel KPIs](01-hotel-kpis/) | How is a 130-room Budapest luxury hotel performing by month and channel? | €20.6M room revenue, 78.7% occupancy; Booking.com costs €1.15M a year in commission | SQL, Python, pandas, matplotlib | ✅ Done |
| 2 | [Ledger reconciliation](02-ledger-reconciliation/) | Do the bank statement and general ledger agree, and where is the budget off? | EUR 54,912 difference fully explained: 180 of 186 bank lines matched, 17 exceptions classified, 8 correcting entries; 4 material budget variances | Python, pandas, openpyxl (Excel report), matplotlib | ✅ Done |
| 3 | [Audit analytics](03-audit-analytics/) | Which payments and journal entries look suspicious? | 100% of 3,421 transactions tested; Benford, duplicate and control tests traced EUR 174k of self-approved payments just under the approval limit to one clerk; 53 of 53 planted problems found | Python, pandas, Benford's Law, openpyxl | ✅ Done |
| 4 | [Portfolio risk](04-portfolio-risk/) | How risky are four Hungarian blue chips for a euro investor, versus the European market? | 29.7% a year at 20% volatility (STOXX 600: 6.2%, 14%); beta 0.61 but R² 0.18, so mostly country risk; 1-day 99% VaR EUR 3,213 on EUR 100k, backtest passed | Python, statsmodels (OLS), scipy, yfinance | ✅ Done |
| 5 | [Richter DCF](05-richter-dcf/) | What is a Gedeon Richter share worth, given its 2029 Vraylar patent cliff? | HUF 12,753 per share vs HUF 13,600 price (6% downside), in line with analyst consensus | Excel, Python, openpyxl | ✅ Done |

[![Hotel KPIs by month](01-hotel-kpis/output/monthly_kpis.png)](01-hotel-kpis/)

## Run it yourself
Requires Python 3.12+.
```bash
pip install -r requirements.txt
```
Each project folder has its own README with run instructions.

*All datasets are synthetic (generated with a fixed random seed), public market data, or published company reports (Richter DCF). No confidential company or client data is used.*
