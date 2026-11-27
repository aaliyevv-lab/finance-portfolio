"""
Shared settings and helpers for the portfolio-risk scripts, so every task uses the same
data, weights and assumptions. Other scripts load it with:  from common import ...
(like source("common.R") in R).
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
OUT = PROJECT / "output"
OUT.mkdir(exist_ok=True)

STOCKS = ["OTP", "MOL", "Richter", "Telekom"]
MARKET = "STOXX600"
WEIGHTS = pd.Series(0.25, index=STOCKS)      # equal weights, rebalanced daily (a simplification)
PORTFOLIO_VALUE = 100_000                    # EUR, used for Value at Risk in money terms
TRADING_DAYS = 252                           # trading days in a year, to annualise daily numbers
RF_ANNUAL = 0.02                             # risk-free rate: approx. average ECB deposit rate
                                             # Nov 2021 - Oct 2026 (an assumption, see README)

# Chart style, the same palette as the other projects
COLORS = {"OTP": "#2a78d6", "MOL": "#eb6834", "Richter": "#1baf7a", "Telekom": "#eda100",
          "Portfolio": "#0b0b0b", "STOXX600": "#52514e"}
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def load_prices():
    """Daily prices in EUR (from Task 1), one column per series."""
    return pd.read_csv(DATA / "prices_eur.csv", parse_dates=["date"], index_col="date")


def load_returns():
    """Daily simple returns: today's price / yesterday's price - 1, plus the portfolio.
    The portfolio return each day is the weighted average of the stock returns."""
    returns = load_prices().pct_change().dropna()          # like price / lag(price) - 1 in R
    returns["Portfolio"] = returns[STOCKS] @ WEIGHTS        # @ = matrix product: sum of weight x return
    return returns


def style(ax, title):
    """Consistent chart styling: left-aligned bold title, light grid, no top/right border."""
    ax.set_title(title, loc="left", fontweight="bold", color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=INK_2)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


plt.rcParams.update({"font.size": 10, "savefig.dpi": 150, "savefig.bbox": "tight"})
