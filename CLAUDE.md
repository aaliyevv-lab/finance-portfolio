# Working agreement for this repo

## About me
- Ali, 2nd-year BSc Applied Economics student, Corvinus University of Budapest.
- Building this portfolio for finance internships in Budapest: Morgan Stanley 2027 Finance
  Internship Program, EY, KPMG, and an entry-level finance role at Matild Palace hotel.
- Level: **R strong** (cleaning 300k+ rows, OLS, hypothesis tests, ANOVA). **Excel**: pivot tables,
  charts. **SQL and Python: beginner**, and those are the gaps to close.
- I learn by doing: short explanation → code → I run it → review.

## How Claude should work in every session
1. **Give full solutions**: complete, runnable code plus an explanation of what each part does.
2. **Small tasks.** Break every project into small numbered tasks. For each task:
   - explain the concept in **3–5 sentences**, comparing to R (dplyr, ggplot2, lm, etc.) when useful;
   - give the full code;
   - say exactly how to run it and what output to expect;
   - end with the git commit command for that task.
3. **Boilerplate is fine** (folder structure, fake data generators, config files, README
   skeletons). Analysis code can also be provided by Claude.
4. **After each project**, ask me **3 interview-style questions** about it (the kind a recruiter or
   finance interviewer would ask) so I practise explaining my work. Give feedback on my answers.
5. **Keep `PROGRESS.md` updated** after every task: what I finished, what I struggled with,
   what to review.
6. **Commit after every task** with a clear message (`<project>: <what was done>`).

## Project order
1. `01-hotel-kpis`: SQLite + Python. Occupancy, ADR, RevPAR, cancellation rate, revenue by channel/month.
2. `02-ledger-reconciliation`: bank vs GL matching, exception report to Excel, budget-vs-actual variance.
3. `03-audit-analytics`: Benford's Law, duplicate payments, unusual journal entries.
4. `04-portfolio-risk`: returns, volatility, correlations, CAPM beta, VaR, one-page risk summary.

## Conventions
- One folder per project: `data/` (inputs, generated data), `sql/` (queries), `src/` (Python
  scripts), `output/` (charts, Excel reports), and a `README.md`.
- Fake data generators use a fixed random seed so results are reproducible.
- Run scripts from the project folder, e.g. `cd 01-hotel-kpis && python src/generate_data.py`.
- Every project README must be readable in **60 seconds**: business problem, what I did, key
  results with one chart, tools used.
- Charts: clear title, labelled axes with units (HUF/EUR, %), saved as PNG to `output/`.
- Plain, simple code over clever code. A recruiter should be able to read it.
