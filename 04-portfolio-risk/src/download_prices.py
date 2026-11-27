"""
Task 1: download 5 years of daily prices and convert them to euros.

The portfolio: the four largest companies on the Budapest Stock Exchange (together most of
the BUX index), seen by a euro-based investor:
    OTP Bank        OTP.BD        bank
    MOL Group       MOL.BD        oil and gas
    Richter Gedeon  RICHTER.BD    pharmaceuticals (the company valued in the DCF project)
    Magyar Telekom  MTELEKOM.BD   telecoms
Benchmark ("the market"): STOXX Europe 600 (^STOXX), 600 large European companies, in EUR.
Exchange rate: EUR/HUF (EURHUF=X), forints per euro.

Prices are adjusted for dividends and splits (auto_adjust=True), so returns include dividends.
The data is saved to data/ so every later task, and anyone re-running them, uses the same numbers.

Run from the project folder:
    cd 04-portfolio-risk
    python3 src/download_prices.py
"""

from pathlib import Path

import pandas as pd
import yfinance as yf

DATA = Path(__file__).resolve().parent.parent / "data"
START, END = "2021-11-01", "2026-11-01"   # END is exclusive: last day is 31 Oct 2026

STOCKS = {"OTP": "OTP.BD", "MOL": "MOL.BD", "Richter": "RICHTER.BD", "Telekom": "MTELEKOM.BD"}
MARKET = {"STOXX600": "^STOXX"}
FX = {"EURHUF": "EURHUF=X"}


def download(ticker):
    """Daily adjusted closing prices for one ticker, as a Series indexed by date."""
    prices = yf.Ticker(ticker).history(start=START, end=END, auto_adjust=True)["Close"]
    prices.index = prices.index.tz_localize(None).normalize()   # drop the time zone, keep the date
    if prices.empty:
        raise SystemExit(f"No data for {ticker}: check the ticker or your internet connection")
    return prices


# Step 1. Download everything into one table, one column per series (like bind_cols in R)
raw = pd.DataFrame({name: download(t) for name, t in {**STOCKS, **MARKET, **FX}.items()})
print(f"Downloaded {len(raw.columns)} series, {raw.index.min():%d %b %Y} to {raw.index.max():%d %b %Y}")
print(raw.notna().sum().rename("trading days").to_string())

# Step 2. Keep only days when the Budapest exchange traded. The FX market trades on days when
#         Budapest is closed and vice versa, so a missing FX or STOXX value is filled with the
#         previous day's value (forward fill, like tidyr::fill() in R).
budapest_days = raw[list(STOCKS)].dropna().index
raw = raw.ffill().loc[budapest_days]

# Step 3. Convert the Hungarian stocks from HUF to EUR: price in EUR = price in HUF / (HUF per EUR)
eur = raw[list(STOCKS)].div(raw["EURHUF"], axis=0)
eur["STOXX600"] = raw["STOXX600"]

DATA.mkdir(exist_ok=True)
raw.round(4).to_csv(DATA / "prices_raw.csv", index_label="date")      # stocks in HUF, STOXX in EUR, FX
eur.round(4).to_csv(DATA / "prices_eur.csv", index_label="date")      # everything in EUR

print(f"\nSaved {len(eur)} trading days to data/prices_raw.csv and data/prices_eur.csv")
print("\nFirst and last prices in EUR:")
print(eur.iloc[[0, -1]].round(2).to_string())
growth = eur.iloc[-1] / eur.iloc[0] - 1
print("\nTotal return over 5 years, in EUR (with dividends):")
print((growth * 100).round(1).astype(str).add("%").to_string())
