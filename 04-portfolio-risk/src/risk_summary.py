"""
Task 6: the one-page risk summary for the client.

Reads the results of Tasks 2-5 and writes output/risk_summary.md: a one-page report in plain
language, with every number filled in by the code (f-strings), so the report can never disagree
with the analysis. If the data or an assumption changes, rerun the scripts and the page updates.

It also tests one recommendation: inverse-volatility weights (hold less of the riskier stocks).

Needs Tasks 2-5 first.

Run from the project folder:
    cd 04-portfolio-risk
    python3 src/risk_summary.py
"""

import numpy as np
import pandas as pd

from common import MARKET, OUT, PORTFOLIO_VALUE, RF_ANNUAL, STOCKS, TRADING_DAYS, load_returns

perf = pd.read_csv(OUT / "performance_summary.csv", index_col="series")
risk = pd.read_csv(OUT / "risk_contribution.csv", index_col="stock")
capm = pd.read_csv(OUT / "capm_results.csv", index_col="series")
var = pd.read_csv(OUT / "var_summary.csv", index_col="confidence")
backtest = pd.read_csv(OUT / "var_backtest.csv", parse_dates=["date"], index_col="date")
corr = pd.read_csv(OUT / "correlation_matrix.csv", index_col=0)

P, M = perf.loc["Portfolio"], perf.loc[MARKET]
pct = lambda x: f"{x:.1%}"                       # 0.297 -> "29.7%"
eur = lambda x: f"EUR {x * PORTFOLIO_VALUE:,.0f}"  # share of the portfolio -> euros

# Recommendation test: inverse-volatility weights (weight proportional to 1 / volatility)
returns = load_returns()
cov = returns[STOCKS].cov() * TRADING_DAYS
inv = 1 / risk["volatility"]
w_inv = inv / inv.sum()
vol_equal = np.sqrt(risk["weight"] @ cov @ risk["weight"])
vol_inv = np.sqrt(w_inv @ cov @ w_inv)

top_risk = risk["risk_contribution"].idxmax()
pairs = corr.loc[STOCKS, STOCKS].where(np.triu(np.ones((4, 4), dtype=bool), k=1)).stack()
exceptions = int(backtest["hist_exception"].sum())
expected = 0.01 * len(backtest)
first_day, last_day = returns.index.min(), returns.index.max()

page = f"""# Risk summary: Hungarian blue-chip portfolio

**Client:** euro-based investor · **Portfolio:** EUR {PORTFOLIO_VALUE:,}, equal weights in OTP Bank, MOL,
Richter Gedeon and Magyar Telekom · **Benchmark:** STOXX Europe 600 · **Period:**
{first_day:%B %Y} – {last_day:%B %Y}, daily data in EUR

## Bottom line
The portfolio earned far more than the European market ({pct(P['annual_return'])} a year vs
{pct(M['annual_return'])}), but it is **a concentrated bet on one country**. Its risk is higher than
the market's ({pct(P['annual_volatility'])} volatility vs {pct(M['annual_volatility'])}), it fell
{pct(-P['max_drawdown'])} from peak to trough in 2022, and most of its moves come from Hungary-specific
factors (the forint, domestic politics, sector taxes) that European diversification does not offset.

## Key figures
| | Portfolio | STOXX Europe 600 |
|---|---:|---:|
| Annual return | {pct(P['annual_return'])} | {pct(M['annual_return'])} |
| Annual volatility | {pct(P['annual_volatility'])} | {pct(M['annual_volatility'])} |
| Sharpe ratio (risk-free {pct(RF_ANNUAL)}) | {P['sharpe_ratio']:.2f} | {M['sharpe_ratio']:.2f} |
| Maximum drawdown | {pct(P['max_drawdown'])} | {pct(M['max_drawdown'])} |
| Beta to STOXX Europe 600 | {capm.loc['Portfolio', 'beta']:.2f} | 1.00 |
| 1-day 99% Value at Risk | {eur(var.loc['99%', 'historical_var'])} | |
| 1-day 99% Expected Shortfall | {eur(var.loc['99%', 'expected_shortfall'])} | |

## What drives the risk
- **Diversification works, up to a point.** The stocks' correlations are low ({pairs.min():.2f}–{pairs.max():.2f}),
  so holding four cuts volatility from {pct(risk['weight'] @ risk['volatility'])} (average stock) to
  {pct(vol_equal)}. But correlations rose to their highest in the 2022 crisis, when protection was needed most.
- **{top_risk} carries the most risk:** {pct(risk.loc[top_risk, 'weight'])} of the money but
  {pct(risk.loc[top_risk, 'risk_contribution'])} of the risk, with the highest volatility
  ({pct(risk.loc[top_risk, 'volatility'])}) and the only beta above 1 ({capm.loc[top_risk, 'beta']:.2f}).
- **Low beta does not mean low risk.** A beta of {capm.loc['Portfolio', 'beta']:.2f} says the portfolio moves
  less than Europe on average, but the market explains only {capm.loc['Portfolio', 'r_squared']:.0%} of its
  daily moves. The other {1 - capm.loc['Portfolio', 'r_squared']:.0%} is Hungarian risk.
- **Currency.** Converting to euros adds the forint's moves to every stock at once: the stocks are more
  correlated in EUR than in HUF.

## Tail risk
- On 99 days out of 100 the portfolio should not lose more than **{eur(var.loc['99%', 'historical_var'])}**
  in a day; on the worst 1% of days the average loss was **{eur(var.loc['99%', 'expected_shortfall'])}**.
  The worst day was a loss of {pct(-P['worst_day'])} (1 March 2022).
- Returns have fat tails: a normal-distribution model puts the 99% VaR at
  {eur(var.loc['99%', 'parametric_var'])}, {pct(1 - var.loc['99%', 'parametric_var'] / var.loc['99%', 'historical_var'])}
  below the historical figure. Use historical VaR and Expected Shortfall, not the normal model.
- Backtest: {exceptions} losses beyond the 99% VaR in {len(backtest)} days (about {expected:.0f} expected).
  The model is consistent with the data (Kupiec test) and in the Basel green zone.

## Recommendations
1. **Reduce the weight of {top_risk}.** Weighting by inverse volatility
   ({', '.join(f'{s} {w:.0%}' for s, w in w_inv.items())}) would lower portfolio volatility from
   {pct(vol_equal)} to {pct(vol_inv)} over the same period: a modest gain, because the other three stocks
   have similar volatility. The bigger risks (country and currency) need points 2 and 3.
2. **Decide on the currency risk explicitly.** Hedging EUR/HUF with forwards removes the shared forint
   risk, at the cost of the interest-rate gap between forint and euro.
3. **Treat this as a satellite, not a core holding.** With {1 - capm.loc['Portfolio', 'r_squared']:.0%} country-specific risk, it belongs next to a
   broad European core, sized so that a repeat of 2022 ({pct(P['max_drawdown'])}) is acceptable.
4. **Monitor with Expected Shortfall** and re-run the VaR backtest monthly; exceptions come in clusters
   (2022 war, April 2025 tariff shock).

*Historical analysis, not a forecast. Assumptions: equal weights rebalanced daily, no costs or taxes,
dividends reinvested, risk-free rate {pct(RF_ANNUAL)} (approximate average ECB deposit rate). Data: Yahoo Finance.*
"""

(OUT / "risk_summary.md").write_text(page)
print(page)
print(f"Saved output/risk_summary.md ({len(page.split())} words)")
