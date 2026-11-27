"""
Task 5: Value at Risk (VaR) and Expected Shortfall for a EUR 100,000 portfolio.

    1-day 99% VaR = the loss the portfolio should NOT exceed on 99 days out of 100.
    Expected Shortfall (ES) = the average loss on the days when it IS exceeded (the bad 1%).

Two methods:
    historical   the actual 1st / 5th percentile of past daily returns (no assumptions)
    parametric   assumes returns are normally distributed: mean + z x standard deviation
Then a backtest: each day, compute VaR from the previous 250 days only, and count how often
the next day's loss was bigger ("exceptions"). A good 99% VaR has about 1 exception per 100 days.

Run from the project folder:
    cd 04-portfolio-risk
    python3 src/var.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from common import COLORS, INK, INK_2, OUT, PORTFOLIO_VALUE, load_returns, style

WINDOW = 250                                   # one year of trading days for the backtest
r = load_returns()["Portfolio"]
print(f"Portfolio: EUR {PORTFOLIO_VALUE:,}, {len(r):,} daily returns\n")

# 1. Are returns normal? Skewness and excess kurtosis (fat tails) say no if far from 0
print(f"Skewness {stats.skew(r):.2f}, excess kurtosis {stats.kurtosis(r):.1f} "
      f"(normal distribution: 0 and 0; positive kurtosis = more extreme days than normal)\n")

# 2. VaR and ES over the whole period
rows = []
for level in (0.95, 0.99):
    alpha = 1 - level
    hist_var = -np.quantile(r, alpha)                              # like -quantile(r, 0.01) in R
    param_var = -(r.mean() + stats.norm.ppf(alpha) * r.std())      # qnorm(0.01) = -2.33
    hist_es = -r[r <= -hist_var].mean()                            # average of the worst 1% (or 5%)
    rows.append({"confidence": f"{level:.0%}", "historical_var": hist_var, "parametric_var": param_var,
                 "expected_shortfall": hist_es})
var = pd.DataFrame(rows).set_index("confidence")
var_eur = var * PORTFOLIO_VALUE
print("1-day VaR and Expected Shortfall:")
print(pd.concat([(var * 100).round(2).add_suffix(" %"), var_eur.round(0).add_suffix(" EUR")], axis=1)
      .to_string())

h99 = var.loc["99%", "historical_var"]
print(f"\nIn words: on 99 days out of 100, the portfolio should not lose more than "
      f"EUR {h99 * PORTFOLIO_VALUE:,.0f} in a day. On the worst 1% of days it lost "
      f"EUR {var.loc['99%', 'expected_shortfall'] * PORTFOLIO_VALUE:,.0f} on average.")
print(f"10-day 99% VaR (square-root-of-time rule, as in Basel): "
      f"EUR {h99 * np.sqrt(10) * PORTFOLIO_VALUE:,.0f}")
worst = r.idxmin()
print(f"Worst single day: {worst:%d %b %Y}, {r.min():.1%} = EUR {r.min() * PORTFOLIO_VALUE:,.0f}")

# 3. Backtest: rolling one-year VaR, each computed only from the PAST (no look-ahead)
hist_roll = -r.rolling(WINDOW).quantile(0.01).shift(1)               # shift(1): use data up to yesterday
param_roll = -(r.rolling(WINDOW).mean() + stats.norm.ppf(0.01) * r.rolling(WINDOW).std()).shift(1)
test = pd.DataFrame({"return": r, "hist_var": hist_roll, "param_var": param_roll}).dropna()
test["hist_exception"] = test["return"] < -test["hist_var"]
test["param_exception"] = test["return"] < -test["param_var"]
n = len(test)
expected = 0.01 * n


def kupiec_p(exceptions, days, p=0.01):
    """Kupiec proportion-of-failures test: is the exception rate consistent with p?
    A likelihood-ratio test, chi-squared with 1 degree of freedom. p < 0.05 = the model is wrong."""
    x = exceptions
    if x == 0:
        return 1.0
    rate = x / days
    lr = -2 * ((days - x) * np.log(1 - p) + x * np.log(p) - (days - x) * np.log(1 - rate) - x * np.log(rate))
    return 1 - stats.chi2.cdf(lr, df=1)


print(f"\nBacktest of the 99% VaR, {n} days ({test.index.min():%b %Y} - {test.index.max():%b %Y}), "
      f"expected exceptions: {expected:.0f}")
for method in ("hist", "param"):
    x = int(test[f"{method}_exception"].sum())
    last_year = int(test[f"{method}_exception"].iloc[-WINDOW:].sum())
    zone = "green" if last_year <= 4 else ("yellow" if last_year <= 9 else "red")
    print(f"  {'historical' if method == 'hist' else 'parametric':<11} {x:>3} exceptions "
          f"({x / n:.1%}), Kupiec p = {kupiec_p(x, n):.3f}; last 250 days: {last_year} -> Basel {zone} zone")

var.round(5).to_csv(OUT / "var_summary.csv")
test.round(5).to_csv(OUT / "var_backtest.csv", index_label="date")

# Chart 1: distribution of daily returns with the VaR cut-offs and a normal curve for comparison
fig, ax = plt.subplots(figsize=(9, 4.8))
ax.hist(r * 100, bins=80, density=True, color=COLORS["OTP"], alpha=0.75, edgecolor="white", linewidth=0.3,
        label="Daily returns")
x = np.linspace(r.min() * 100, r.max() * 100, 300)
ax.plot(x, stats.norm.pdf(x, r.mean() * 100, r.std() * 100), color=INK, linewidth=1.5,
        label="Normal distribution, same mean and volatility")
# 99% label to the left of its line, 95% label to the right of its line, so they don't overlap
for level, ls, side in (("95%", "--", 1), ("99%", "-", -1)):
    v = var.loc[level, "historical_var"] * 100
    ax.axvline(-v, color=COLORS["MOL"], linestyle=ls, linewidth=1.5)
    ax.annotate(f"{level} VaR\n-{v:.1f}%", (-v, ax.get_ylim()[1] * 0.6), xytext=(6 * side, 0),
                textcoords="offset points", ha="left" if side > 0 else "right",
                color=COLORS["MOL"], fontsize=9)
ax.set_xlabel("Daily portfolio return (%)", color=INK_2)
ax.set_ylabel("Density", color=INK_2)
style(ax, "Daily returns of the portfolio: fatter tails than a normal distribution")
ax.legend(frameon=False, loc="upper left")
fig.savefig(OUT / "var_distribution.png")

# Chart 2: backtest, daily losses vs the rolling 99% VaR, exceptions marked
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.bar(test.index, test["return"] * 100, color=INK_2, width=1.5, label="Daily return")
ax.plot(test.index, -test["hist_var"] * 100, color=COLORS["MOL"], linewidth=1.5,
        label="99% VaR (historical, previous 250 days)")
exc = test[test["hist_exception"]]
ax.scatter(exc.index, exc["return"] * 100, color=COLORS["MOL"], s=25, zorder=3,
           label=f"Exceptions ({len(exc)})")
ax.set_ylabel("Daily return (%)", color=INK_2)
style(ax, "VaR backtest: losses beyond the 99% VaR")
ax.legend(frameon=False, loc="upper left", ncol=3)
fig.savefig(OUT / "var_backtest.png")
print("\nSaved output/var_summary.csv, output/var_backtest.csv, output/var_distribution.png, "
      "output/var_backtest.png")
