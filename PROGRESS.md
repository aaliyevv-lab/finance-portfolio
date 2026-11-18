# Progress log

## Status
| # | Project | Status |
|---|---------|--------|
| 0 | Setup (repo, tools, git basics) | Done |
| 1 | hotel-kpis | In progress: Task 7/8 done (README in review) |
| 2 | ledger-reconciliation | Not started |
| 3 | audit-analytics | Not started |
| 4 | portfolio-risk | Not started |
| 5 | richter-dcf | Done (extra project, built outside the task-by-task format) |

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

### 2026-11-18: hotel-kpis Task 4: ADR and RevPAR
- **Done:** `sql/03_adr_revpar.sql`: monthly occupancy/ADR/RevPAR, KPIs by room type, full-year totals.
  Full year: €20.64M room revenue, 78.7% occupancy, €553 ADR, €435 RevPAR. December has the highest RevPAR
  (€563, ADR €656) despite lower occupancy than summer; Jan–Feb RevPAR ~€233.
- **Learned:** ADR vs RevPAR (RevPAR = occupancy × ADR), chaining several CTEs, a query with no GROUP BY
  returns one summary row. Set git identity (user.name / user.email) so commits link to GitHub profile.
- **Struggled with:** (fill in)
- **To review:** explain why a hotel can raise occupancy and still lose RevPAR.

### 2026-11-18: hotel-kpis Task 5: cancellations and lead time
- **Done:** `sql/04_cancellations.sql`: cancellation rate + revenue at risk by channel, by arrival month,
  lead time by channel, cancellation rate by lead-time bucket. Booking.com 30% vs travel agents 10%;
  Booking.com = €2.9M of €5.6M cancelled booking value.
- **Learned:** `AVG(CASE WHEN ... THEN 1 ELSE 0 END)` = `mean(x == "a")`; `julianday()` date differences;
  `CASE` without ELSE gives NULL and AVG skips NULLs (like `na.rm = TRUE`); bucket labels prefixed for sorting.
  Insight: the lead-time result is confounded by channel (omitted variable bias).
- **Struggled with:** (fill in)
- **To review:** explain why "lost revenue" from cancellations is an upper bound, and the confounding in query 4.

### 2026-11-18: hotel-kpis Task 6: revenue by channel
- **Done:** `sql/05_channel_revenue.sql`: gross/commission/net by channel, monthly pivot by channel,
  commission by month. Booking.com €6.40M gross but €1.15M commission; total commission ≈ €1.95M (9.5%).
- **Learned:** net ADR as the real value of a channel; pivot in SQL with `SUM(CASE WHEN ...)`
  (= `pivot_wider`); multiply inside SUM when each row has its own rate.
  Git: push rejected → `git pull` (rebase) → `git push`.
- **Struggled with:** (fill in)
- **To review:** the "move 10% of Booking.com nights to direct = ~€115k saving" calculation.

### 2026-11-18: hotel-kpis Task 7: charts in Python
- **Done:** `src/make_charts.py` (written by Claude, read and run by me): runs the saved SQL with
  `pd.read_sql`, saves 4 PNGs in `output/` (monthly KPIs, channel revenue, cancellations, weekday/weekend).
- **Learned:** DataFrame = R data frame; matplotlib `fig, ax` vs ggplot layers; `plt.subplots(3, 1)` ≈ facets;
  Python functions, loops, indentation, 0-based indexing, f-strings. Why no dual-axis charts.
- **Struggled with:** (fill in)
- **To review:** explain what `query("03_adr_revpar.sql", 1)` does step by step.

### 2026-11-18: richter-dcf: DCF valuation of Gedeon Richter
- **Done:** Excel DCF built by Claude from Richter's 2025 annual report (`src/build_model.py` writes
  every forecast cell as a formula), Python check in `src/make_chart.py` (same HUF 12,753 per share),
  chart and README. Base case: HUF 12,753 vs HUF 13,600 price (-6%); EV HUF 2,024bn; WACC 10.5%, g 3%.
- **Learned:** FCFF = EBIT × (1 − t) + D&A − capex − ΔNWC; CAPM WACC; Gordon-growth terminal value;
  EV-to-equity bridge (add cash and investments, subtract debt, leases, NCI). Key insight: a first
  version without the Vraylar patent cliff gave HUF 20,300, so modelling the business correctly
  matters more than the formulas.
- **Struggled with:** (fill in)
- **To review:** walk through the DCF tab top to bottom out loud; explain why the terminal value
  excludes royalties; change the core EBIT margin to 18% and explain how the value moves.

## Review list (things to revisit before interviews)
- (empty for now)

## Interview Q&A practice
- (filled in after each project)
