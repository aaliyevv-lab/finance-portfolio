# Progress log

## Status
| # | Project | Status |
|---|---------|--------|
| 0 | Setup (repo, tools, git basics) | Done |
| 1 | hotel-kpis | Done (interview answers to practise) |
| 2 | ledger-reconciliation | Done (code given by Claude step by step, run and committed by me; interview questions to practise) |
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

### 2026-11-18: hotel-kpis Task 8: README + portfolio front page
- **Done:** project README for recruiters, portfolio front page (name, skills, status table, key result, chart).
- **Learned:** `cd ..`, `pwd`; save before committing (● = unsaved); `git add` works relative to the current folder.

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

### 2026-11-27: ledger-reconciliation Task 1: generate bank and GL data
- **Done:** `src/generate_data.py` builds October 2026 for the hotel's operating account: GL 191 rows,
  bank 186 rows, both opening at EUR 850,000. Closing GL EUR 1,041,914.39 vs bank EUR 987,002.82 →
  EUR 54,911.57 to explain. 17 planted problems in `data/answer_key.csv` (don't open yet).
  The script checks itself: the planted problems must explain the whole difference.
- **Learned:** what a bank reconciliation is and why month-end needs it; timing differences
  (deposits in transit, outstanding payments) vs real errors (duplicates, wrong amounts, wrong references);
  card settlements arrive the next business day.
- **Struggled with:** (fill in)
- **To review:** explain out loud why a card sale on Friday 30 Oct is in the GL but not on the October bank statement.

### 2026-11-27: ledger-reconciliation Tasks 2–6: matching, exceptions, reconciliation, budget
- **Done:** `match_exact.py` (178 matches on reference + amount), `match_date_amount.py` (2 more on
  date + amount: wrong references), `classify_exceptions.py` (17 exceptions, 0 left to investigate),
  `reconciliation_report.py` (adjusted bank = adjusted GL = EUR 1,026,745.47; Excel report with
  8 correcting entries), `budget_vs_actual.py` (4 material variances; corrected net cash flow ties
  back to the reconciliation).
- **Learned:** inner join = exact match, anti-join = what is left; amounts in cents to avoid float
  errors; `cumcount()` so duplicates don't double-match; timing items vs errors; reconciliation
  statement layout; materiality (% AND EUR) for variance reporting; writing a multi-sheet Excel file.
- **Struggled with:** creating files in the right folder in VS Code (file first landed outside `src`;
  budget CSV was missing). (fill in anything else)
- **To review:** the three interview questions below, out loud, in under 60 seconds each.

### 2026-11-27: ledger-reconciliation review fixes (Claude, after checking the branch)
- **Checked:** all scripts rerun from scratch; every checkpoint matches (178 + 2 matches, 17 exceptions,
  adjusted bank = adjusted GL = EUR 1,026,745.47, all 17 planted problems found).
- **Improved:** proper double-entry journal entries (Dr/Cr with account numbers, asserted to equal the
  GL adjustment of EUR −15,168.92); formatted Excel report (readable headers, € format, highlighted
  totals); variance chart in blue/orange (colour-blind safe, same palette as Project 1); budget
  comparison relabelled "book basis" (card takings include EUR 54,679 deposits in transit).
- **To review:** write the 8 journal entries by hand from the exception list, then compare.

## Review list (things to revisit before interviews)
- Hotel KPI formulas: occupancy, ADR, RevPAR = occupancy × ADR, cancellation rate, net ADR.
- Calendar range join (`date >= check_in AND date < check_out`) and why check-out is not a night.
- WHERE vs HAVING; `AVG(CASE WHEN ...)` for rates; pivot with `SUM(CASE WHEN ...)`.
- Git loop: pull → work → add → commit → push; rejected push → pull, then push.

## Interview Q&A practice
### Project 1: hotel-kpis (model answers given by Claude on request; practise saying them in my own words)
1. **Occupancy up 80% → 85% but RevPAR fell?** RevPAR = occupancy × ADR, so ADR must have fallen more than
   occupancy rose (e.g. 80% × €600 = €480 vs 85% × €550 = €467.50). Check ADR by segment/channel, discounting,
   channel mix shift toward OTAs/corporate, room-type mix (more Deluxe, fewer suites), and length-of-stay/promo deals.
2. **Monthly occupancy in SQL?** Room-nights sold ÷ room-nights available. Tricky part: stays crossing month ends.
   Joined bookings to a calendar table on `date >= check_in AND date < check_out` (one row per night), counted
   stayed nights per month, divided by 130 × days. Sanity checks found a weekend-flag bug (Sunday counted).
3. **Reduce dependence on Booking.com?** 31% of gross (€6.4M) but €1.15M commission; net ADR €467 vs €570 direct;
   30% cancellation rate. Shift some demand to direct (10% shift ≈ €115k/yr) via best-rate guarantee, loyalty
   perks, non-refundable rates — but don't drop it: reach to foreign guests, fills Jan–Feb, billboard effect.
- **Still to do:** answer all three out loud without notes; time each answer (≤ 60 seconds).

### Project 2: ledger-reconciliation (model answers given by Claude on request; practise saying them in my own words)
1. **GL and bank differ by EUR 54,912. How do you find out why?** Match in passes from strict to loose:
   reference + amount (178 matches), then date + amount for wrongly typed references (2 more). Classify
   what's left: timing items (deposits in transit EUR 54,679, outstanding payments EUR 14,936) adjust the
   bank side; errors and unbooked items (duplicates, wrong amounts, fees, interest, unidentified receipt)
   adjust the GL side. Both adjusted balances = EUR 1,026,745.47, difference 0.00, checked with an assert.
2. **Timing difference vs error?** Timing: both records are right, they just record it in different
   months, and it clears by itself (card takings of Fri 30 Oct, paid by the bank on Mon 2 Nov). No entry,
   but check it clears. Error: one record is wrong and needs a correcting entry (INV-261019 booked twice:
   reverse EUR 16,437.88; PAY-5011 booked as 1,520 instead of 1,250, difference divisible by 9 = swapped digits).
3. **IT suppliers EUR 31,817 over budget: how to investigate?** Drill down: total → supplier → invoice.
   EUR 64.7k to IT Systems Zrt in 11 payments, EUR 27.1k to Florist Bp in 5. Ask: timing (annual licence
   paid in Oct?), one-off (new system/project), miscoding (florist isn't IT: wrong category), or real
   overspend? 11 payments to one supplier in a month → check for duplicate invoices/split payments.
   Check contracts and POs, then tell the GM: amount, cause, one-off or recurring, action.
- **Still to do:** answer all three out loud without notes; time each answer (≤ 60 seconds).
