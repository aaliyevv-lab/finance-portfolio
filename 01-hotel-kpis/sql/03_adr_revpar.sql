-- Task 4: ADR and RevPAR by month
-- ADR    = room revenue / room-nights sold        (average price of a sold room)
-- RevPAR = room revenue / room-nights available   (= occupancy x ADR)

-- 1. Monthly KPI table: occupancy, ADR, RevPAR
WITH nights AS (
    -- one row per night stayed, with the price paid for that night
    SELECT c.month,
           b.rate_eur
    FROM calendar AS c
    JOIN bookings AS b
      ON c.date >= b.check_in
     AND c.date <  b.check_out
    WHERE b.status = 'stayed'
),
sold AS (
    SELECT month,
           COUNT(*)      AS room_nights_sold,
           SUM(rate_eur) AS room_revenue_eur
    FROM nights
    GROUP BY month
),
available AS (
    SELECT month,
           COUNT(*) * (SELECT COUNT(*) FROM rooms) AS room_nights_available
    FROM calendar
    GROUP BY month
)
SELECT a.month,
       ROUND(100.0 * s.room_nights_sold / a.room_nights_available, 1) AS occupancy_pct,
       ROUND(s.room_revenue_eur / s.room_nights_sold, 0)              AS adr_eur,
       ROUND(s.room_revenue_eur / a.room_nights_available, 0)         AS revpar_eur,
       ROUND(s.room_revenue_eur, 0)                                   AS room_revenue_eur
FROM available AS a
JOIN sold AS s ON a.month = s.month
ORDER BY a.month;

-- 2. Full-year KPIs by room type
WITH nights AS (
    SELECT r.room_type,
           b.rate_eur
    FROM calendar AS c
    JOIN bookings AS b
      ON c.date >= b.check_in
     AND c.date <  b.check_out
    JOIN rooms AS r ON b.room_id = r.room_id
    WHERE b.status = 'stayed'
),
inventory AS (
    SELECT room_type,
           COUNT(*) AS n_rooms,
           COUNT(*) * (SELECT COUNT(*) FROM calendar) AS room_nights_available
    FROM rooms
    GROUP BY room_type
)
SELECT i.room_type,
       i.n_rooms,
       ROUND(100.0 * COUNT(*) / i.room_nights_available, 1) AS occupancy_pct,
       ROUND(SUM(n.rate_eur) / COUNT(*), 0)                 AS adr_eur,
       ROUND(SUM(n.rate_eur) / i.room_nights_available, 0)  AS revpar_eur
FROM nights AS n
JOIN inventory AS i ON n.room_type = i.room_type
GROUP BY i.room_type, i.n_rooms, i.room_nights_available
ORDER BY revpar_eur DESC;

-- 3. Full-year totals (the numbers for the README)
WITH nights AS (
    SELECT b.rate_eur
    FROM calendar AS c
    JOIN bookings AS b
      ON c.date >= b.check_in
     AND c.date <  b.check_out
    WHERE b.status = 'stayed'
),
available AS (
    SELECT (SELECT COUNT(*) FROM calendar) * (SELECT COUNT(*) FROM rooms) AS room_nights_available
)
SELECT COUNT(*)                                                    AS room_nights_sold,
       a.room_nights_available,
       ROUND(100.0 * COUNT(*) / a.room_nights_available, 1)        AS occupancy_pct,
       ROUND(SUM(n.rate_eur) / COUNT(*), 0)                        AS adr_eur,
       ROUND(SUM(n.rate_eur) / a.room_nights_available, 0)         AS revpar_eur,
       ROUND(SUM(n.rate_eur), 0)                                   AS room_revenue_eur
FROM nights AS n, available AS a;