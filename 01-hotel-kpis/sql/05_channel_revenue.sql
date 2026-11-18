-- Task 6: Revenue by channel and month, gross vs net of commission
-- Gross revenue = what the guest pays
-- Commission    = gross x channel commission % (paid to Booking.com, Expedia, agents)
-- Net revenue   = gross - commission (what the hotel keeps)

-- 1. Full-year channel performance
WITH nights AS (
    SELECT b.channel_id,
           b.rate_eur
    FROM calendar AS c
    JOIN bookings AS b
      ON c.date >= b.check_in
     AND c.date <  b.check_out
    WHERE b.status = 'stayed'
)
SELECT ch.channel_name,
       ch.commission_pct,
       COUNT(*)                                                    AS room_nights,
       ROUND(SUM(n.rate_eur), 0)                                   AS gross_revenue_eur,
       ROUND(SUM(n.rate_eur) * ch.commission_pct, 0)               AS commission_eur,
       ROUND(SUM(n.rate_eur) * (1 - ch.commission_pct), 0)         AS net_revenue_eur,
       ROUND(100.0 * SUM(n.rate_eur) / (SELECT SUM(rate_eur) FROM nights), 1) AS share_of_gross_pct,
       ROUND(SUM(n.rate_eur) / COUNT(*), 0)                        AS gross_adr_eur,
       ROUND(SUM(n.rate_eur) * (1 - ch.commission_pct) / COUNT(*), 0) AS net_adr_eur
FROM nights AS n
JOIN channels AS ch ON n.channel_id = ch.channel_id
GROUP BY ch.channel_name, ch.commission_pct
ORDER BY net_revenue_eur DESC;

-- 2. Gross revenue by month and channel, one column per channel (EUR thousands)
WITH nights AS (
    SELECT c.month,
           b.channel_id,
           b.rate_eur
    FROM calendar AS c
    JOIN bookings AS b
      ON c.date >= b.check_in
     AND c.date <  b.check_out
    WHERE b.status = 'stayed'
)
SELECT month,
       ROUND(SUM(CASE WHEN channel_id = 1 THEN rate_eur ELSE 0 END) / 1000, 0) AS direct_k,
       ROUND(SUM(CASE WHEN channel_id = 2 THEN rate_eur ELSE 0 END) / 1000, 0) AS booking_com_k,
       ROUND(SUM(CASE WHEN channel_id = 3 THEN rate_eur ELSE 0 END) / 1000, 0) AS expedia_k,
       ROUND(SUM(CASE WHEN channel_id = 4 THEN rate_eur ELSE 0 END) / 1000, 0) AS corporate_k,
       ROUND(SUM(CASE WHEN channel_id = 5 THEN rate_eur ELSE 0 END) / 1000, 0) AS agent_gds_k,
       ROUND(SUM(rate_eur) / 1000, 0)                                          AS total_k
FROM nights
GROUP BY month
ORDER BY month;

-- 3. Commission cost by month
WITH nights AS (
    SELECT c.month,
           b.rate_eur,
           ch.commission_pct
    FROM calendar AS c
    JOIN bookings AS b
      ON c.date >= b.check_in
     AND c.date <  b.check_out
    JOIN channels AS ch ON b.channel_id = ch.channel_id
    WHERE b.status = 'stayed'
)
SELECT month,
       ROUND(SUM(rate_eur), 0)                                           AS gross_revenue_eur,
       ROUND(SUM(rate_eur * commission_pct), 0)                          AS commission_eur,
       ROUND(SUM(rate_eur * (1 - commission_pct)), 0)                    AS net_revenue_eur,
       ROUND(100.0 * SUM(rate_eur * commission_pct) / SUM(rate_eur), 1)  AS commission_pct_of_gross
FROM nights
GROUP BY month
ORDER BY month;