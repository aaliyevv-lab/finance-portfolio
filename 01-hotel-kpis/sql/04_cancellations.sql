-- Task 5: Cancellations and booking lead time
-- Cancellation rate = cancelled bookings / all bookings
-- Lead time         = days between booking date and check-in

-- 1. Cancellation rate and lost revenue by channel
SELECT c.channel_name,
       COUNT(*)                                                      AS n_bookings,
       SUM(CASE WHEN b.status = 'cancelled' THEN 1 ELSE 0 END)       AS n_cancelled,
       ROUND(100.0 * AVG(CASE WHEN b.status = 'cancelled' THEN 1 ELSE 0 END), 1) AS cancel_rate_pct,
       ROUND(SUM(CASE WHEN b.status = 'cancelled' THEN b.rate_eur * b.nights ELSE 0 END), 0) AS lost_revenue_eur
FROM bookings AS b
JOIN channels AS c ON b.channel_id = c.channel_id
GROUP BY c.channel_name
ORDER BY cancel_rate_pct DESC;

-- 2. Cancellation rate by arrival month
SELECT strftime('%Y-%m', check_in)                                         AS arrival_month,
       COUNT(*)                                                             AS n_bookings,
       ROUND(100.0 * AVG(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END), 1) AS cancel_rate_pct
FROM bookings
WHERE check_in BETWEEN '2025-11-01' AND '2026-10-31'
GROUP BY arrival_month
ORDER BY arrival_month;

-- 3. Average lead time by channel (days booked in advance)
SELECT c.channel_name,
       ROUND(AVG(julianday(b.check_in) - julianday(b.booking_date)), 0) AS avg_lead_days,
       ROUND(AVG(CASE WHEN b.status = 'cancelled'
                      THEN julianday(b.check_in) - julianday(b.cancel_date) END), 0) AS avg_days_cancelled_before_arrival
FROM bookings AS b
JOIN channels AS c ON b.channel_id = c.channel_id
GROUP BY c.channel_name
ORDER BY avg_lead_days DESC;

-- 4. Cancellation rate by lead-time bucket
SELECT CASE
           WHEN julianday(check_in) - julianday(booking_date) <= 7  THEN '1. 0-7 days'
           WHEN julianday(check_in) - julianday(booking_date) <= 30 THEN '2. 8-30 days'
           WHEN julianday(check_in) - julianday(booking_date) <= 90 THEN '3. 31-90 days'
           ELSE '4. 90+ days'
       END                                                                    AS lead_time_bucket,
       COUNT(*)                                                               AS n_bookings,
       ROUND(100.0 * AVG(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END), 1) AS cancel_rate_pct
FROM bookings
GROUP BY lead_time_bucket
ORDER BY lead_time_bucket;