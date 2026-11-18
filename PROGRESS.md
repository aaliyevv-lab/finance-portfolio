# Progress log

## Status
| # | Project | Status |
|---|---------|--------|
| 0 | Setup (repo, tools, git basics) | Done |
| 1 | hotel-kpis | In progress: Task 3/8 done |
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
  calendar 365, bookings 18,775 after the weekend fix). Occupancy 57% (Jan) to 88% (Jun–Sep), no double bookings.
- **Learned:** database schema (PRIMARY KEY, REFERENCES/foreign key, NOT NULL, CHECK), why
  a fixed random seed matters, calendar table for splitting stays across months.
- **Struggled with:** (fill in)
- **To review:** read the CREATE TABLE block and explain each table out loud.
- **Bug found later (Task 3):** weekend flag used `dayofweek >= 4`, which also counted Sunday
  (pandas: Monday = 0). Fixed to Fri+Sat only. Lesson: sanity-check counts (a year has ~104 weekend nights, not 157).

### 2026-11-18: hotel-kpis Task 2: SQL basics
- **Done:** set up VS Code + git on Mac (clone, pull, commit, push). `sql/01_explore.sql` with 7 queries:
  SELECT/LIMIT, GROUP BY + COUNT/AVG, WHERE with AND, subquery for % share, JOIN with aliases, HAVING.
- **Learned:** SQL execution order (FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT);
  WHERE filters rows before grouping, HAVING filters groups after; 100.0 to avoid integer division.
- **Struggled with:** writing query 7 (channel length of stay) from scratch; asked for the solution.
- **To review:** rewrite query 7 from memory without looking; translate it into dplyr and back.

### 2026-11-18: hotel-kpis Task 3: occupancy by month
- **Done:** `sql/02_occupancy.sql`: booking split into nights, monthly occupancy, weekday vs weekend.
  Results: 57.3% (Jan) to 88.4% (Sep); weekends 82.4% vs weekdays 77.2%.
- **Learned:** range join to the calendar (one booking row → one row per night, like `tidyr::uncount`),
  check-out date is not a night, CTEs (`WITH`), LEFT JOIN, CASE WHEN. First time a push was rejected
  because GitHub had newer commits → `git pull` then `git push`.
- **Struggled with:** (fill in)
- **To review:** explain out loud why counting nights by check-in month gives the wrong monthly occupancy.

## Review list (things to revisit before interviews)
- (empty for now)

## Interview Q&A practice
- (filled in after each project)
