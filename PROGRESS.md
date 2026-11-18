# Progress log

## Status
| # | Project | Status |
|---|---------|--------|
| 0 | Setup (repo, tools, git basics) | Done |
| 1 | hotel-kpis | In progress: Task 1/8 done |
| 2 | ledger-reconciliation | Not started |
| 3 | audit-analytics | Not started |
| 4 | portfolio-risk | Not started |

## Log

### 2026-11-18: Setup
- **Done:** git repo initialised, one folder per project, CLAUDE.md + PROGRESS.md created.
  Python 3.13 with pandas, numpy, matplotlib, statsmodels, scipy, openpyxl, yfinance; SQLite 3 CLI.
- **Learned:** git basics (`status`, `add`, `commit`, `log`, `push`).
- **Struggled with:** none yet.
- **To review:** the git workflow cheat sheet in the README.

### 2026-11-18: hotel-kpis Task 1: generate database
- **Done:** `src/generate_data.py` builds `data/hotel.db` (rooms 130, rates 48, channels 5,
  calendar 365, bookings 18,920). Sanity check: occupancy 58% (Jan) to 89% (Jun–Sep), no double bookings.
- **Learned:** database schema (PRIMARY KEY, REFERENCES/foreign key, NOT NULL, CHECK), why
  a fixed random seed matters, calendar table for splitting stays across months.
- **Struggled with:** (fill in)
- **To review:** read the CREATE TABLE block and explain each table out loud.

## Review list (things to revisit before interviews)
- (empty for now)

## Interview Q&A practice
- (filled in after each project)
