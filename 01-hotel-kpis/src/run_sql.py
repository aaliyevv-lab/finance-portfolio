"""
Run every query in a .sql file against data/hotel.db and print the results as tables.

Usage (from the 01-hotel-kpis folder):
    python3 src/run_sql.py sql/01_explore.sql

Queries are separated by semicolons. A comment line (-- ...) right above a query
is printed as its title.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hotel.db"

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_rows", 50)


def split_queries(sql_text):
    """Split a .sql file into (title, query) pairs."""
    pairs = []
    for chunk in sql_text.split(";"):
        lines = [line for line in chunk.strip().splitlines() if line.strip()]
        # title = the last comment line ABOVE the query (comments inside the query are ignored)
        title = "Query"
        for line in lines:
            if not line.strip().startswith("--"):
                break
            title = line.strip().lstrip("-").strip()
        code = "\n".join(l for l in lines if not l.strip().startswith("--"))
        if code.strip():
            pairs.append((title, code))
    return pairs


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 src/run_sql.py sql/<file>.sql")
        sys.exit(1)

    sql_file = Path(sys.argv[1])
    queries = split_queries(sql_file.read_text())

    with sqlite3.connect(DB_PATH) as con:
        for title, query in queries:
            print(f"\n=== {title} ===")
            try:
                result = pd.read_sql(query, con)
                print(result.to_string(index=False) if len(result) else "(no rows)")
            except Exception as e:
                print(f"ERROR: {e}\n--- query ---\n{query}")


if __name__ == "__main__":
    main()
