"""
Task 4: CAPM beta. How sensitive is each stock to the European market?

The CAPM regression (the "market model") for each stock, on daily excess returns:
    (stock return - risk-free)  =  alpha  +  beta x (market return - risk-free)  +  error
    beta   how much the stock moves when the market moves 1%  (beta > 1: more than the market)
    alpha  return not explained by the market (annualised here)
    R²     share of the stock's risk explained by the market (systematic risk); 1 - R² is the
           stock-specific (idiosyncratic) risk that diversification can remove

It is an OLS regression, exactly like lm(stock ~ market) in R. statsmodels gives the same output.
Standard errors are HAC (Newey-West), robust to heteroskedasticity and autocorrelation, which
daily returns usually have.

Robustness check: betas from WEEKLY returns. Budapest and the STOXX index don't always react on
the same day, which can bias daily betas downwards.

Run from the project folder:
    cd 04-portfolio-risk
    python3 src/capm.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import COLORS, INK_2, MARKET, OUT, RF_ANNUAL, STOCKS, TRADING_DAYS, load_returns, style

returns = load_returns()
rf_daily = RF_ANNUAL / TRADING_DAYS
excess = returns - rf_daily                       # excess returns: over the risk-free rate
names = STOCKS + ["Portfolio"]


def capm(y, x):
    """OLS of y on a constant and x, with HAC standard errors. Like lm(y ~ x) in R."""
    X = sm.add_constant(x)                         # adds the intercept column (alpha)
    return sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})


# Full regression output for the portfolio, the same table summary(lm(...)) prints in R
model = capm(excess["Portfolio"], excess[MARKET])
print(model.summary(xname=["alpha (const)", "beta (STOXX600)"]).tables[1])
print(f"R-squared: {model.rsquared:.3f}   observations: {int(model.nobs)}\n")

# One row per stock and the portfolio
rows = []
for name in names:
    fit = capm(excess[name], excess[MARKET])
    rows.append({
        "series": name,
        "beta": fit.params[MARKET],
        "beta_t": fit.tvalues[MARKET],
        "alpha_annual": fit.params["const"] * TRADING_DAYS,
        "alpha_p": fit.pvalues["const"],
        "r_squared": fit.rsquared,
        "idiosyncratic_vol": fit.resid.std() * np.sqrt(TRADING_DAYS),
    })
results = pd.DataFrame(rows).set_index("series")

# Robustness: weekly returns (compound the daily returns within each week, Friday to Friday)
weekly = (1 + returns).resample("W-FRI").prod() - 1
weekly_excess = weekly - RF_ANNUAL / 52
results["beta_weekly"] = [capm(weekly_excess[n], weekly_excess[MARKET]).params[MARKET] for n in names]

show = results.copy()
show["alpha_annual"] = (show["alpha_annual"] * 100).map(lambda x: f"{x:.1f}%")
show["idiosyncratic_vol"] = (show["idiosyncratic_vol"] * 100).map(lambda x: f"{x:.1f}%")
print(show.round({"beta": 2, "beta_t": 1, "alpha_p": 3, "r_squared": 2, "beta_weekly": 2}).to_string())

port = results.loc["Portfolio"]
print(f"\nPortfolio: when the STOXX 600 moves 1%, the portfolio moves {port['beta']:.2f}% on average "
      f"(weekly data: {port['beta_weekly']:.2f}%).")
print(f"The market explains {port['r_squared']:.0%} of the portfolio's daily moves; "
      f"{1 - port['r_squared']:.0%} is Hungary-specific risk (stocks, forint, local politics).")
print(f"Alpha {port['alpha_annual']:.1%} a year, p-value {port['alpha_p']:.3f}: "
      + ("statistically significant at 5%." if port["alpha_p"] < 0.05 else
         "not statistically significant at 5%, despite the large number: 5 years of noisy daily data "
         "can't separate skill or luck from zero."))

results.round(4).to_csv(OUT / "capm_results.csv")

# Chart: portfolio vs market daily excess returns with the regression line,
# like ggplot(aes(market, portfolio)) + geom_point() + geom_smooth(method = "lm")
fig, ax = plt.subplots(figsize=(7, 5.5))
x, y = excess[MARKET] * 100, excess["Portfolio"] * 100
ax.scatter(x, y, s=8, alpha=0.35, color=COLORS["OTP"], edgecolors="none")
line_x = np.linspace(x.min(), x.max(), 50)
ax.plot(line_x, model.params["const"] * 100 + model.params[MARKET] * line_x, color=COLORS["Portfolio"],
        linewidth=2, label=f"beta = {model.params[MARKET]:.2f},  R² = {model.rsquared:.2f}")
ax.axhline(0, color=INK_2, linewidth=0.6)
ax.axvline(0, color=INK_2, linewidth=0.6)
ax.set_xlabel("STOXX Europe 600 daily excess return (%)", color=INK_2)
ax.set_ylabel("Portfolio daily excess return (%)", color=INK_2)
style(ax, "CAPM: Hungarian blue-chip portfolio vs the European market")
ax.legend(frameon=False, loc="upper left")
fig.savefig(OUT / "capm_scatter.png")
print("\nSaved output/capm_results.csv, output/capm_scatter.png")
