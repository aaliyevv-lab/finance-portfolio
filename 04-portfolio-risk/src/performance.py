"""
Task 2: returns, volatility, Sharpe ratio and maximum drawdown.

    annual return      compound growth per year (CAGR) over the 5 years
    annual volatility  standard deviation of daily returns x sqrt(252)
    Sharpe ratio       (annual return - risk-free rate) / annual volatility: return per unit of risk
    max drawdown       the worst fall from a previous peak, the loss an investor who bought at
                       the top would have suffered

Run from the project folder:
    cd 04-portfolio-risk
    python3 src/performance.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import COLORS, INK_2, MARKET, OUT, RF_ANNUAL, STOCKS, TRADING_DAYS, load_returns, style

returns = load_returns()
series = STOCKS + ["Portfolio", MARKET]
years = len(returns) / TRADING_DAYS
print(f"{len(returns):,} daily returns, {returns.index.min():%d %b %Y} to {returns.index.max():%d %b %Y} "
      f"({years:.1f} years)\n")

# Growth of EUR 1: multiply (1 + daily return) day after day, like cumprod(1 + r) in R
growth = (1 + returns[series]).cumprod()

# Max drawdown: how far below its previous peak each series was, at the worst point
running_peak = growth.cummax()                        # highest value so far, like cummax() in R
drawdown = growth / running_peak - 1

summary = pd.DataFrame({
    "annual_return": growth.iloc[-1] ** (1 / years) - 1,
    "annual_volatility": returns[series].std() * np.sqrt(TRADING_DAYS),
    "max_drawdown": drawdown.min(),
    "worst_day": returns[series].min(),
    "best_day": returns[series].max(),
})
summary["sharpe_ratio"] = (summary["annual_return"] - RF_ANNUAL) / summary["annual_volatility"]
summary["max_drawdown_date"] = drawdown.idxmin().dt.strftime("%Y-%m-%d")

show = summary.copy()
for col in ["annual_return", "annual_volatility", "max_drawdown", "worst_day", "best_day"]:
    show[col] = (show[col] * 100).map(lambda x: f"{x:.1f}%")
show["sharpe_ratio"] = show["sharpe_ratio"].round(2)
print(show.to_string())

avg_stock_vol = summary.loc[STOCKS, "annual_volatility"].mean()
print(f"\nAverage volatility of the four stocks: {avg_stock_vol:.1%}; portfolio volatility: "
      f"{summary.loc['Portfolio', 'annual_volatility']:.1%}  <- lower: diversification (Task 3)")
print(f"Risk-free rate used for the Sharpe ratio: {RF_ANNUAL:.1%} a year")

summary.round(4).to_csv(OUT / "performance_summary.csv", index_label="series")

# Chart: growth of EUR 100. Log scale, so equal percentage moves look equally big
# (Telekom's 8x rise would otherwise squash every other line).
fig, ax = plt.subplots(figsize=(10, 5))
for name in series:
    bold = name in ("Portfolio", MARKET)
    ax.plot(growth.index, growth[name] * 100, color=COLORS[name], linewidth=2.2 if bold else 1.2,
            linestyle="--" if name == MARKET else "-", label=name if name != MARKET else "STOXX Europe 600")
    ax.annotate(f"{name if name != MARKET else 'STOXX 600'}  €{growth[name].iloc[-1] * 100:,.0f}",
                (growth.index[-1], growth[name].iloc[-1] * 100), xytext=(6, 0), textcoords="offset points",
                va="center", fontsize=9, color=COLORS[name])
ax.set_yscale("log")
ax.set_yticks([50, 100, 200, 400, 800])
ax.set_yticklabels(["€50", "€100", "€200", "€400", "€800"])
ax.set_ylabel("Value of EUR 100 invested (log scale)", color=INK_2)
style(ax, "Growth of EUR 100 invested in Nov 2021, in euros, dividends reinvested")
ax.legend(frameon=False, loc="upper left")
ax.set_xlim(growth.index[0], growth.index[-1] + pd.Timedelta(days=200))
fig.savefig(OUT / "growth_of_100.png")
print("\nSaved output/performance_summary.csv, output/growth_of_100.png")
