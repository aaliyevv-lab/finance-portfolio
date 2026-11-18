"""
Generate a realistic fake SQLite database for a 130-room luxury hotel in Budapest.

Covers stays from November 2025 to October 2026 (12 months).
Output: data/hotel.db with 5 tables: rooms, rates, channels, calendar, bookings.

Run from the project folder:
    cd 01-hotel-kpis
    python src/generate_data.py
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)  # fixed seed -> same data every run (like set.seed(42) in R)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hotel.db"

PERIOD_START = pd.Timestamp("2025-11-01")
PERIOD_END = pd.Timestamp("2026-10-31")  # last night in scope
SIM_START = PERIOD_START - pd.Timedelta(days=7)  # start a week early so stays roll into Nov 1

# ---------------------------------------------------------------------------
# 1. ROOMS: 130 rooms across 4 types
# ---------------------------------------------------------------------------
ROOM_TYPES = {
    #  type            count  base rate (EUR/night)
    "Deluxe":         (60, 380),
    "Premier":        (40, 480),
    "Junior Suite":   (20, 650),
    "Suite":          (10, 1100),
}

rooms = []
room_id = 1
for room_type, (count, base_rate) in ROOM_TYPES.items():
    for _ in range(count):
        floor = (room_id - 1) // 22 + 1  # ~22 rooms per floor -> floors 1-6
        rooms.append({
            "room_id": room_id,
            "room_number": f"{floor}{(room_id - 1) % 22 + 1:02d}",  # e.g. 101, 215
            "room_type": room_type,
            "floor": floor,
            "base_rate_eur": base_rate,
        })
        room_id += 1
rooms = pd.DataFrame(rooms)

# ---------------------------------------------------------------------------
# 2. RATES: seasonal rate per room type and month
# ---------------------------------------------------------------------------
# month -> (price multiplier, target occupancy)
SEASON = {
    "2025-11": (0.95, 0.72), "2025-12": (1.20, 0.82), "2026-01": (0.75, 0.55),
    "2026-02": (0.80, 0.60), "2026-03": (0.95, 0.70), "2026-04": (1.05, 0.78),
    "2026-05": (1.15, 0.85), "2026-06": (1.20, 0.88), "2026-07": (1.15, 0.86),
    "2026-08": (1.20, 0.87), "2026-09": (1.15, 0.88), "2026-10": (1.05, 0.82),
}
SEASON["2025-10"] = SEASON["2025-11"]  # only used for the warm-up week

rates = pd.DataFrame([
    {"room_type": rt, "month": m, "rate_eur": round(base * mult, -1)}
    for rt, (_, base) in ROOM_TYPES.items()
    for m, (mult, _) in SEASON.items() if m != "2025-10"
])

# Special high-demand dates: (start, end inclusive, price multiplier, occupancy)
EVENTS = [
    ("2025-12-24", "2026-01-01", 1.35, 0.95),  # Christmas markets & New Year's Eve
    ("2026-07-23", "2026-07-26", 1.60, 0.98),  # Formula 1 Hungarian GP weekend (assumed dates)
    ("2026-08-19", "2026-08-21", 1.30, 0.95),  # St. Stephen's Day (Aug 20) fireworks
]

# ---------------------------------------------------------------------------
# 3. CHANNELS: where bookings come from
# ---------------------------------------------------------------------------
channels = pd.DataFrame([
    # id, name,              commission, mix share, cancel prob, rate factor, mean lead time (days)
    (1, "Direct (website/phone)", 0.00, 0.28, 0.15, 1.00, 35),
    (2, "Booking.com",            0.18, 0.30, 0.30, 1.00, 25),
    (3, "Expedia",                0.20, 0.12, 0.25, 1.00, 28),
    (4, "Corporate",              0.00, 0.15, 0.12, 0.88, 10),
    (5, "Travel agent / GDS",     0.10, 0.15, 0.10, 0.92, 60),
], columns=["channel_id", "channel_name", "commission_pct", "share", "cancel_prob",
            "rate_factor", "lead_mean"])

# ---------------------------------------------------------------------------
# 4. CALENDAR: one row per night in the 12-month period
# ---------------------------------------------------------------------------
dates = pd.date_range(PERIOD_START, PERIOD_END, freq="D")
calendar = pd.DataFrame({
    "date": dates.strftime("%Y-%m-%d"),
    "year": dates.year,
    "month": dates.strftime("%Y-%m"),
    "day_of_week": dates.day_name(),
    "is_weekend": (dates.dayofweek >= 4).astype(int),  # Fri & Sat nights
})


# ---------------------------------------------------------------------------
# 5. BOOKINGS: simulate stays room by room so no room is ever double-booked
# ---------------------------------------------------------------------------
def night_profile(date):
    """Return (price multiplier, target occupancy) for a given night."""
    mult, occ = SEASON[date.strftime("%Y-%m")]
    if date.dayofweek >= 4:  # Fri/Sat nights are busier and pricier in a city hotel
        occ = min(occ + 0.07, 0.97)
        mult *= 1.08
    for start, end, ev_mult, ev_occ in EVENTS:
        if pd.Timestamp(start) <= date <= pd.Timestamp(end):
            mult *= ev_mult
            occ = ev_occ
    return mult, occ


MEAN_STAY = 2.6  # average length of stay in nights

stays = []
all_nights = pd.date_range(SIM_START, PERIOD_END, freq="D")
profiles = {d: night_profile(d) for d in all_nights}

for room in rooms.itertuples():
    d = SIM_START
    while d <= PERIOD_END:
        _, occ = profiles[d]
        # probability that a stay starts tonight, given the target occupancy:
        # occ = p*L / (p*L + (1 - p))  =>  p = occ / (L*(1-occ) + occ)
        p_start = occ / (MEAN_STAY * (1 - occ) + occ)
        if rng.random() < p_start:
            nights = int(np.clip(rng.poisson(MEAN_STAY - 1) + 1, 1, 10))
            stays.append({"room_id": room.room_id, "room_type": room.room_type,
                          "check_in": d, "nights": nights})
            d += pd.Timedelta(days=nights)
        else:
            d += pd.Timedelta(days=1)

stays = pd.DataFrame(stays)
stays["status"] = np.where(rng.random(len(stays)) < 0.02, "no_show", "stayed")

# Cancelled bookings never occupied a room. Per channel, add enough of them so that
# cancelled / all bookings ~= that channel's cancel probability.
stays["channel_id"] = rng.choice(channels.channel_id, size=len(stays), p=channels.share)
cancelled = []
for ch in channels.itertuples():
    n_kept = (stays.channel_id == ch.channel_id).sum()
    n_cancel = int(round(n_kept * ch.cancel_prob / (1 - ch.cancel_prob)))
    sample = stays.sample(n_cancel, replace=True, random_state=int(rng.integers(1e9))).copy()
    sample["channel_id"] = ch.channel_id
    sample["status"] = "cancelled"
    cancelled.append(sample)
bookings = pd.concat([stays, *cancelled], ignore_index=True)

# Rate paid per night = monthly rate x date premium x channel discount x noise
ch = channels.set_index("channel_id")
base = rooms.set_index("room_type")["base_rate_eur"].groupby(level=0).first()
price_mult = bookings.check_in.map(lambda x: profiles[x][0])
noise = rng.normal(1.0, 0.04, len(bookings))
bookings["rate_eur"] = (
    bookings.room_type.map(base) * price_mult
    * bookings.channel_id.map(ch.rate_factor) * noise
).round(2)

# Booking date = check-in minus lead time (exponential, mean depends on channel)
lead = rng.exponential(bookings.channel_id.map(ch.lead_mean)).astype(int)
bookings["booking_date"] = bookings.check_in - pd.to_timedelta(lead, unit="D")
bookings["check_out"] = bookings.check_in + pd.to_timedelta(bookings.nights, unit="D")

# Cancellation date: somewhere between booking date and check-in
is_cxl = bookings.status == "cancelled"
days_before = (bookings.check_in - bookings.booking_date).dt.days
cxl_offset = (rng.random(len(bookings)) * days_before).astype(int)
bookings["cancel_date"] = (bookings.booking_date + pd.to_timedelta(cxl_offset, unit="D")).where(is_cxl)

bookings["adults"] = rng.choice([1, 2, 2, 2, 3], size=len(bookings))
bookings["room_revenue_eur"] = np.where(bookings.status == "stayed",
                                        (bookings.rate_eur * bookings.nights).round(2), 0.0)

# Sort chronologically by booking date and assign IDs
bookings = bookings.sort_values(["booking_date", "check_in"]).reset_index(drop=True)
bookings.insert(0, "booking_id", np.arange(100001, 100001 + len(bookings)))
for col in ["booking_date", "check_in", "check_out", "cancel_date"]:
    bookings[col] = bookings[col].dt.strftime("%Y-%m-%d")  # NaT -> NaN -> NULL in SQL

bookings = bookings[["booking_id", "booking_date", "check_in", "check_out", "nights",
                     "room_id", "channel_id", "adults", "rate_eur", "status",
                     "cancel_date", "room_revenue_eur"]]

# ---------------------------------------------------------------------------
# 6. WRITE TO SQLITE (explicit schema = proper types, keys and constraints)
# ---------------------------------------------------------------------------
SCHEMA = """
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS calendar;
DROP TABLE IF EXISTS rates;
DROP TABLE IF EXISTS channels;
DROP TABLE IF EXISTS rooms;

CREATE TABLE rooms (
    room_id        INTEGER PRIMARY KEY,
    room_number    TEXT NOT NULL,
    room_type      TEXT NOT NULL,
    floor          INTEGER NOT NULL,
    base_rate_eur  REAL NOT NULL
);

CREATE TABLE rates (
    room_type  TEXT NOT NULL,
    month      TEXT NOT NULL,          -- 'YYYY-MM'
    rate_eur   REAL NOT NULL,          -- published rack rate for that month
    PRIMARY KEY (room_type, month)
);

CREATE TABLE channels (
    channel_id      INTEGER PRIMARY KEY,
    channel_name    TEXT NOT NULL,
    commission_pct  REAL NOT NULL      -- 0.18 = 18% of room revenue
);

CREATE TABLE calendar (
    date         TEXT PRIMARY KEY,     -- 'YYYY-MM-DD', one row per night
    year         INTEGER NOT NULL,
    month        TEXT NOT NULL,        -- 'YYYY-MM'
    day_of_week  TEXT NOT NULL,
    is_weekend   INTEGER NOT NULL      -- 1 = Friday or Saturday night
);

CREATE TABLE bookings (
    booking_id        INTEGER PRIMARY KEY,
    booking_date      TEXT NOT NULL,   -- when the reservation was made
    check_in          TEXT NOT NULL,
    check_out         TEXT NOT NULL,   -- guest leaves this morning (not a night stayed)
    nights            INTEGER NOT NULL,
    room_id           INTEGER NOT NULL REFERENCES rooms(room_id),
    channel_id        INTEGER NOT NULL REFERENCES channels(channel_id),
    adults            INTEGER NOT NULL,
    rate_eur          REAL NOT NULL,   -- agreed price per night
    status            TEXT NOT NULL CHECK (status IN ('stayed', 'cancelled', 'no_show')),
    cancel_date       TEXT,            -- NULL unless cancelled
    room_revenue_eur  REAL NOT NULL    -- rate x nights for stays, 0 otherwise
);
"""

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(DB_PATH) as con:
    con.executescript(SCHEMA)
    rooms.to_sql("rooms", con, if_exists="append", index=False)
    rates.to_sql("rates", con, if_exists="append", index=False)
    channels[["channel_id", "channel_name", "commission_pct"]].to_sql(
        "channels", con, if_exists="append", index=False)
    calendar.to_sql("calendar", con, if_exists="append", index=False)
    bookings.to_sql("bookings", con, if_exists="append", index=False)

    print(f"Database written to {DB_PATH}\n")
    for table in ["rooms", "rates", "channels", "calendar", "bookings"]:
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<10} {n:>7,} rows")
