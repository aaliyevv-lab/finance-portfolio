"""
Task 3: correlations and diversification. Do the stocks move together, and how much risk
does holding four of them remove?

    correlation matrix   of daily returns, like cor() in R
    diversification      portfolio volatility vs the weighted average of the stocks' volatilities
    risk contribution    how much of the portfolio's risk each stock is responsible for
    crisis check         are correlations higher in the 2022 crisis than in calmer years?
    currency check       are correlations higher in EUR than in HUF? (the forint is a shared risk)

Run from the project folder:
    cd 04-portfolio-risk
    python3 src/correlation.py
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import DATA, INK, MARKET, OUT, STOCKS, TRADING_DAYS, WEIGHTS, load_returns, style


def avg_pairwise(corr):
    """Average correlation between different stocks (the values above the diagonal)."""
    upper = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1))
    return upper.stack().mean()


returns = load_returns()

# 1. Correlation matrix of daily returns
corr = returns[STOCKS + [MARKET]].corr()
print("Correlation of daily returns (EUR):")
print(corr.round(2).to_string())
print(f"\nAverage correlation between the four stocks: {avg_pairwise(corr.loc[STOCKS, STOCKS]):.2f}")

# 2. Diversification: if the stocks were perfectly correlated (1.0), portfolio volatility would
#    equal the weighted average of their volatilities. Anything lower is the diversification benefit.
cov = returns[STOCKS].cov() * TRADING_DAYS                  # annualised covariance matrix
vols = np.sqrt(np.diag(cov))                                # each stock's annual volatility
port_vol = np.sqrt(WEIGHTS @ cov @ WEIGHTS)                 # sqrt(w' Σ w), the portfolio formula
avg_vol = WEIGHTS @ vols
print(f"\nWeighted average stock volatility: {avg_vol:.1%}")
print(f"Portfolio volatility:              {port_vol:.1%}")
print(f"Risk removed by diversification:   {1 - port_vol / avg_vol:.0%}")

# 3. Risk contribution: weight x (covariance with the portfolio) / portfolio variance.
#    The contributions add up to 100%. A stock can contribute more risk than its 25% weight.
contribution = WEIGHTS * (cov @ WEIGHTS) / port_vol**2
risk = pd.DataFrame({"weight": WEIGHTS, "volatility": vols, "risk_contribution": contribution})
print("\nRisk contribution by stock:")
print((risk * 100).round(1).astype(str).add("%").to_string())

# 4. Crisis check: correlations tend to rise exactly when diversification is needed most
crisis = returns.loc["2022", STOCKS].corr()
calm = returns.loc["2024":"2026", STOCKS].corr()
print(f"\nAverage correlation between the stocks: 2022 {avg_pairwise(crisis):.2f}, "
      f"2024-2026 {avg_pairwise(calm):.2f}")

# 5. Currency check: the same correlations with returns in forints (no currency effect)
huf_returns = (pd.read_csv(DATA / "prices_raw.csv", parse_dates=["date"], index_col="date")[STOCKS]
                 .pct_change().dropna())
print(f"Average correlation between the stocks: in HUF {avg_pairwise(huf_returns.corr()):.2f}, "
      f"in EUR {avg_pairwise(corr.loc[STOCKS, STOCKS]):.2f} (the forint/euro rate moves all four together)")

corr.round(4).to_csv(OUT / "correlation_matrix.csv")
risk.round(4).to_csv(OUT / "risk_contribution.csv", index_label="stock")

# Chart: correlation heatmap, one blue hue from light (low) to dark (high), values written in
fig, ax = plt.subplots(figsize=(6.5, 5.2))
labels = STOCKS + ["STOXX 600"]
image = ax.imshow(corr.values, cmap="Blues", vmin=0, vmax=1)
for i in range(len(labels)):
    for j in range(len(labels)):
        value = corr.values[i, j]
        ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=10,
                color="white" if value > 0.6 else INK)
ax.set_xticks(range(len(labels)), labels)
ax.set_yticks(range(len(labels)), labels)
style(ax, "Correlation of daily returns, Nov 2021 - Oct 2026 (EUR)")
ax.grid(False)
ax.spines[["left", "bottom"]].set_visible(False)
fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Correlation")
fig.savefig(OUT / "correlation_heatmap.png")
print("\nSaved output/correlation_matrix.csv, output/risk_contribution.csv, output/correlation_heatmap.png")
