# Risk summary: Hungarian blue-chip portfolio

**Client:** euro-based investor · **Portfolio:** EUR 100,000, equal weights in OTP Bank, MOL,
Richter Gedeon and Magyar Telekom · **Benchmark:** STOXX Europe 600 · **Period:**
November 2021 – October 2026, daily data in EUR

## Bottom line
The portfolio earned far more than the European market (29.7% a year vs
6.2%), but it is **a concentrated bet on one country**. Its risk is higher than
the market's (20.0% volatility vs 14.1%), it fell
38.4% from peak to trough in 2022, and most of its moves come from Hungary-specific
factors (the forint, domestic politics, sector taxes) that European diversification does not offset.

## Key figures
| | Portfolio | STOXX Europe 600 |
|---|---:|---:|
| Annual return | 29.7% | 6.2% |
| Annual volatility | 20.0% | 14.1% |
| Sharpe ratio (risk-free 2.0%) | 1.39 | 0.30 |
| Maximum drawdown | -38.4% | -22.5% |
| Beta to STOXX Europe 600 | 0.61 | 1.00 |
| 1-day 99% Value at Risk | EUR 3,213 | |
| 1-day 99% Expected Shortfall | EUR 4,833 | |

## What drives the risk
- **Diversification works, up to a point.** The stocks' correlations are low (0.25–0.43),
  so holding four cuts volatility from 27.8% (average stock) to
  20.0%. But correlations rose to their highest in the 2022 crisis, when protection was needed most.
- **OTP carries the most risk:** 25.0% of the money but
  35.5% of the risk, with the highest volatility
  (35.1%) and the only beta above 1 (1.08).
- **Low beta does not mean low risk.** A beta of 0.61 says the portfolio moves
  less than Europe on average, but the market explains only 18% of its
  daily moves. The other 82% is Hungarian risk.
- **Currency.** Converting to euros adds the forint's moves to every stock at once: the stocks are more
  correlated in EUR than in HUF.

## Tail risk
- On 99 days out of 100 the portfolio should not lose more than **EUR 3,213**
  in a day; on the worst 1% of days the average loss was **EUR 4,833**.
  The worst day was a loss of 9.2% (1 March 2022).
- Returns have fat tails: a normal-distribution model puts the 99% VaR at
  EUR 2,820, 12.2%
  below the historical figure. Use historical VaR and Expected Shortfall, not the normal model.
- Backtest: 8 losses beyond the 99% VaR in 995 days (about 10 expected).
  The model is consistent with the data (Kupiec test) and in the Basel green zone.

## Recommendations
1. **Reduce the weight of OTP.** Weighting by inverse volatility
   (OTP 19%, MOL 26%, Richter 27%, Telekom 28%) would lower portfolio volatility from
   20.0% to 19.4% over the same period: a modest gain, because the other three stocks
   have similar volatility. The bigger risks (country and currency) need points 2 and 3.
2. **Decide on the currency risk explicitly.** Hedging EUR/HUF with forwards removes the shared forint
   risk, at the cost of the interest-rate gap between forint and euro.
3. **Treat this as a satellite, not a core holding.** With 82% country-specific risk, it belongs next to a
   broad European core, sized so that a repeat of 2022 (-38.4%) is acceptable.
4. **Monitor with Expected Shortfall** and re-run the VaR backtest monthly; exceptions come in clusters
   (2022 war, April 2025 tariff shock).

*Historical analysis, not a forecast. Assumptions: equal weights rebalanced daily, no costs or taxes,
dividends reinvested, risk-free rate 2.0% (approximate average ECB deposit rate). Data: Yahoo Finance.*
