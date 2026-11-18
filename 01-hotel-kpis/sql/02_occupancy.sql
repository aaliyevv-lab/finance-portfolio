-- Task 3: Occupancy by month
-- Occupancy = room-nights sold / room-nights available

-- 1. One booking split into nights (29 Nov to 3 Dec = 4 nights: 2 in Nov, 2 in Dec)
SELECT b.booking_id, b.check_in, b.check_out, c.date AS night, c.month
FROM bookings AS b
JOIN calendar AS c
  ON c.date >= b.check_in
 AND c.date <  b.check_out
WHERE b.booking_id = 100109;

-- 2. Occupancy by month
WITH rooms_sold AS (
    SELECT c.month,
           COUNT(*) AS room_nights_sold
    FROM calendar AS c
    JOIN bookings AS b
      ON c.date >= b.check_in
     AND c.date <  b.check_out
    WHERE b.status = 'stayed'
    GROUP BY c.month
),
rooms_available AS (
    SELECT month,
           COUNT(*) AS days,
           COUNT(*) * (SELECT COUNT(*) FROM rooms) AS room_nights_available
    FROM calendar
    GROUP BY month
)
SELECT a.month,
       a.days,
       a.room_nights_available,
       s.room_nights_sold,
       ROUND(100.0 * s.room_nights_sold / a.room_nights_available, 1) AS occupancy_pct
FROM rooms_available AS a
LEFT JOIN rooms_sold AS s ON a.month = s.month
ORDER BY a.month;

-- 3. Weekday vs weekend occupancy (Fri and Sat nights = weekend)
WITH nights_sold AS (
    SELECT c.date, COUNT(*) AS rooms_sold
    FROM calendar AS c
    JOIN bookings AS b
      ON c.date >= b.check_in
     AND c.date <  b.check_out
    WHERE b.status = 'stayed'
    GROUP BY c.date
)
SELECT CASE WHEN c.is_weekend = 1 THEN 'Weekend (Fri-Sat)' ELSE 'Weekday (Sun-Thu)' END AS night_type,
       COUNT(*) AS nights,
       ROUND(100.0 * SUM(n.rooms_sold) / (COUNT(*) * 130), 1) AS occupancy_pct
FROM calendar AS c
LEFT JOIN nights_sold AS n ON c.date = n.date
GROUP BY night_type;